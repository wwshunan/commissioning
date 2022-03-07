from .orbit import OrbitGather, CorrectorGather, Orbit, MeasureResponseMatrix, ResponseMatrix

def create_task(keys, rm_step, sc_step, rm_lim, sc_lim, alpha):
    gathered_orbit = OrbitGather(keys)
    gathered_cors = CorrectorGather(keys)

    orbit = Orbit(gathered_orbit, gathered_cors)
    method = MeasureResponseMatrix(gathered_cors, gathered_orbit, rm_step, sc_step, rm_lim, sc_lim)
    orbit.response_matrix = ResponseMatrix(method=method)
    orbit.response_matrix.calculate()
    angles = orbit.correct(alpha)
    return angles