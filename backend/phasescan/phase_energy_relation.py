from scipy.constants import c
from pathlib import Path
import numpy as np
import pandas as pd


basedir = Path(__file__).resolve().parent

class TofPhaseTransformer(object):
    def __init__(self, cavity_name, freq, mass):
        self.tof_bpm_distance = 2.02635
        self.cavity_name = cavity_name
        self.tof_relations = pd.read_csv(basedir.joinpath('bpm_phase_tof.txt'), sep=r'\s+')
        self.tof_relation = self.tof_relations.loc[
            self.tof_relations['cavity_name'] == self.cavity_name]
        self.slope = self.tof_relation['slope'].iat[0]
        self.trunc = self.tof_relation['trunc'].iat[0]
        self.freq = freq
        self.mass = mass

    def tof2energy(self, tof):
        speed = self.tof_bpm_distance / tof * 1e9
        beta = speed / c
        gamma = (1 - beta ** 2) ** (-0.5)
        w = (gamma - 1) * self.mass
        return w

    def energy2tof(self, energy):
        gamma = energy / self.mass + 1
        beta = (1 - 1 / gamma ** 2) ** 0.5
        speed = beta * c
        tof = self.tof_bpm_distance / speed * 1e9
        return tof

    def energy_to_phase_diff(self, energy):
        tof = self.energy2tof(energy)
        bpm_phase_diff = self.slope * tof + self.trunc
        return bpm_phase_diff

    def calc_tof_period(self, phase_diff, energy):
        tof_max_periods = 10
        phase_diffs = []
        for i in range(-tof_max_periods, tof_max_periods):
            phase_diffs.append(phase_diff + i * 360)
        i = np.argmin(abs(np.array(phase_diffs) -
                          self.energy_to_phase_diff(energy)))
        return i - tof_max_periods

    def phase_to_energy(self, periods, phase):
        phase = phase + periods * 360
        tof = (phase - self.trunc) / self.slope
        return self.tof2energy(tof)

    def energy_to_phase(self, periods, energy):
        tof = self.energy2tof(energy)
        phase = self.slope * tof + self.trunc
        return -(phase - periods * 360)




