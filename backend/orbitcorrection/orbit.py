from pathlib import Path
from epics import PV
from numpy.linalg import svd
import json
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)

class Corrector(object):
    def __init__(self, label, write_label, read_label=None, kind=None):
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
    def __init__(self, x_pv, y_pv):
        self.x_ref = 0
        self.y_ref = 0
        #self.x_pv = PV(x_pv)
        #self.y_pv = PV(y_pv)
        self.x_pv = x_pv
        self.y_pv = y_pv

    @property
    def x(self):
        return PV(self.x_pv).get()

    @property
    def y(self):
        return PV(self.y_pv).get()

class OrbitSVD:
    def __init__(self, epsilon_x=0.001, epsilon_y=0.001):
        self.epsilon_x = epsilon_x
        self.epsilon_y = epsilon_y

    def apply(self, resp_matrix, orbit, weights=None):
        print('correction')
        if weights is None:
            weights = np.eye(len(orbit))
        resp_matrix = np.dot(weights, resp_matrix)
        misalign = np.dot(weights, orbit)

        U, s, V = svd(resp_matrix)
        s_inv = np.zeros(len(s))
        s_max = max(s)
        for i in range(len(s)):
            if i < int(len(s)/2.):
                epsilon = self.epsilon_x
            else:
                epsilon = self.epsilon_y
            if s[i] <= s_max * epsilon:
                s_inv[i] = 0.
            else:
                s_inv[i] = 1. / s[i]
        Sinv = np.zeros((np.shape(U)[0], np.shape(V)[0]))
        Sinv[:len(s), :len(s)] = np.diag(s_inv)
        Sinv = np.transpose(Sinv)
        A = np.dot(np.transpose(V), np.dot(Sinv, np.transpose(U)))
        angle = np.dot(A, misalign)
        logger.debug("max(abs(angle)) = " + str(np.max(np.abs(angle))) + " min(abs(angle)) = " + str(np.min(np.abs(angle))))
        return angle

class Orbit(object):
    def __init__(self, ids, rm_method=None):
        self.cors = []
        self.bpms = []
        self.rm_method = rm_method
        self.response_matrix = None
        self.orbit_solver = OrbitSVD()
        basedir = Path(__file__).resolve().parent
        fname = basedir.joinpath('resources', 'config.json')
        with open(fname) as f:
            self.data = json.load(f)

        self.create_correctors(ids)
        self.create_bpms(ids)

        if self.rm_method:
            self.setup_response_matrix()

    @staticmethod
    def extract_elems(data, elem_type, ids):
        elements = {}
        for section in data:
            el_list = []
            for child in section['children']:
                if child['label'] == elem_type:
                    [el_list.append(elem) for elem in child['children'] if elem['id'] in ids]
            if el_list:
                elements[section['label']] = el_list
        return elements

    def create_correctors(self, ids):
        cors = self.extract_elems(self.data, '校正铁', ids)
        self.cors = []
        for s in cors:
            for cor in cors[s]:
                if s == 'MEBT':
                    kind = 'rm'
                else:
                    kind = 'sc'
                self.cors.append(Corrector(f"{s}-{cor['label']}", cor['set_pv'], cor['get_pv'], kind))

    def create_bpms(self, ids):
        bpms = self.extract_elems(self.data, 'bpm', ids)
        self.bpms = [Bpm(bpm['x_pv'], bpm['y_pv']) for s in bpms for bpm in bpms[s]]

    def setup_response_matrix(self):
        self.response_matrix = ResponseMatrix(method=self.rm_method)

    def get_orbit(self):
        m = len(self.bpms)
        orbit = np.zeros(2 * m)
        for i, bpm in enumerate(self.bpms):
            #print("get_orbit = ",bpm.id, bpm.x,  bpm.x_ref)
            orbit[i] = bpm.x - bpm.x_ref
            orbit[i+m] = bpm.y - bpm.y_ref
        return orbit

    def correct(self, alpha):
        orbit = (1 - alpha) * self.get_orbit()
        resp_matrix = self.response_matrix.matrix
        angles = self.orbit_solver.apply(resp_matrix=resp_matrix, orbit=orbit)
        correct_strengths = {}
        for cor, angle in zip(self.cors, angles):
            correct_strengths[cor.label] = {
                'strength': round(angle, 2),
                'pv': cor.write_label
            }
        return correct_strengths

class MeasureResponseMatrix(object):
    def __init__(self, cors, bpms, rm_step, sc_step, rm_lim, sc_lim):
        self.cors = cors
        self.bpms = bpms
        self.rm_step = rm_step
        self.sc_step = sc_step
        self.rm_lim = rm_lim
        self.sc_lim = sc_lim

    def one_cor_rm(self, cor, step, lim, correct_section):
        if correct_section.lower() == 'sc':
            loop_num = 4
        else:
            loop_num = 2

        #bpms = [bpm for s in self.bpms for bpm in self.bpms[s]]
        m = len(self.bpms)
        data = np.zeros((loop_num, m*2+1))

        start_current = cor.current
        stop_current = start_current + step
        if abs(stop_current) > lim:
            stop_current = start_current - step
        for i, current in enumerate(np.linspace(start_current, stop_current, loop_num)):
            cor.current = current
            rb_val = cor.current

            while abs(rb_val - current) > 0.2:
                time.sleep(0.5)
                rb_val = cor.current
                #print(read_pv)
            data[i, 0] = current
            for bpm_idx, bpm in enumerate(self.bpms):
                data[i, bpm_idx+1] = bpm.x
                data[i, bpm_idx+m+1] = bpm.y
        cor.current = start_current
        rb_val = cor.current
        while abs(rb_val - start_current) > 0.2:
            time.sleep(0.5)
            rb_val = cor.current
        linear_fit = np.polyfit(data[:, 0], data[:, 1:], 1)
        return linear_fit[0, :].reshape(-1, 1)

    def calculate(self):
        #bpms = [bpm for s in self.bpms for bpm in self.bpms[s]]
        response_matrix = np.empty((len(self.bpms)*2, 0))
        for cor in self.cors:
            if cor.kind == 'rm':
                rm_column = self.one_cor_rm(cor, self.rm_step, self.rm_lim, 'rm')
            else:
                rm_column = self.one_cor_rm(cor, self.sc_step, self.sc_lim, 'sc')
            response_matrix = np.hstack((response_matrix, rm_column))
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








