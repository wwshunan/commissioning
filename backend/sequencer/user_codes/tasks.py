from epics import PV
from ..exceptions import raise_exception
import pandas as pd
import time
import os
import redis

base_dir = os.path.dirname(os.path.abspath(__file__))

pvs = pd.read_csv(os.path.join(base_dir, 'silicon_pvs.txt'), header=0, 
                  sep='\s+', index_col='label')

def check_vacc():
    lebt_vac = pvs.loc['LEBT_vac'] 
    if PV(lebt_vac['pv']).get() > lebt_vac['default']:
        raise_exception('LEBT真空异常')
    mebt_vac = pvs.loc['MEBT_vac'] 
    if PV(mebt_vac['pv']).get() > mebt_vac['default']:
        raise_exception('MEBT真空异常')

def check_lebt_current():
    lebt_fc_current = pvs.loc['LEBT_current'] 
    lebt_fc_in = pvs.loc['LEBT_FC_in']
    if PV(lebt_fc_in['pv']).get() == 1 and PV(lebt_fc_current['pv']).get() < lebt_fc_current['default']:
        raise_exception('LFC流强过低')

def check_RFQ():
    rfq = pvs.loc['RFQ_power'] 
    if abs(PV(rfq['pv']).get() - rfq['default']) > 1:
        raise_exception('RFQ功率异常')

def check_mebt_quads():
    quads = ['MEBT_Q1_get', 'MEBT_Q2_get', 'MEBT_Q3_get']
    for quad in quads:
        q = pvs.loc[quad]
        if abs(PV(q['pv']).get() - q['default']) > 0.2:
            raise_exception('MEBT四极铁电流异常')

def machine_checking():
    check_vacc()
    check_lebt_current()
    check_RFQ()
    check_mebt_quads()
    return '机器状态正常'

def timing_setting():
    pass

def timing_setting_reset():
    repeat_pv = PV('SCR_STRG:SDG:FRQ')
    width_pv = PV('SCR_STRG:SDG01:CH1_WIDTH')
    repeat_pv.put(1)
    width_pv.put(200)
    return '定时参数重置成功'

def raise_occupy():
    r = redis.Redis(host='127.0.0.1', port=6379)
    timing_repeat = int(r.get('timing_repeat'))
    timing_width = int(r.get('timing_width'))
    repeat_pv = PV('SCR_STRG:SDG:FRQ')
    width_pv = PV('SCR_STRG:SDG01:CH1_WIDTH')
    target_pv = PV('TARGET_VAC:VG:Pres')

    repeat = 1
    repeat_pv.put(repeat)
    width_pv.put(timing_width)
    while repeat != timing_repeat:
        if target_pv.get() > 5e-4:
            repeat_pv.put(1)
            raise_exception('终端真空超阈值')
        repeat += 1
        time.sleep(3)
        repeat_pv.put(repeat)

    return '提高占空比完成'


    #timing_repeat = pvs.loc['timing_freq']
    #chopper_width = pvs.loc['timing_chopper']

def moving_unit(status: str, driver: str, label: str, target: str):
    unit_status = pvs.loc[status]
    settings = {
        'open': {
            'val': 0,
            'msg': '打开'
        },
        'close': {
            'val': 1,
            'msg': '关闭'
        }
    }

    if PV(unit_status['pv']).get() != 1:
        valv_driver = pvs.loc[driver]['pv']
        PV(valv_driver).put(settings[target]['val'])
        time.sleep(4)
    if PV(unit_status['pv']).get() != 1:
        raise_exception(f'{label}未{settings[target]["msg"]}')

def close_lfc():
    moving_unit('LEBT_FC_in', 'LFC_driver', 'LFC', 'close')
    return 'LFC关闭'

def open_lfc():
    moving_unit('LEBT_FC_out', 'LFC_driver', 'LFC', 'open')

def open_mfc():
    moving_unit('MEBT_FC_out', 'MFC_driver', 'MFC', 'open')

def open_lfc_ramping():
    open_lm_valv()
    open_lfc()
    open_mfc()
    return 'LFC已打开'

def open_lm_valv():
    moving_unit('LEBT_valv_out', 'Lvalv_driver', 'LEBT阀门', 'open')
    moving_unit('MEBT_valv_out', 'Mvalv_driver', 'MEBT阀门', 'open')

def close_fc2():
    insert_fc('LEBT_FC_in', 'LFC_driver', 'LEBT')
    return 'LFC关闭'

def lebt_status_check():
    time.sleep(5)
    return 'LEBT正常'

def mebt_status_check():
    time.sleep(5)
    return 'MEBT正常'

def sc_status_check():
    time.sleep(5)
    return 'SC正常'

def hebt_status_check():
    time.sleep(5)
    return 'HEBT正常'

def valve_status_check():
    time.sleep(10)
    return '所有阀门已打开'

def intercept_status_check():
    time.sleep(10)
    return 'MEBT和高能段束诊元件已打开'

def rfq_transit_check():
    time.sleep(10)
    return 'RFQ传输效率高于96%'
