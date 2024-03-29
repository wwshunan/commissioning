#!/usr/bin/env python
from scipy.constants import c
from scipy import interpolate
from scipy.optimize import leastsq, curve_fit
from .phase_energy_relation import TofPhaseTransformer
from pathlib import Path
from .cfit import (get_bpm_phases, single_bpm_sim_params, 
                   simulate_energy, double_bpm_sim_params)
from scipy.optimize import minimize_scalar
import numpy as np


basedir = Path(__file__).resolve().parent

class DataFitBase(object):
    def __init__(self, **kwargs):
        self.cav_phases_degree = kwargs['cavity_phases']
        self.bpm_phases = kwargs['bpm_phases']
        self.Win = kwargs['Win']
        self.distance = kwargs['distance']
        self.sync_phase = kwargs['sync_phase']
        self.field_name = kwargs['field_name']
        self.start_phase = kwargs['start_phase']
        self.epk_ref = kwargs['Epk_ref']
        self.rf_direction = kwargs['rf_direction']
        self.freq = kwargs['freq']
        self.bpm_harm = kwargs['bpm_harm']
        self.bpm_polarity = kwargs['bpm_polarity']
        self.m = kwargs['m']
        self.q = kwargs['q']
        self.cavity_name = kwargs['cavity_name']

        data = np.loadtxt(basedir.joinpath('resources', 'fields', self.field_name))
        z = np.linspace(data[0, 0], data[-1, 0], 1501)
        f = interpolate.interp1d(data[:, 0], data[:, 3], kind='slinear')
        self.Ez = f(z)
        self.dz = (data[-1, 0] - data[0, 0]) / 1500

        if self.rf_direction == 0:
            self.cav_phases_rad = -np.asarray(self.cav_phases_degree) * np.pi / 180
        else:
            self.cav_phases_rad = np.asarray(self.cav_phases_degree) * np.pi / 180


class SingleBPMFit(DataFitBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def bpm_fit(self):
        p0 = [1, 0, 0]
        plsq = leastsq(self.residuals, p0)
        error = np.std(self.residuals(plsq[0]))

        sync_phase = self.sync_phase * np.pi / 180
        field_factor = plsq[0][0]
        phase_in = plsq[0][1]

        phase_opt = self.get_entr_phase(sync_phase, field_factor)
        computed_bpm_phases = [self.get_bpm_phases(field_factor, phase_in + delta)
                               for delta in self.cav_phases_rad]

        delta_start = self.cav_phases_rad[0]
        print(phase_in + delta_start)
        if self.rf_direction == 0:
            rf_phase = (phase_in + delta_start - phase_opt) * 180 / np.pi + self.start_phase
        else:
            rf_phase = -(phase_in + delta_start - phase_opt) * 180 / np.pi + self.start_phase

        exit_energy = self.get_process_params(field_factor, phase_opt)[2]
        rf_phase = phase_wrapping(rf_phase)
        entr_phase = (phase_in +delta_start) * 180 / np.pi
        return (entr_phase, rf_phase, exit_energy, field_factor * self.epk_ref, error,
                self.cav_phases_degree, computed_bpm_phases + plsq[0][2])

    def get_bpm_phases(self, field_factor, phase_in):
        return get_bpm_phases(field_factor, phase_in, self.Win, self.freq, self.dz,
                              self.distance, self.q, self.m, self.Ez, self.bpm_harm, self.bpm_polarity)
        '''
        W = self.Win
        t = 0
        #a = 0
        #b = 0
        for i in range(len(self.Ez) - 1):
            phi = phase_in + 2 * np.pi * self.freq * t
            gamma = W / self.m + 1
            beta = (1 - gamma ** -2) ** 0.5
            W = W + self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.cos(phi) * self.dz
            gamma_exit = W / self.m + 1
            beta_exit = (1 - gamma_exit ** -2) ** 0.5
            #a += c * Ez[i] * sin(phi) * dz
            #b += c * self.Ez[i] * np.cos(phi) * self.dz
            t += self.dz / (0.5 * (beta + beta_exit) * c)
        t += self.distance / (beta_exit * c)
        # traceWin_phi = actan(a / b)
        return -(self.freq * t) * 180 * 2 * self.bpm_harm * self.bpm_polarity
        '''

    def residuals(self, p):
        field_factor, phase_in, offset = p
        err = self.bpm_phases - [
            self.get_bpm_phases(field_factor, phase_in + delta) + offset
            for delta in self.cav_phases_rad]
        return err

    def sync_phase_diff(self, x, *args):
        phi = x
        field_factor, sync_phase = args
        abs_diff = np.square(self.get_process_params(field_factor, phi)[0] - sync_phase)
        return abs_diff

    def get_entr_phase(self, sync_phase, field_factor):
        bnds = (-np.pi, np.pi)
        res = minimize_scalar(self.sync_phase_diff, 0, bounds=bnds, 
                              args=(field_factor, sync_phase))

        best_fit_phase = res.x
        return best_fit_phase

    def get_process_params(self, field_factor, phase_in):
        return single_bpm_sim_params(field_factor, phase_in, self.Win, self.freq, self.dz,
                                         self.distance, self.q, self.m, self.Ez, self.bpm_harm, self.bpm_polarity)
    '''
    def get_process_params(self, field_factor, phase_in):
        W = self.Win
        t = 0
        a = 0
        b = 0
        for i in range(len(self.Ez) - 1):
            gamma = W / self.m + 1
            beta = (1 - gamma ** -2) ** 0.5
            phi = phase_in + 2 * np.pi * self.freq * (t + 0.5 * self.dz / (beta * c))
            W = W + self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.cos(phi) * self.dz
            gammaExit = W / self.m + 1
            betaExit = (1 - gammaExit ** -2) ** 0.5
            a += self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.sin(phi) * self.dz
            b += self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.cos(phi) * self.dz
            t += self.dz / (0.5 * (beta + betaExit) * c)
        t += self.distance / (betaExit * c)
        entr_phase = np.arctan(a / b)
        if (b < 0 and a < 0):
            entr_phase -= np.pi
        elif (b < 0 and a > 0):
            entr_phase += np.pi

        return entr_phase, a, b

    '''

class DoubleBPMFit(DataFitBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tof_tool = TofPhaseTransformer(self.cavity_name, self.freq, self.m)
        self.periods = self.get_tof_periods()

    def get_non_accel_index(self):
        param, _ = curve_fit(self.sine_fun,
                             self.cav_phases_degree,
                             self.bpm_phases[:, 0])
        offset = param[-1]
        return np.argmin(abs(self.bpm_phases[:, 0] - offset))

    def sine_fun(self, x, amp, freq, delta, offset):
        return amp * np.sin(freq * x + delta) + offset

    def get_tof_periods(self):
        non_accel_idx = self.get_non_accel_index()
        non_accel_phase_diff = self.bpm_phases[non_accel_idx, 0] - \
                               self.bpm_phases[non_accel_idx, 1]
        periods = self.tof_tool.calc_tof_period(non_accel_phase_diff, self.Win)
        return periods

    def transfer_phase_to_energy(self):
        periods = self.periods
        bpm_phase_diff = self.bpm_phases[:, 0] - self.bpm_phases[:, 1]
        energies = self.tof_tool.phase_to_energy(periods, bpm_phase_diff)
        return energies

    def bpm_fit(self):
        p0 = [self.Win, 1, 0]
        plsq = leastsq(self.residuals, p0)
        error = np.std(self.residuals(plsq[0]))

        sync_phase = self.sync_phase * np.pi / 180
        w_in = plsq[0][0]
        field_factor = plsq[0][1]
        phase_in = plsq[0][2]

        phase_opt = self.get_entr_phase(w_in, sync_phase, field_factor)

        computed_energies = np.array([self.simulate_energy(w_in,
                                                           field_factor,
                                                           phase_in + delta)
                                      for delta in self.cav_phases_rad])
        computed_phases = self.tof_tool.energy_to_phase(self.periods, computed_energies)
        delta_start = self.cav_phases_rad[0]
        print(phase_in, delta_start, phase_opt)
        if self.rf_direction == 0:
            rf_phase = (phase_in + delta_start - phase_opt) * 180 / np.pi + self.start_phase
        else:
            rf_phase = -(phase_in + delta_start - phase_opt) * 180 / np.pi + self.start_phase

        w_gain = self.get_process_params(w_in, field_factor, phase_opt)[2]
        rf_phase = phase_wrapping(rf_phase)
        entr_phase = (phase_in +delta_start) * 180 / np.pi
        return (entr_phase, rf_phase, w_in, w_gain, field_factor * self.epk_ref,
                error, self.cav_phases_degree, computed_phases)

    def simulate_energy(self, w, field_factor, phase_in):
        return simulate_energy(w, field_factor, phase_in, self.Ez, 
                               self.freq, self.m, self.q, self.dz)
    '''
    def simulate_energy(self, w, field_factor, phase_in):
        W = w
        t = 0
        for i in range(len(self.Ez) - 1):
            phi = phase_in + 2 * np.pi * self.freq * t
            gamma = W / self.m + 1
            beta = (1 - gamma ** -2) ** 0.5
            W = W + self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.cos(phi) * self.dz
            gammaExit = W / self.m + 1
            betaExit = (1 - gammaExit ** -2) ** 0.5
            t += self.dz / (0.5 * (beta + betaExit) * c)
        return W
    '''

    def residuals(self, p):
        w, field_factor, phase_in = p
        # bpm_diff = self.bpm_phases[:, 1] - self.bpm_phases[:, 0]
        measured_energies = self.transfer_phase_to_energy()
        err = measured_energies - [
            self.simulate_energy(w, field_factor, phase_in + delta)
            for delta in self.cav_phases_rad]
        return err

    def sync_phase_diff(self, x, args):
        phi = x
        w_in, field_factor, sync_phase = args
        return np.square(self.get_process_params(w_in, field_factor, phi)[0] - sync_phase)

    def get_entr_phase(self, w_in, sync_phase, field_factor):
        bnds = (-np.pi, np.pi)
        from scipy.optimize import minimize_scalar
        res = minimize_scalar(self.sync_phase_diff, 0, bounds=bnds, 
                              args=(w_in, field_factor, sync_phase))

        best_fit_phase = res.x
        return best_fit_phase

    def get_process_params(self, W, field_factor, phase_in):
        return double_bpm_sim_params(W, field_factor, phase_in, self.Ez, 
                                     self.freq, self.m, self.q, self.dz)
    '''
    def get_process_params(self, W, field_factor, phase_in):
        t = 0
        a = 0
        b = 0
        for i in range(len(self.Ez) - 1):
            gamma = W / self.m + 1
            beta = (1 - gamma ** -2) ** 0.5
            phi = phase_in + 2 * np.pi * self.freq * (t + 0.5 * self.dz / (beta * c))
            W = W + self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.cos(phi) * self.dz
            gammaExit = W / self.m + 1
            betaExit = (1 - gammaExit ** -2) ** 0.5
            a += self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.sin(phi) * self.dz
            b += self.q * field_factor * 0.5 * (self.Ez[i] + self.Ez[i + 1]) * np.cos(phi) * self.dz
            t += self.dz / (0.5 * (beta + betaExit) * c)
        entr_phase = np.arctan(a / b)
        if (b < 0 and a < 0):
            entr_phase -= np.pi
        elif (b < 0 and a > 0):
            entr_phase += np.pi

        return entr_phase, a, b
    '''


def phase_wrapping(inValue):
    outValue = inValue
    if (abs(inValue) > 180):
        outValue += 180
        while (outValue < 0):
            outValue += 360
        outValue = outValue % 360
        outValue -= 180
    return outValue
