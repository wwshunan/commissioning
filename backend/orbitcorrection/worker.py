import time
from .orbit import Orbit, MeasureResponseMatrix, ResponseMatrix

def create_task(keys, rm_step, sc_step, rm_lim, sc_lim, alpha):
    orbit = Orbit(keys)
    cors, bpms = orbit.cors, orbit.bpms
    method = MeasureResponseMatrix(cors, bpms, rm_step, sc_step, rm_lim, sc_lim)
    orbit.response_matrix = ResponseMatrix(method=method)
    orbit.response_matrix.calculate()
    angles = orbit.correct(alpha)
    return angles