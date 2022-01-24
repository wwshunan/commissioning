from epics import PV
from collections import OrderedDict
from scipy.interpolate import interp1d
from pathlib import Path
import numpy as np
import pandas as pd

cavityList = ['buncher1', 'buncher2', 'cm1-1', 'cm1-2', 'cm1-3', 'cm1-4', 'cm1-5', 'cm1-6']
cavityList += ['cm2-1', 'cm2-2', 'cm2-3', 'cm2-4', 'cm2-5', 'cm2-6']
cavityList += ['cm3-1', 'cm3-2', 'cm3-3', 'cm3-4', 'cm3-5', 'cm3-6']
cavityList += ['cm4-1', 'cm4-2', 'cm4-3', 'cm4-4', 'cm4-5']
cavity_names = {
    'MEBT': ['buncher1', 'buncher2'],
    'CM1': ['cm1-1', 'cm1-2', 'cm1-3', 'cm1-4', 'cm1-5', 'cm1-6'],
    'CM2': ['cm2-1', 'cm2-2', 'cm2-3', 'cm2-4', 'cm2-5', 'cm2-6'],
    'CM3': ['cm3-1', 'cm3-2', 'cm3-3', 'cm3-4', 'cm3-5', 'cm3-6'],
    'CM4': ['cm4-1', 'cm4-2', 'cm4-3', 'cm4-4', 'cm4-5'],
}

ibs = {
    'target': {
        'CAFe_HEBT_QL_130b': 'QL130.txt',
        'CAFe_HEBT_D1b': 'D1.txt',
        'CAFe_HEBT_QL_350b': 'QL350.txt',
        'CAFe_HEBT_D2b': 'D2.txt',
        'CAFe_HEBT_QL_200b': 'QL200.txt',
        'CAFe_HEBT_QL_250b': 'QL250.txt'
    },
    'detector': {
        'SHANS_Q1_460b': 'DETECTOR-Q1.txt',
        'SHANS_Q2_450b': 'DETECTOR-Q2.txt',
        'SHANS_Q3_630b': 'DETECTOR-Q3.txt',
        'SHANS_D1b': 'DETECTOR-D1.txt',
        'SHANS_D2b': 'DETECTOR-D2.txt'
    }
}

basedir = Path(__file__).resolve().parent.parent
phase_fname = basedir.joinpath('phasescan', 'resources', 'synch_phases.txt')

pv_files = {
    'MEBT': basedir.joinpath('lattice', 'resources', 'MEBT-pvs.txt'),
    'CM1': basedir.joinpath('lattice', 'resources', 'CM1-pvs.txt'),
    'CM2': basedir.joinpath('lattice', 'resources', 'CM2-pvs.txt'),
    'CM3': basedir.joinpath('lattice', 'resources', 'CM3-pvs.txt'),
    'CM4': basedir.joinpath('lattice', 'resources', 'CM4-pvs.txt'),
    'TARGET': basedir.joinpath('lattice', 'resources', 'TARGET-pvs.txt'),
    'DETECTOR': basedir.joinpath('lattice', 'resources', 'DETECTOR-pvs.txt'),
}

def read_info(section, config_file):
    section_info = OrderedDict()
    for element_type in section:
        element_info = OrderedDict()
        for i, el in enumerate(section[element_type]):
            element_info['{}{}'.format(element_type, i+1)] = el
        section_info[element_type] = element_info
    return section_info

def generate_info(lattice):
    lattice_info = OrderedDict()
    for section in lattice:
        lattice_info[section] = read_info(lattice[section], pv_files[section])
    return lattice_info

def set_sync_phases(lattice):
    with open(phase_fname, 'w') as fobj:
        fobj.write('cavity_name synch_phase\n')
        for section in lattice:
            cavities = lattice[section].get('cavities')
            if cavities:
                for i, cavity in enumerate(cavities):
                    if abs(float(cavity['amp'])) > 0.001:
                        fobj.write(f"{cavity_names[section][i]}\t{cavity['phase']}\n")

def set_section(section, pv_file):
    magnets = section.get('magnets')
    if not magnets:
        return

    df = pd.read_csv(pv_file, sep=r'\s+')
    for i, magnet_val in enumerate(magnets):
        pv = PV(df.at[i, 'write_pv_name'])
        pv.put(magnet_val)

def set_lattice(lattice):
    for section in lattice:
        set_section(lattice[section], pv_files[section])

def check_one_section_magnets(section, pv_file):
    magnets_gt_tol = {}
    tolerance = 0.5
    magnets = section.get('magnets')
    if magnets:
        df = pd.read_csv(pv_file, sep=r'\s+')
        for i, magnet_val in enumerate(magnets):
            pv = PV(df.at[i, 'read_pv_name'])
            magnet_rb = pv.get()

            if abs(magnet_rb - magnet_val) > tolerance:
                magnet_name = df.at[i, 'element-name']
                magnets_gt_tol[magnet_name] = round(magnet_val - magnet_rb, 2)
    return magnets_gt_tol

def check_all_magnets(lattice):
    magnets_gt_tol = {}
    for section in lattice:
        magnets_diff_section = check_one_section_magnets(lattice[section], pv_files[section])
        magnets_gt_tol[section] = magnets_diff_section
    return magnets_gt_tol

def cavity_info_append(section, amp, phase):
    cavity_info = OrderedDict()
    cavity_info['amp'] = amp
    cavity_info['phase'] = phase
    section.append(cavity_info)

def cm_lattice(fobj):
    mebt_quads = []
    mebt_bunchers = []
    cm1_sols = []
    cm1_cavities = []
    cm2_sols = []
    cm2_cavities = []
    cm3_sols = []
    cm3_cavities = []
    cm4_sols = []
    cm4_cavities = []
    count = 0

    for raw_line in fobj:
        line = raw_line.decode("utf-8")
        if not line.strip() or line.startswith(';'):
            continue
        if line.strip().upper() == 'END':
            break
        line_split = line.split()
        if len(line_split) > 9:
            if line_split[9].startswith('Ultri_heavy'):
                amp = str(round(float(line_split[5])*1099, 2))
                phase = line_split[3]
                cavity_info_append(mebt_bunchers, amp, phase)
            elif line_split[9].startswith(('q120', 'q150')):
                quad_val = abs(round(float(line_split[5]), 2))
                mebt_quads.append(quad_val)
            elif line_split[9].startswith('sol'):
                if line_split[9] == 'sol_yuan':
                    coeff = 158.6
                else:
                    coeff = 140.8
                sol_current = abs(round(float(line_split[5]) * coeff, 2))
                if count < 6:
                    cm1_sols.append(sol_current)
                elif (count >=6) and (count < 12):
                    cm2_sols.append(sol_current)
                elif (count >= 12) and (count < 18):
                    cm3_sols.append(sol_current)
                else:
                    cm4_sols.append(sol_current)
            elif line_split[9].startswith(('hwr', 'cav')):
                amp = line_split[6]
                phase = line_split[3]
                if count < 6:
                    amp = str(round(float(amp) * 12.5, 2))
                    cavity_info_append(cm1_cavities, amp, phase)
                elif (count >= 6) and (count < 12):
                    amp = str(round(float(amp) * 12.5, 2))
                    cavity_info_append(cm2_cavities, amp, phase)
                elif (count >= 12) and (count < 18):
                    amp = str(round(float(amp) * 12.5, 2))
                    cavity_info_append(cm3_cavities, amp, phase)
                else:
                    amp = str(round(float(amp) * 32 / 3.5, 2))
                    cavity_info_append(cm4_cavities, amp, phase)
                count += 1
    return {
        'MEBT': {
            'magnets': mebt_quads,
            'cavities': mebt_bunchers,
        },
        'CM1': {
            'magnets': cm1_sols,
            'cavities': cm1_cavities
        },
        'CM2': {
            'magnets': cm2_sols,
            'cavities': cm2_cavities
        },
        'CM3': {
            'magnets': cm3_sols,
            'cavities': cm3_cavities
        },
        'CM4': {
            'magnets': cm4_sols,
            'cavities': cm4_cavities
        },
    }

def get_real_current(current, fname):
    data = np.loadtxt(basedir.joinpath('lattice', 'resources', 'I2B', fname))
    interp_ib = interp1d(data[:, 0], data[:, 1])
    real_field = interp_ib(100) * current / 100
    interp_bi = interp1d(data[:, 1], data[:, 0])
    real_current = interp_bi(real_field)
    return real_current.round(1)

def hebt_lattice(fobj, section):
    hebt_magnets = []

    for raw_line in fobj:
        line = raw_line.decode("utf-8")
        if not line.strip() or line.startswith(';'):
            continue
        if line.strip().upper() == 'END':
            break
        line_split = line.split()
        if len(line_split) > 9 and line_split[9] in ibs[section].keys():
            magnet_val = abs(float(line_split[5]))
            ib_fname = ibs[section][line_split[9]]
            real_current = get_real_current(magnet_val, ib_fname)

            if line_split[9] == 'CAFe_HEBT_D1b':
                real_current *= -1

            hebt_magnets.append(real_current)

    return {
        section.upper(): {
            'magnets': hebt_magnets,
        },
    }

def load_lattice(tracewin_file, section):
    if section == 'cm':
        return cm_lattice(tracewin_file)
    elif section == 'target':
        return hebt_lattice(tracewin_file, 'target')
    else:
        return hebt_lattice(tracewin_file, 'detector')
    tracewin_file.close()

