from epics import PV
from rq import get_current_job
import numpy as np
import time, random


configs = {
    'quad': {
        'pvs': ['HEBT_PS:T0_Q-01:CurSet', 'HEBT_PS:T0_Q-02:CurSet',
                'HEBT_PS:T0_D-01:CurSet', 'HEBT_PS:T2_Q-01:CurSet',
                'HEBT_PS:T2_D-01:CurSet', 'HEBT_PS:T2_Q-02:CurSet',
                'HEBT_PS:T2_Q-03:CurSet', 'HEBT_PS:T2_Q-04:CurSet',
                'HEBT_PS:T2_CH-03:CurSet', 'HEBT_PS:T2_CV-03:CurSet'
                ],
        'log_names': ['index', 't0q01', 't0q02', 't0d01', 't2q01', 't2d01', 't2q02',
                      't2q03', 't2q04', 't2ch03', 't2cv03', 'target'
                      ],
        'lb': [100, 100, -700, 100, 500, 100, 100, 100, -180, -180],
        'ub': [370, 370, -500, 380, 700, 600, 600, 600,  180,  180]

    },
    'steer': {
        'pvs': ['HEBT_PS:T0_CH-01:CurSet', 'HEBT_PS:T0_CV-01:CurSet',
                'HEBT_PS:T2_CH-01:CurSet', 'HEBT_PS:T2_CV-01:CurSet',
                'HEBT_PS:T2_CH-02:CurSet', 'HEBT_PS:T2_CV-02:CurSet',
                'HEBT_PS:T2_CH-03:CurSet', 'HEBT_PS:T2_CV-03:CurSet'
                ],
        'log_names': ['index', 't0ch01', 't0cv01', 't2ch01', 't2cv01', 't2ch02', 't2cv02',
                      't2ch03', 't2cv03', 'target'
                      ],
        'lb': [-180, -180, -180, -180, -180, -180, -180, -180],
        'ub': [180,  180,  180,  180,  180,  180,  180,  180]

    }
}
rb_pvs = {
    'quad_scan': ['HEBT_PS:T0_Q-01:CurMon', 'HEBT_PS:T0_Q-02:CurMon', 
                  'HEBT_PS:T0_D-01:CurMon', 'HEBT_PS:T2_Q-01:CurMon',
                  'HEBT_PS:T2_D-01:CurMon', 'HEBT_PS:T2_Q-02:CurMon',
                  'HEBT_PS:T2_Q-03:CurMon', 'HEBT_PS:T2_Q-04:CurMon',
                  'HEBT_PS:T2_CH-03:CurMon', 'HEBT_PS:T2_CV-03:CurMon'
                  ],
    'steer_scan': ['HEBT_PS:T0_CH-01:CurMon', 'HEBT_PS:T0_CV-01:CurMon', 
                   'HEBT_PS:T2_CH-01:CurMon', 'HEBT_PS:T2_CV-01:CurMon',
                   'HEBT_PS:T2_CH-02:CurMon', 'HEBT_PS:T2_CV-02:CurMon', 
                   'HEBT_PS:T2_CH-03:CurMon', 'HEBT_PS:T2_CV-03:CurMon'
                   ]
}

T2HR = 'SS_BD:CHAN1_AVG_SUB_OST_VAL'
SSFC = 'SS_BD:CHAN2_AVG_SUB_OST_VAL'
T2FC = 'SS_BD:CHAN0_AVG_SUB_OST_VAL'
halo1 = 'HEBT_BD:CHAN2_AVG_SUB_OST_VAL'
halo2 = 'HEBT_BD:CHAN3_AVG_SUB_OST_VAL'
halo3 = 'HEBT_BD:CHAN7_AVG_SUB_OST_VAL'
halo4 = 'HEBT_BD:CHAN5_AVG_SUB_OST_VAL'
halo5 = 'HEBT_BD:CHAN6_AVG_SUB_OST_VAL'

def t2fc_max(repeat, step): # for T2FC max
    ilist2 = np.zeros(repeat)
    t2fc_pv = PV(T2FC)
    for i in range(repeat):
        ilist2[i] = t2fc_pv.get()
        time.sleep(step)
    current2 = np.median(ilist2)
    return current2

def ssfc_max(repeat, step): # for SSFC max 
    ilist2 = np.zeros(repeat)
    ssfc_pv = PV(SSFC)
    for i in range(repeat):
        ilist2[i] = ssfc_pv.get()
        time.sleep(step)
    current2 = np.median(ilist2)
    return current2
    
def halo_min(repeat, step): # for halo min 
    current_pv_names = [T2HR, halo1, halo2, halo3, halo4, halo5]
    current_pvs = [PV(x) for x in current_pv_names]
    current_array = np.zeros((len(current_pvs), repeat))

    for i in range(repeat):
        for j in range(len(current_pvs)):
            current_array[j, i] = current_pvs[j].get()
        time.sleep(step)
    
    current2 = -np.sum(np.median(current_array, axis=1))
    return current2

def ssfc_sub_halo_max(repeat, step, correct_factor): # for ssfc-halo max 
    current_pv_names = [T2HR, halo1, halo2, halo3, halo4, halo5, SSFC]
    current_pvs = [PV(x) for x in current_pv_names]
    current_array = np.zeros((len(current_pvs), repeat))
    for i in range(repeat):
        for j in range(len(current_pvs)):
            current_array[j, i] = current_pvs[j].get()
        time.sleep(step)
    current2 = np.median(current_array[-1]) / correct_factor - np.sum(np.median(current_array[:-1], axis=1))
    return current2

#def gety4(repeat, p=False, mode=1):
#    global w, step, record
#    ilist1 = np.zeros(repeat)
#    ilist2 = np.zeros(repeat)
#    for i in range(repeat):
#        ilist1[i] = caget(acct1)
#        ilist2[i] = caget(T2FC)
#        time.sleep(step)
#    current1 = np.median(ilist1)
#    current2 = np.median(ilist2)
#    record = [current2, current2 / current1]
#    if p:
#        print(round(current2, 2), str(round(current2 / current1 * 100, 2)) + '%')
#    if mode == 2:
#        return current2 / current1 / w * 50
#    return current2

def factory(opt_target, repeat, step, correct_factor):
    if opt_target == "T2FC Max":
        target = t2fc_max(repeat, step)
    elif opt_target == "SSFC Max":
        target = ssfc_max(repeat, step)
    elif opt_target == "Halo Min":
        target = halo_min(repeat, step)
    else:
        target = ssfc_sub_halo_max(repeat, step, correct_factor)
    return target

def repeat_calc(freq):
    mfc1 = 50
    std_var = 0.004*mfc1
    var = factory("T2FC Max", 100, 1 / freq, 0)
    repeat = min(round(var/std_var)+1, 600)
    return repeat
  
def hebt_q_match(opt_target, opti_param, freq, repeat, correct_factor=2, iter_max=100, ssfc_min=65, w=2):
    repeat = repeat_calc(freq)
    xbest = []
    ybest = -1000 
    step = 1 / freq
    pvs = [PV(s) for s in configs[opti_param]['pvs']]
    x = [s.get() for s in pvs]
    print(x)
    results = []

    job = get_current_job()
    job.meta['stop'] = False
    job.save()
    for i in range(iter_max+1):
        y = factory(opt_target, repeat, step, correct_factor)
        if i>0 and y/yold<0.9:
            x[idx] = xold
            print(xold)
            pvs[idx].put(x[idx])
            time.sleep(2)
            y = factory(opt_target, repeat, step, correct_factor)
        if i>0 and y/ybest>1.1:
            y = factory(opt_target, repeat, step, correct_factor)
        iter_result = dict(zip(configs[opti_param]['log_names'], [i] + x + [round(y, 4)]))
        results.append(iter_result)
        if y > ybest:
            ybest = y
            xbest = x[:]
        idx = random.randint(0, len(configs[opti_param]['pvs']) - 1)
        dx = 2.0 # quads
        if idx == 2 or idx == 4: # dipoles
            dx = 0.1
        if idx == 8 or idx == 9: # steers 
            dx = 0.5
        if idx == 3: # achromatic quad
            dx == 1.0
        if x[idx] > configs[opti_param]['ub'][idx] - dx:
            dx = -dx
        pvs[idx].put(x[idx] + dx)
        time.sleep(2)
        y2 = factory(opt_target, repeat, step, correct_factor)
        ssfc_pv = PV(SSFC)
        while ssfc_pv.get() < ssfc_min and not job.meta.get('stop'):
            time.sleep(5)
            y2 = factory(opt_target, repeat, step, correct_factor)
        xold = x[idx]
        yold = y
        job.refresh()
        if job.meta.get('stop'):
            break
        x[idx] = np.clip(round(x[idx] + dx * w * (y2 - y), 2), 
                         configs[opti_param]['lb'][idx], 
                         configs[opti_param]['ub'][idx])
        pvs[idx].put(x[idx])
        time.sleep(2)

    for i in range(len(xbest)):
        pvs[i].put(xbest[i])
    return results

#run(100, mode=1)

