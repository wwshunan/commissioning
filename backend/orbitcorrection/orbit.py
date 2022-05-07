from pathlib import Path
from epics import PV
from ..services.pv_handler import PhaseScanPVController
from numpy.linalg import svd
import pandas as pd
import json
import numpy as np
import time
import logging
import datetime

logger = logging.getLogger(__name__)

basedir = Path(__file__).resolve().parent
fname = basedir.joinpath('resources', 'config.json')
with open(fname) as f:
    data = json.load(f)

related_filename = basedir.joinpath('resources', 'causality.xlsx')
cor_bpm_relation = pd.read_excel(related_filename, index_col=0)
pv_controller = PhaseScanPVController()

def extract_elems(elem_type, ids):
    elements = {}
    for section in data:
        el_list = []
        for child in section['children']:
            if child['label'] == elem_type:
                [el_list.append(elem) for elem in child['children'] if elem['id'] in ids]
        if el_list:
            elements[section['label']] = el_list
    return elements

class Corrector(object):
    def __init__(self, id, label, write_label, read_label=None, kind=None):
        self.id = id
        self.label = label
        self.write_label = write_label
        self.write_pv = PV(write_label)
        self.read_label = read_label
        self.kind = kind
        if read_label:
            self.read_pv = PV(read_label)

    @property
    def current(self):
        if self.read_label:
            return self.read_pv.get()

    @current.setter
    def current(self, value):
        self.write_pv.put(value)

class Bpm(object):
    def __init__(self, id, x_pv, y_pv):
        self.id = id
        self.x_ref = 0
        self.y_ref = 0
        self.x_pv = PV(x_pv)
        self.y_pv = PV(y_pv)

    @property
    def x(self):
        return self.x_pv.get()

    @property
    def y(self):
        return self.y_pv.get()

class OrbitSVD(object):
    def apply(self, cors, rm_lim, sc_lim, resp_matrix, orbit, weights=None):
        if weights is None:
            weights = np.eye(len(orbit))
        resp_matrix = np.dot(weights, resp_matrix)
        misalign = np.dot(weights, orbit)

        U, s, V = svd(resp_matrix)
        s_inv = np.zeros(len(s))
        for i in range(len(s)):
            if s[i] > 1e-5:
                s_inv[i] = 1. / s[i]
            else:
                s_inv[i] = 0

        #for i in range(len(s)):
        #    if i < int(len(s)/2.):
        #        epsilon = self.epsilon_x
        #    else:
        #        epsilon = self.epsilon_y
        #    if s[i] <= s_max * epsilon:
        #        s_inv[i] = 0.
        #    else:
        #        s_inv[i] = 1. / s[i]
        c = 0
        while True:
            Sinv = np.zeros((np.shape(U)[0], np.shape(V)[0]))
            Sinv[:len(s), :len(s)] = np.diag(s_inv)
            Sinv = np.transpose(Sinv)
            print(s_inv)
            A = np.dot(np.transpose(V), np.dot(Sinv, np.transpose(U)))
            angles = np.dot(A, misalign)
           
            for cor, current in zip(cors, angles):
                lim = sc_lim     
                if not cor.id.startswith('CM'):
                    lim = rm_lim
                print(current, cor.current, lim, cor.id)
                if abs(current + cor.current) > lim:
                    max_index = np.argmax(s_inv)
                    #index = np.where(s_inv > 1e-5, s_inv, np.inf).argmax()
                    s_inv[max_index] = 0
                    break
            else:
                break

        logger.debug("max(abs(angle)) = " + str(np.max(np.abs(angles))) +
                     " min(abs(angle)) = " + str(np.min(np.abs(angles))))
        return angles

class CorrectorGather(object):
    def __init__(self, ids):
        self.cors = []
        self.create_correctors(ids)

    def create_correctors(self, ids):
        cors = extract_elems('校正铁', ids)
        self.cors = []
        for s in cors:
            for cor in cors[s]:
                if s == 'MEBT':
                    kind = 'rm'
                else:
                    kind = 'sc'
                self.cors.append(Corrector(cor['id'], f"{s}-{cor['label']}",
                                           cor['set_pv'], cor['get_pv'], kind))

class OrbitGather(object):
    def __init__(self, ids):
        self.bpms = []
        self.create_bpms(ids)
        self.refer_orbit = self.get_avg_orbit()

    def create_bpms(self, ids):
        bpms = extract_elems('bpm', ids)
        self.bpms = [Bpm(bpm['id'], bpm['x_pv'], bpm['y_pv'])
                     for s in bpms for bpm in bpms[s]]

    def get_avg_orbit(self):
        avg_num = 6
        orbit = self.get_orbit()
        for _ in range(avg_num-1):
            orbit += self.get_orbit()
        orbit /= avg_num
        return orbit

    def get_orbit(self):
        m = len(self.bpms)
        orbit = np.zeros(2 * m)
        for i, bpm in enumerate(self.bpms):
            orbit[i] += bpm.x - bpm.x_ref
            orbit[i+m] += bpm.y - bpm.y_ref
        time.sleep(1)
        return orbit

    def get_orbit_diff(self, cor_id):
        diff_orbit = self.get_avg_orbit() - self.refer_orbit
        relation_col = cor_bpm_relation[cor_id]
        m = len(self.bpms)
        for i, bpm in enumerate(self.bpms):
            if relation_col[bpm.id] == 0:
                diff_orbit[i] = 0
                diff_orbit[i+m] += 0
        return diff_orbit


class Orbit(object):
    def __init__(self, gather_orbit, gather_correction,
                 rm_lim, sc_lim, rm_method=None):
        self.cors = gather_correction.cors
        self.bpms = gather_orbit.bpms
        self.gather_orbit = gather_orbit
        self.rm_method = rm_method
        self.response_matrix = None
        self.orbit_solver = OrbitSVD()
        self.rm_lim = rm_lim
        self.sc_lim = sc_lim

        if self.rm_method:
            self.setup_response_matrix()

    def setup_response_matrix(self):
        self.response_matrix = ResponseMatrix(method=self.rm_method)

    def correct(self, alpha):
        orbit = -(1 - alpha) * self.gather_orbit.refer_orbit
        resp_matrix = self.response_matrix.matrix
        angles = self.orbit_solver.apply(self.cors, self.rm_lim, self.sc_lim, 
                                         resp_matrix=resp_matrix, orbit=orbit)

        correct_strengths = {}
        for cor, angle in zip(self.cors, angles):
            correct_strengths[cor.label] = {
                'strength': round(angle+cor.current, 2),
                'pv': cor.write_label
            }
        return correct_strengths

class MeasureResponseMatrix(object):
    def __init__(self, gather_cors, gather_orbit, rm_step, sc_step, rm_lim, sc_lim):
        self.cors = gather_cors.cors
        self.bpms = gather_orbit.bpms
        self.rm_step = rm_step
        self.sc_step = sc_step
        self.rm_lim = rm_lim
        self.sc_lim = sc_lim
        self.gather_orbit = gather_orbit
        self.prev_cor = None
        self.prev_cor_current = None

    def one_cor_rm(self, cor, step, lim):
        #bpms = [bpm for s in self.bpms for bpm in self.bpms[s]]
        m = len(self.bpms)
        data = np.zeros(m*2+1)

        start_current = cor.current
        stop_current = start_current + step

        if abs(stop_current) > lim:
            stop_current = start_current - step
        cor.current = stop_current

        #监控先前校正铁电流是否归位
        if self.prev_cor:
            rb_val = self.prev_cor.current
            while abs(rb_val - self.prev_cor_current) > 0.2:
                time.sleep(0.5)
                rb_val = cor.current

        rb_val = cor.current

        while abs(rb_val - stop_current) > 0.2:
            time.sleep(0.5)
            rb_val = cor.current
        data[0] = stop_current
        data[1:] = self.gather_orbit.get_orbit_diff(cor.id)
        cor.current = start_current
        self.prev_cor = cor
        self.prev_cor_current = start_current
        bpm_resp = data[1:] / (stop_current - start_current)
        return bpm_resp.reshape(-1, 1)

    def calculate(self):
        response_matrix = np.empty((len(self.bpms)*2, 0))
        i = 0
        while i < len(self.cors):
            cor = self.cors[i]
            if cor.kind == 'rm':
                rm_column = self.one_cor_rm(cor, self.rm_step, self.rm_lim)
            else:
                rm_column = self.one_cor_rm(cor, self.sc_step, self.sc_lim)
            if not pv_controller.get_cavity_ready() or not pv_controller.get_current_ready():
                continue
            i += 1
            response_matrix = np.hstack((response_matrix, rm_column))
        resp_filename = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M.txt')
        np.savetxt(basedir.joinpath('data', resp_filename), response_matrix)
        return response_matrix

class ResponseMatrix(object):
    def __init__(self, method=None):
        self.cors = []
        self.bpms = []
        self.method = method
        self.matrix = None

    def calculate(self):
        if self.method:
            self.cors = self.method.cors
            self.bpms = self.method.bpms
            self.matrix = self.method.calculate()








