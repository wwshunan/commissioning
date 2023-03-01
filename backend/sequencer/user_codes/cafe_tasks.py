from epics import PV
from ..exceptions import raise_exception
import pandas as pd
import time
import os
import redis
import numpy as np

base_dir = os.path.dirname(os.path.abspath(__file__))

pvs = pd.read_csv(os.path.join(base_dir, 'cafe_pvs.txt'), header=0, 
                  sep='\s+', index_col='label')

def check_lebt_current():
    lebt_fc_current = pvs.loc['LEBT_current'] 
    lebt_fc_in = pvs.loc['LEBT_FC_in']
    if PV(lebt_fc_in['pv']).get() == 1 and PV(lebt_fc_current['pv']).get() < lebt_fc_current['default']:
        raise_exception('LFC流强过低')


def timing_setting():
    pass

def timing_setting_reset():
    repeat_pv = PV('SCR_STRG:SDG:FRQ')
    width_pv = PV('SCR_STRG:SDG01:CH1_WIDTH')
    repeat_pv.put(1)
    width_pv.put(200)
    return '定时参数重置成功'

def moving_unit(status: str, driver: str, target: str, msg: str):
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

    if PV(unit_status['pv']).get() != settings[target]['val']:
        driver_pvname = pvs.loc[driver]['pv']
        PV(driver_pvname).put(settings[target]['val'])
        time.sleep(15)

    if 't2_fc' in status:
        if PV(unit_status['pv']).get() > -99:
            raise_exception(msg)
    else:
        if PV(unit_status['pv']).get() != settings[target]['val']:
            raise_exception(msg)

def close_lebt_dump():
    moving_unit('LEBT_dump_in', 'Ldump_driver', 'close', 'LEBT_DUMP无法插入，请手动操作！')
    return 'LEBT Dump关闭'

def close_lebt_dump_hebt():
    moving_unit('LEBT_dump_in', 'Ldump_driver', 'close', 'LEBT_DUMP无法插入，请手动操作！')
    raise_exception("请手动设定HEBT Lattice") 

def open_lebt_dump_hebt():
    repeat = PV(pvs.loc['timing_freq']['pv'])
    width = PV(pvs.loc['timing_chopper']['pv'])
    if (repeat.get() * width.get()) > 200:
        raise_exception("Duty factor is too high, LEBT DUMP is NOT allowed to be pulled out！") 
    if PV(pvs.loc['mps_status']['pv']).get() != 0:
        raise_exception("束流总运行状态不具备LEBT_DUMP拔出条件，请检查！")
    moving_unit('LEBT_dump_in', 'Ldump_driver', 'open', 'LEBT_DUMP无法拔出，请手动操作！')
    raise_exception("请手动测能量！")

def open_lebt_dump():
    repeat = PV(pvs.loc['timing_freq']['pv'])
    width = PV(pvs.loc['timing_chopper']['pv'])
    if (repeat.get() * width.get()) > 200:
        raise_exception("Duty factor is too high, LEBT DUMP is NOT allowed to be pulled out！") 
    if PV(pvs.loc['mps_status']['pv']).get() != 0:
        raise_exception("束流总运行状态不具备LEBT_DUMP拔出条件，请检查！")
    moving_unit('LEBT_dump_in', 'Ldump_driver', 'open', 'LEBT_DUMP无法拔出，请手动操作！')

def move_fcs():
    elements_to_insert = ['ss_fc', 't2_fc', 'mfc']
    for el in elements_to_insert:
        put_pv = PV(pvs.loc[el+'_in_set']['pv'])
        put_pv.put(1)
    
    PV(pvs.loc["t2_hr_set"]["pv"]).put(0)
    time.sleep(15)
    for el in elements_to_insert:
        get_pv = PV(pvs.loc[el+'_get']['pv'])
        if get_pv.get() > 0.5:
            raise_exception(f"{el}无法插入，请手动操作")

    #t2_hr_rb = PV(pvs.loc['t2_hr_get']['pv']).get()
    #if t2_hr_rb > 0.5:
     #   raise_exception("T2_HR无法打开，请手动操作")

def diag_sampling_setting(who: str):
    window_width = PV(pvs.loc[f"{who}_window_width"]['pv'])
    start = PV(pvs.loc[f"{who}_start"]['pv'])
    width = PV(pvs.loc[f"{who}_width"]['pv'])
    noise_start = PV(pvs.loc[f"{who}_noise_start"]['pv'])
    noise_width = PV(pvs.loc[f"{who}_noise_width"]['pv'])
    window_width.put(0)   #0 for 80us
    start.put(250)
    width.put(200)
    noise_start.put(900)
    noise_width.put(200)
    action = PV(pvs.loc[f"{who}_action"]["pv"])
    action.put(1)

def bpm_sampling_setting(who: str):
    window_width = PV(pvs.loc[f"{who}_window_width"]['pv'])
    start = PV(pvs.loc[f"{who}_start"]['pv'])
    width = PV(pvs.loc[f"{who}_width"]['pv'])
    window_width.put(0)  #0 for 1ms
    start.put(100)
    width.put(800)

def diag_gain_setting():
    gains = ['mfc', 't2hr', 't2fc', 'ssfc', 'sshr1', 'sshr2', 'sshr3', 'sshr4', 'sshr5']
    for g in gains:
        PV(pvs.loc[f"{g}_gain"]["pv"]).put(2)  #对应1e5

    signals = ['mfc', 't2hr', 'sshr']
    for s in signals:
        diag_sampling_setting(s)

def current_checking(diag_name: str, msg: str):
    currents = []
    current_pv = PV(pvs.loc[diag_name]['pv'])

    for _ in range(10):
        current_val = current_pv.get()
        currents.append(current_val)

    mfc_avg = np.average(currents)
    if mfc_avg < 5:
        raise_exception(msg)

def mfc_current_checking():
    current_checking("mfc", "MFC流强过低，请检查RFQ或离子源！")

def freq_setting():
    freq = PV(pvs.loc["timing_freq"]["pv"])
    freq.put(10)

def t2fc_current_checking():
    current_checking("t2fc", "T2FC流强过低，请检查HEBT Lattice！")

def open_t2fc():
    moving_unit('t2_fc_get', 't2_fc_out_set', 'close', 'T2FC无法拔出，请手动操作！')  #"close " for open

def restore_lebt_collimator():
    collimators = ['cm1', 'cm2', 'cm3']
    r = redis.Redis(host='127.0.0.1', port=6379)

    for cm in collimators:
        cm_val = r.get(cm)
        cm_set_pv = PV(pvs.loc[f'{cm}_set']['pv'])
        cm_set_pv.put(float(cm_val.decode()))
        cm_act_pv = PV(pvs.loc[f'{cm}_action']['pv'])
        cm_act_pv.put(1)


    time.sleep(10)

    for cm in collimators:
        cm_val = float(r.get(cm).decode())
        cm_get_pv = PV(pvs.loc[f'{cm}_get']['pv'])
        
        if abs(cm_get_pv.get() - float(cm_val)) > 0.1:
            raise_exception("LEBT光阑设定有误，请检查！")

    raise_exception("设定无误，请手动选择BPM衰减，完成后将转为终端模式")

def bpm_gain_setting():
    #gains = ['t2hr','ssfc', 'sshr1', 'sshr2', 'sshr3', 'sshr4', 'sshr5']
    gains = ['T2_BPM2', 'T2_BPM3', 'SS_BPM']
    for g in gains:
        PV(pvs.loc[f"{g}_Gain"]["pv"]).put(10)  #对应0dB

    #signals = ['t2hr', 'sshr']
    signals = ['ssbpm', 't2bpm2', 't2bpm3']
    for s in signals:
        bpm_sampling_setting(s)

def restore_mps():
    bypasses = ['hebt_ring_bypass', 'mfc_bypass', 'T2_FC_bypass', 
                'SS_VS_bypass', 'SS_FC_bypass']
    for b in bypasses:
        PV(pvs.loc[b]['pv']).put(0)

def open_ssfc():
    moving_unit('ss_fc_get', 'ss_fc_out_set', 'close', 'SSFC无法拔出，请手动操作！')  #"close" for open
    raise_exception("请手动转入终端模式！")

def dipole_status_checking():
    dipole_status = PV(pvs.loc['dipole_status']['pv'])
    print(dipole_status.get())
    if int(dipole_status.get()) != 1:
        raise_exception("HEBT二极铁电源故障，请检查！")
    return "HEBT二极铁正常"


def drop_T0D1_current():
    dipole_set_pv = PV(pvs.loc['dipole_put']['pv'])
    dipole_get_pv = PV(pvs.loc['dipole_get']['pv'])

    dipole_original = dipole_get_pv.get()
    dipole_set_pv.put(0)
    time.sleep(3)

    if abs(dipole_get_pv.get() - dipole_original) < 5:
        raise_exception("T0_D01电流无法退零，请检查电源状态！")
    
    raise_exception("请手动切换至加速器模式") 
    
def switchAC():
    repeat = PV(pvs.loc['timing_freq']['pv'])
    width = PV(pvs.loc['timing_chopper']['pv'])
    if repeat.get() != 1 or width.get() != 20:
        raise_exception("宏脉冲时间结构有误，请检查！") 
    trigger = PV(pvs.loc['timing_trigger']['pv'])
    trigger.put(0)
    return "转入定时触发"

def mps_bypass():
    bypasses = ['mfc_bypass', 'T2_FC_bypass', 'hebt_ring_bypass', 
                'SS_VS_bypass', 'SS_FC_bypass']
    for b in bypasses:
        PV(pvs.loc[b]['pv']).put(1)
    
    #raise_exception("请手动转入终端模式！")

def dipole_checking():
    dipole = PV(pvs.loc['dipole_get']['pv'])
    if dipole.get() > 0.1:
        raise_exception("T0_D01电流回读值未变零，请检查！")
    return "HEBT二极铁电流为零"

def lebt_collimator_setting():
    collimators = ['cm1', 'cm2', 'cm3']
    r = redis.Redis(host='127.0.0.1', port=6379)

    for cm in collimators:
        cm_rb = PV(pvs.loc[f'{cm}_set']['pv']).get()
        r.set(cm, str(cm_rb))
        cm_set_pv = PV(pvs.loc[f'{cm}_set']['pv'])
        cm_set_pv.put(120)
        cm_act_pv = PV(pvs.loc[f'{cm}_action']['pv'])
        cm_act_pv.put(1)

    time.sleep(10)

    for cm in collimators:
        cm_get_pv = PV(pvs.loc[f'{cm}_get']['pv'])
        
        if abs(cm_get_pv.get() - 120) > 0.1:
            raise_exception("LEBT光阑设定有误，请检查！")
    return "LEBT光阑已设定"

#def close_lfc():
#    moving_unit('LEBT_FC_in', 'LFC_driver', 'LFC', 'close')
 #   return 'LFC关闭'

#def open_lfc():
 #   moving_unit('LEBT_FC_out', 'LFC_driver', 'LFC', 'open')
#
def open_mfc():
    moving_unit('mfc_get', 'mfc_out_set', 'close', 'MFC无法拔出，请手动操作！')  #"close" for open



