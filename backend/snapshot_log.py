from epics import PV
import time
import numpy as np
import os

bpm_fnames = ['x.txt', 'y.txt', 'phase.txt']
bpm_fnames = [os.path.join('lattice/monitor/bpm', fname)
              for fname in bpm_fnames]
magnet_fnames = ['MEBT-magnets-mon.txt', 'CM1-magnets-mon.txt', 'CM2-magnets-mon.txt',
                 'CM3-magnets-mon.txt', 'CM4-magnets-mon.txt', 'HEBT-magnets-mon.txt']
magnet_fnames = [os.path.join('lattice/monitor/magnets', fname)
                 for fname in magnet_fnames]
amp_fnames = ['MEBT-amp-mon.txt', 'cm1-amp-mon.txt', 'cm2-amp-mon.txt',
              'cm3-amp-mon.txt', 'cm4-amp-mon.txt']
amp_fnames = [os.path.join('lattice/monitor/amp', fname)
              for fname in amp_fnames]
phase_fnames = ['MEBT-phase-mon.txt', 'cm1-phase-mon.txt', 'cm2-phase-mon.txt',
                'cm3-phase-mon.txt', 'cm4-phase-mon.txt']
phase_fnames = [os.path.join('lattice/monitor/phase', fname)
                for fname in phase_fnames]

pv_fnames = {
    'amps': amp_fnames,
    'phases': phase_fnames,
    'magnets': magnet_fnames,
    'bpms': bpm_fnames
}

def get_pv_values():
    vals = {}
    for label in pv_fnames:
        vals[label] = get_one_type_values(pv_fnames[label])
    return vals

def get_one_type_values(fnames):
    vals = {}
    for fname in fnames:
        with open(fname) as fobj:
            for each_line in fobj:
                name, pv_name = each_line.split()
                vals[name] = PV(pv_name).get()
    return vals

def checkout(stored):
    current_vals = get_pv_values()
    phase_tol = 1
    amp_tol = 0.2
    magnet_tol = 0.2
    bpm_pos_tol = 0.3
    bpm_phase_tol = 2
    diffs = {}
    for k in current_vals:
        diffs[k] = {}
        for name in current_vals[k]:
            current_val = current_vals[k][name]
            preview_val = stored[k][name]
            diff = current_val - float(preview_val)
            if ((k == 'amps' and abs(diff) > amp_tol) or
                (k == 'phases' and abs(diff) > phase_tol) or
                (k == 'magnets' and abs(diff) > magnet_tol) or
                (k == 'bpms' and 'phase' in name and abs(diff) > bpm_phase_tol) or
                (k == 'bpms' and 'phase' not in name and abs(diff) > bpm_pos_tol)
            ):
                diffs[k][name] = diff
    return diffs
