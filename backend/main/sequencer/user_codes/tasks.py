from epics import PV
from backend.main.utils import checkout_sections
from backend.main.flask_app_mod import app
import time
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

def open_fc1():
    pv = PV('LEBT_BD:FC_01:Rem')
    pv.put(0)
    time.sleep(2)
    rb_val = PV('LEBT_BD:FC_01:In').get()
    if rb_val == 1:
        return "FC1已打开"
    return 'FC1打开失败'

def open_fc2():
    pv = PV('FC2_out')
    pv.put(0)
    time.sleep(2)
    rb_val = PV('T:axis5_real_pos_r').get()
    if rb_val == 1:
        return "FC2处于关闭状态"
    return 'FC2处于打开状态'

def close_fc2():
    pos = -137
    pv = PV('FC2_in')
    pv.put(pos)
    time.sleep(2)
    rb_val = PV('T:axis5_real_pos_r').get()
    if abs(rb_val) > abs(float(pos)) - 5:
        return "FC2处于打开状态"
    return 'FC2处于关闭状态'

def lebt_status_check():
    with app.app_context():
        diffs = checkout_sections(['LEBT'])

    result = []
    [result.append(k) for i in diffs for k in diffs[i]]
    if result:
        return ', '.join(result) + '异常'
    else:
        return 'LEBT正常'

def mebt_status_check():
    with app.app_context():
        diffs = checkout_sections(['MEBT'])

    result = []
    [result.append(k) for i in diffs for k in diffs[i]]
    if result:
        return ', '.join(result) + '异常'
    else:
        return 'MEBT正常'

def sc_status_check():
    with app.app_context():
        diffs = checkout_sections(['SC'])

    result = []
    [result.append(k) for i in diffs for k in diffs[i]]
    if result:
        return ', '.join(result) + '异常'
    else:
        return 'SC正常'

def hebt_status_check():
    with app.app_context():
        diffs = checkout_sections(['B-HEBT'])

    result = []
    [result.append(k) for i in diffs for k in diffs[i]]
    if result:
        return ', '.join(result) + '异常'
    else:
        return 'HEBT正常'

def valve_status_check():
    filename = os.path.join(base_dir, 'valve/pvs.txt')
    closed_valves = []
    with open(filename) as fobj:
        for line in fobj:
            valve_name, valve_pv = line.split()
            valve_val = PV(valve_pv).get()
            if not valve_val:
                closed_valves.append(valve_name)
    if len(closed_valves) > 0:
        return ', '.join(closed_valves) + '没打开!'
    else:
        return '所有阀门已打开'

def intercept_status_check():
    filename = os.path.join(base_dir, 'intercepts/pvs.txt')
    inserted_elements = []
    with open(filename) as fobj:
        for line in fobj:
            name, pv, pos = line.split()
            val = PV(pv).get()
            if abs(val) < abs(float(pos)) - 5:
                inserted_elements.append(name)
    if len(inserted_elements) > 0:
        return ', '.join(inserted_elements) + '没打开!'
    else:
        return 'MEBT和高能段束诊元件已打开'

def rfq_transit_check():
    acct1 = PV('ADS:ACCT1').get()
    acct2 = PV('ADS:ACCT2').get()
    transit_efficient = acct2 / acct1 if acct1 > 0 else 0
    if transit_efficient < 0.96:
        return 'RFQ传输效率低于96%'
    else:
        return 'RFQ传输效率高于96%'
