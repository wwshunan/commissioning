from epics import PV
import json

bypass_fname = 'lattice/monitor/bypass.txt'
def get_pv_values(sections):

    vals = {}
    with open('lattice/monitor/monitor_pvs.json') as f:
        data = json.load(f)

    with open(bypass_fname) as f:
        bypass_pvs = f.read()
    bypass_pvs = bypass_pvs.split('\n')
    for s in sections:
        for record_type in data[s]:
            if record_type not in vals:
                vals[record_type] = {}
            if record_type == 'bpms':
                for k_list in data[s][record_type].values():
                    for e in k_list:
                        if e['value'] in bypass_pvs:
                            continue
                        vals[record_type][e['name']] = PV(e['value']).get()
            else:
                for e in data[s][record_type]:
                    if e['value'] in bypass_pvs:
                        continue
                    vals[record_type][e['name']] = PV(e['value']).get()
    return vals

def checkout(stored, sections):
    current_vals = get_pv_values(sections)
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

if __name__ == '__main__':
    pass
