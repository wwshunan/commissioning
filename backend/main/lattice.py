from epics import PV
from collections import OrderedDict

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

phase_fname = '../../phasescan/synch-phases/phases.dat'

config_files = {
    'MEBT': 'lattices/MEBT-map.dat',
    'CM1': 'lattices/CM1-map.dat',
    'CM2': 'lattices/CM2-map.dat',
    'CM3': 'lattices/CM3-map.dat',
    'CM4': 'lattices/CM4-map.dat',
    'HEBT': 'lattices/HEBT-map.dat'
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
        lattice_info[section] = read_info(lattice[section], config_files[section])
    return lattice_info

def set_sync_phases(lattice):
    with open(phase_fname, 'a') as fobj:
        for section in lattice:
            cavities = lattice[section].get('cavity')
            if cavities:
                for i, cavity in enumerate(cavities):
                    if abs(float(cavity['amp'])) > 0.001:
                        fobj.write('{}\t{}\n'.format(cavity_names[section][i],
                                                     cavity['phase']))

def set_section(section, config_file):
    magnets = section.get('quad') or section.get('sol')
    if not magnets:
        return
    magnets_sz = len(magnets)
    c = 0
    with open(config_file) as f:
        for line in f:
            if line.strip() and c < magnets_sz:
                _, pv_name = line.split()
                pv = PV(pv_name)
                pv.put(magnets[c])
                c += 1

def set_lattice(lattice):
    print('set_lattice')
    for section in lattice:
        set_section(lattice[section], config_files[section])

def cavity_info_append(section, amp, phase):
    cavity_info = OrderedDict()
    cavity_info['amp'] = amp
    cavity_info['phase'] = phase
    section.append(cavity_info)

def load_lattice(filename):
    tracewin_file = open(filename, 'r', encoding="utf-8")
    synch_phase_file = open('../../phasescan/synch-phases/phases.dat', 'w')
    tracewin_phases = []
    mebt_quads = []
    mebt_bunchers = []
    hebt_quads = []
    cm1_sols = []
    cm1_cavities = []
    cm2_sols = []
    cm2_cavities = []
    cm3_sols = []
    cm3_cavities = []
    cm4_sols = []
    cm4_cavities = []
    count = 0

    for line in tracewin_file:
        if not line.strip() or line.startswith(';'):
            continue
        if line.strip().upper() == 'END':
            break
        line_split = line.split()
        if len(line_split) > 9:
            if line_split[9].startswith('buncher'):
                amp = str(round(float(line_split[5])*600, 2))
                phase = line_split[3]
                cavity_info_append(mebt_bunchers, amp, phase)
            elif line_split[9].startswith(('quad1', 'quad2')):
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
                    # tracewin_phases.append('{0}\t{1}'.format(cavity_name, line_split[3]))
                count += 1
            elif line_split[9].startswith('Q_H'):
                quad_val = abs(round(float(line_split[5]), 2))
                hebt_quads.append(quad_val)

    #tracewin_file.close()
    #for phase in tracewin_phases:
    #    synch_phase_file.write('{0}\n'.format(phase))
    #synch_phase_file.close()

    return {
        'MEBT': {
            'quad': mebt_quads,
            'cavity': mebt_bunchers,
        },
        'CM1': {
            'sol': cm1_sols,
            'cavity': cm1_cavities
        },
        'CM2': {
            'sol': cm2_sols,
            'cavity': cm2_cavities
        },
        'CM3': {
            'sol': cm3_sols,
            'cavity': cm3_cavities
        },
        'CM4': {
            'sol': cm4_sols,
            'cavity': cm4_cavities
        },
        'HEBT': {
            'quad': hebt_quads,
        }
    }

