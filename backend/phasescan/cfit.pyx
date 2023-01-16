# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
from libc.math cimport cos, sin, atan 
cimport numpy as np
import numpy as np

DEF c = 299792458.0
DEF pi = 3.141592653589793

def get_bpm_phases(double field_factor, double phase_in, double Win, double freq, 
                   double dz, double distance, double q, double m, double[:] Ez, 
                   int bpm_harm, int bpm_polarity):
    cdef:
        double t = 0.0, W = Win
        double phi, beta, gamma, gamma_exit, beta_exit
        int i, N = Ez.shape[0]

    for i in range(N - 1):
        phi = phase_in + 2 * pi * freq * t
        gamma = W / m + 1
        beta = (1 - gamma ** -2) ** 0.5
        W +=  q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * cos(phi) * dz
        gamma_exit = W / m + 1
        beta_exit = (1 - gamma_exit ** -2) ** 0.5
        t += dz / (0.5 * (beta + beta_exit) * c)
    t += distance / (beta_exit * c)

    return -(freq * t) * 360 * bpm_harm * bpm_polarity

def single_bpm_sim_params(double field_factor, double phase_in, double Win, double freq, 
                          double dz, double distance, double q, double m, double[:] Ez, 
                          int bpm_harm, int bpm_polarity):
    cdef:
        double t = 0.0, W = Win, entr_phase 
        double phi, beta, gamma, gamma_exit, beta_exit, a = 0.0, b = 0.0
        int i, N = Ez.shape[0]

    for i in range(N - 1):
        gamma = W / m + 1
        beta = (1 - gamma ** -2) ** 0.5
        phi = phase_in + 2 * pi * freq * (t + 0.5 * dz / (beta * c))
        W += q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * cos(phi) * dz
        gammaExit = W / m + 1
        betaExit = (1 - gammaExit ** -2) ** 0.5
        a += q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * sin(phi) * dz
        b += q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * cos(phi) * dz
        t += dz / (0.5 * (beta + betaExit) * c)
    t += distance / (betaExit * c)
    entr_phase = atan(a / b)
    if (b < 0 and a < 0):
        entr_phase -= pi
    elif (b < 0 and a > 0):
        entr_phase += pi

    return entr_phase, a, b

def simulate_energy(double w, double field_factor, double phase_in, double[:] Ez,
                    double freq, double m, double q, double dz):
    cdef:
        double phi, gamma, beta, gammaExit, betaExit, W = w, t = 0.0
        int i, N = Ez.shape[0]

    for i in range(N - 1):
        phi = phase_in + 2 * pi * freq * t
        gamma = W / m + 1
        beta = (1 - gamma ** -2) ** 0.5
        W = W + q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * cos(phi) * dz
        gammaExit = W / m + 1
        betaExit = (1 - gammaExit ** -2) ** 0.5
        t += dz / (0.5 * (beta + betaExit) * c)
    return W

def double_bpm_sim_params(double W, double field_factor, double phase_in, double[:] Ez,
                          double freq, double m, double q, double dz):
    cdef:
        double t = 0, a = 0.0, b = 0.0, gamma, beta, phi, gammaExit, betaExit, entr_phase
        int i, N = Ez.shape[0]

    for i in range(N - 1):
        gamma = W / m + 1
        beta = (1 - gamma ** -2) ** 0.5
        phi = phase_in + 2 * pi * freq * (t + 0.5 * dz / (beta * c))
        W = W + q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * cos(phi) * dz
        gammaExit = W / m + 1
        betaExit = (1 - gammaExit ** -2) ** 0.5
        a += q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * sin(phi) * dz
        b += q * field_factor * 0.5 * (Ez[i] + Ez[i + 1]) * cos(phi) * dz
        t += dz / (0.5 * (beta + betaExit) * c)
    entr_phase = atan(a / b)
    if (b < 0 and a < 0):
        entr_phase -= pi
    elif (b < 0 and a > 0):
        entr_phase += pi

    return entr_phase, a, b