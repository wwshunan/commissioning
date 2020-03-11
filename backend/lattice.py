from epics import PV

cavityList = ['buncher1', 'buncher2', 'cm1-1', 'cm1-2', 'cm1-3', 'cm1-4', 'cm1-5', 'cm1-6']
cavityList += ['cm2-1', 'cm2-2', 'cm2-3', 'cm2-4', 'cm2-5', 'cm2-6']
cavityList += ['cm3-1', 'cm3-2', 'cm3-3', 'cm3-4', 'cm3-5', 'cm3-6']
cavityList += ['cm4-1', 'cm4-2', 'cm4-3', 'cm4-4', 'cm4-5']

lattice_status = {}

def info_lattice(mebt_quads, sols, hebt_quads):
    if len(mebt_quads) != 0:
        lattice_status['MEBT'] = {}
        mebt_pv_fname = 'lattice/MEBT-map.dat'
        quads_sz = len(mebt_quads)
        with open(mebt_pv_fname) as f:
            for i, line in enumerate(f):
                if i < quads_sz:
                    quad_name, _ = line.split()
                    lattice_status['MEBT'][quad_name] = mebt_quads[i]


def set_mebt_magnets(quads):
    mebt_pv_fname = 'lattice/MEBT-map.dat'
    quads_sz = len(quads)
    with open(mebt_pv_fname) as f:
        for i, line in enumerate(f):
            if i < quads_sz:
                _, quad_pv_name = line.split()
                quad_pv = PV(quad_pv_name)
                quad_pv.put(quads[i])

def set_solenoids(sols):
    sol_pv_fname = 'lattice/CM-map.dat'
    sol_sz = len(sols)
    with open(sol_pv_fname) as f:
        for i, line in enumerate(f):
            if line.strip() and i < sol_sz:
                _, sol_pv_name = line.split()
                sol_pv = PV(sol_pv_name)
                sol_pv.put(sols[i])

def set_hebt_magnets(quads):
    hebt_pv_fname = 'lattice/HEBT-map.dat'
    quads_sz = len(quads)
    with open(hebt_pv_fname) as f:
        for i, line in enumerate(f):
            if i < quads_sz:
                _, quad_pv_name = line.split()
                quad_pv = PV(quad_pv_name)
                quad_pv.put(quads[i])

def load_lattice(filename):
    tracewin_file = open(filename, 'r', encoding="utf-8")
    synch_phase_file = open('phasescan/synch-phases/phases.dat', 'w')
    tracewin_phases = []
    mebt_quads = []
    hebt_quads = []
    sols = []
    phase_count = 0

    for line in tracewin_file:
        if not line.strip() or line.startswith(';'):
            continue
        if line.strip().upper() == 'END':
            break
        line_split = line.split()
        if len(line_split) > 9:
            if line_split[9].startswith(('hwr', 'cav', 'buncher')):
                if float(line_split[6]) > 1e-6:
                    cavity_name = cavityList[phase_count]
                    tracewin_phases.append('{0}\t{1}'.format(cavity_name, line_split[3]))
                phase_count += 1
            elif line_split[9].startswith(('quad1', 'quad2')):
                quad_val = abs(round(float(line_split[5]), 2))
                mebt_quads.append(quad_val)
            elif line_split[9] == 'sol':
                coeff = 158.6
                sol_current = abs(round(float(line_split[5]) * coeff, 2))
                sols.append(sol_current)
            elif line_split[9] == 'sol_yuan':
                coeff = 140.8
                sol_current = abs(round(float(line_split[5]) * coeff, 2))
                sols.append(sol_current)
            elif line_split[9].startswith('Q_H'):
                quad_val = abs(round(float(line_split[5]), 2))
                hebt_quads.append(quad_val)

    tracewin_file.close()
    for phase in tracewin_phases:
        synch_phase_file.write('{0}\n'.format(phase))
    synch_phase_file.close()
    return (mebt_quads, sols, hebt_quads)

    set_mebt_magnets(mebt_quads)
    set_solenoids(sols)
    set_hebt_magnets(hebt_quads)

