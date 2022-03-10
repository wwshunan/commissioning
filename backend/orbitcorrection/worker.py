from .orbit import (OrbitGather, CorrectorGather, Orbit, Corrector,
                    MeasureResponseMatrix, ResponseMatrix)
import numpy as np

def create_task(keys, rm_step, sc_step, rm_lim, sc_lim, alpha):
    gathered_orbit = OrbitGather(keys)
    gathered_cors = CorrectorGather(keys)

    orbit = Orbit(gathered_orbit, gathered_cors, rm_lim, sc_lim)
    method = MeasureResponseMatrix(gathered_cors, gathered_orbit, rm_step, sc_step, rm_lim, sc_lim)
    orbit.response_matrix = ResponseMatrix(method=method)
    orbit.response_matrix.calculate()
    angles = orbit.correct(alpha)
    return angles

def set_corrector_strength(keys, strength):
    gathered_orbit = OrbitGather(keys)
    gathered_cors = CorrectorGather(keys)
    optimal_orbit = 0xFFFF
    cor_objs = []
    optimal_correctors = []

    for cor_obj, cor in zip(gathered_cors.cors, strength):
        cor_obj.current = cor['value']

    while True:
        for i, cor in enumerate(strength):
            if abs(gathered_cors[i].current - cor['value']) > 0.2:
                break
        else:
            break
        orbit = gathered_orbit.get_orbit()
        if optimal_orbit > np.average(np.sum(orbit)):
            optimal_correctors = []
            for cor_obj in cor_objs:
                optimal_correctors.append(cor_obj.current)

    if optimal_correctors:
        for cor, val in zip(gathered_cors, optimal_correctors):
            cor.current = val



