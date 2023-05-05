from epics import PV
from ..exceptions import raise_exception
from .opt1d import Opt1d, check_pv_setting, t2fc_target_func
from scipy.constants import c
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar
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

    status_pv = PV(unit_status['pv'])
    print('1')
    if status_pv.get(timeout=3) != settings[target]['val']:
        print('2')
        driver_pvname = pvs.loc[driver]['pv']
        PV(driver_pvname).put(settings[target]['val'])

    print('3')
    epoch = 0
    while epoch < 15:
        if 't2_fc' in status:
            print('4')
            if status_pv.get() < -99:
                break
        else:
            print(status)
            print(settings)
            if status_pv.get(timeout=3) == settings[target]['val']:
                print('5')
                break
        time.sleep(1)
        epoch += 1
    else:
        raise_exception(msg)

    #if 't2_fc' in status:
    #    if PV(unit_status['pv']).get() > -99:
    #        raise_exception(msg)
    #else:
    #    if PV(unit_status['pv']).get(timeout=3) != settings[target]['val']:
    #        raise_exception(msg)


def close_lebt_dump():
    moving_unit('LEBT_dump_in', 'Ldump_driver',
                'close', 'LEBT_DUMP无法插入，请手动操作！')
    raise_exception("请手动转换加速器模式")


def close_lebt_dump_target():
    moving_unit('LEBT_dump_in', 'Ldump_driver',
                'close', 'LEBT_DUMP无法插入，请手动操作！')


def close_lebt_dump_hebt():
    moving_unit('LEBT_dump_in', 'Ldump_driver',
                'close', 'LEBT_DUMP无法插入，请手动操作！')


def open_lebt_dump_hebt():
    repeat = PV(pvs.loc['timing_freq']['pv'])
    width = PV(pvs.loc['timing_chopper']['pv'])
    if (repeat.get() * width.get()) > 200:
        raise_exception(
            "Duty factor is too high, LEBT DUMP is NOT allowed to be pulled out！")
    if PV(pvs.loc['mps_status']['pv']).get() != 0:
        raise_exception("束流总运行状态不具备LEBT_DUMP拔出条件，请检查！")
    moving_unit('LEBT_dump_in', 'Ldump_driver', 'open', 'LEBT_DUMP无法拔出，请手动操作！')
    raise_exception("请手动测能量！")


def open_lebt_dump():
    repeat = PV(pvs.loc['timing_freq']['pv'])
    width = PV(pvs.loc['timing_chopper']['pv'])
    if (repeat.get() * width.get()) > 200:
        raise_exception(
            "Duty factor is too high, LEBT DUMP is NOT allowed to be pulled out！")
    if PV(pvs.loc['mps_status']['pv']).get() != 0:
        raise_exception("束流总运行状态不具备LEBT_DUMP拔出条件，请检查！")
    moving_unit('LEBT_dump_in', 'Ldump_driver', 'open', 'LEBT_DUMP无法拔出，请手动操作！')


def move_fcs():
    elements_to_insert = ['ss_fc', 't2_fc', 'mfc']
    get_pvs = []
    for el in elements_to_insert:
        put_pv = PV(pvs.loc[el+'_in_set']['pv'])
        put_pv.put(1)
        get_pv = PV(pvs.loc[el+'_get']['pv'])
        get_pvs.append(get_pv)

    PV(pvs.loc["t2_hr_set"]["pv"]).put(0)

    epoch = 0
    while epoch < 15 and any(pv.get() > 0.5 for pv in get_pvs):
        time.sleep(1)
        epoch += 1

    for i, el in enumerate(elements_to_insert):
        if get_pvs[i].get() > 0.5:
            raise_exception(f"{el}无法插入，请手动操作")

def diag_sampling_setting(who: str):
    window_width = PV(pvs.loc[f"{who}_window_width"]['pv'])
    start = PV(pvs.loc[f"{who}_start"]['pv'])
    width = PV(pvs.loc[f"{who}_width"]['pv'])
    noise_start = PV(pvs.loc[f"{who}_noise_start"]['pv'])
    noise_width = PV(pvs.loc[f"{who}_noise_width"]['pv'])
    window_width.put(0)  # 0 for 80us
    start.put(250)
    width.put(200)
    noise_start.put(900)
    noise_width.put(200)
    action = PV(pvs.loc[f"{who}_action"]["pv"])
    action.put(1)


def bpm_sampling_setting(who: str, start_val: int, stop_val: int):
    window_width = PV(pvs.loc[f"{who}_window_width"]['pv'])
    start = PV(pvs.loc[f"{who}_start"]['pv'])
    width = PV(pvs.loc[f"{who}_width"]['pv'])
    window_width.put(0)  # 0 for 1ms
    start.put(start_val)
    width.put(stop_val)


def diag_gain_setting_target():
    gains = ['t2hr', 'sshr1', 'sshr2', 'sshr3', 'sshr4', 'sshr5']
    for g in gains:
        if g == 't2hr':
            PV(pvs.loc[f"{g}_gain"]["pv"]).put(2)  # 对应1e5
        else:
            PV(pvs.loc[f"{g}_gain"]["pv"]).put(3)  # 对应1e6


def diag_gain_setting():
    gains = ['mfc', 't2hr', 't2fc', 'ssfc',
             'sshr1', 'sshr2', 'sshr3', 'sshr4', 'sshr5']
    for g in gains:
        PV(pvs.loc[f"{g}_gain"]["pv"]).put(1)  # 对应1e4

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
    moving_unit('t2_fc_get', 't2_fc_out_set', 'close',
                'T2FC无法拔出，请手动操作！')  # "close " for open

def close_t2fc():
    put_pv = PV(pvs.loc['t2_fc_in_set']['pv'])
    put_pv.put(1)

    get_pv = PV(pvs.loc['t2_fc_get']['pv'])

    epoch = 0
    while epoch < 15:
        if get_pv.get() > -1:
            break
        time.sleep(1)
        epoch += 1
    else:
        raise_exception("T2 FC无法插入，请手动操作")

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

    # raise_exception("设定无误，请手动选择BPM衰减，完成后将转为终端模式")


def bpm_gain_setting_opt():
    #gains = ['t2hr','ssfc', 'sshr1', 'sshr2', 'sshr3', 'sshr4', 'sshr5']
    gains = ['T2_BPM2', 'T2_BPM3']
    for g in gains:
        PV(pvs.loc[f"{g}_Gain"]["pv"]).put(6)  # 对应0dB

    #signals = ['t2hr', 'sshr']
    signals = ['t2bpm2', 't2bpm3']
    for s in signals:
        bpm_sampling_setting(s, 15, 15)


def bpm_gain_setting_target():
    #gains = ['t2hr','ssfc', 'sshr1', 'sshr2', 'sshr3', 'sshr4', 'sshr5']
    gains = ['T2_BPM2', 'T2_BPM3', 'SS_BPM']
    for g in gains:
        PV(pvs.loc[f"{g}_Gain"]["pv"]).put(6)  # 对应0dB

    #signals = ['t2hr', 'sshr']
    signals = ['ssbpm', 't2bpm2', 't2bpm3']
    for s in signals:
        bpm_sampling_setting(s, 100, 800)


def restore_mps():
    bypasses = ['hebt_ring_bypass', 'mfc_bypass', 'T2_FC_bypass',
                'SS_VS_bypass', 'SS_FC_bypass']
    for b in bypasses:
        PV(pvs.loc[b]['pv']).put(0)


def open_ssfc_t2fc():
    moving_unit('ss_fc_get', 'ss_fc_out_set', 'close',
                'SSFC无法拔出，请手动操作！')  # "close" for open
    open_t2fc()
    raise_exception("请手动转入终端模式！")


def dipole_status_checking():
    dipole_status = PV(pvs.loc['T0_D01_status']['pv'])
    print(dipole_status.get())
    if int(dipole_status.get()) != 1:
        raise_exception("HEBT二极铁电源故障，请检查！")
    return "HEBT二极铁正常"


def load_T0D1_current(charge: int, nucleons: int, energy: float):
    energy = float(energy)
    static_energy_unit = 931.4941024
    if nucleons == 40:
        ns = 39.9623831
    elif nucleons == 54:
        ns = 53.9388805

    static_energy = ns * static_energy_unit - charge * 0.511
    total_energy = energy + static_energy
    gamma = total_energy / static_energy
    beta = (1 - gamma**-2)**0.5
    rigidity = total_energy * beta / c * 1e6 / charge

    t0d1_xs = [-533.292, -563.877, -592.907, -620.597, -
               647.099, -508.757, -541.009, -571.467, -600.4, -627.988]
    t0d1_ys = [-557.5, -599.9, -643.5, -689.9, -
               743.8, -525.5, -568.0, -611.1, -655.5, -703.6]
    t2q1_xs = [202.095, 213.284, 224.563, 235.117, 245.232,
               192.954, 204.983, 217.071, 227.703, 237.606]
    t2q1_ys = [202.1, 213.3, 224.6, 235.2,
               245.3, 192.9, 205.0, 217.1, 227.8, 237.7]
    t2d1_xs = [524.742, 554.852, 583.454, 610.695, 636.779,
               500.533, 532.296, 562.295, 590.784, 617.947]
    t2d1_ys = [548.6, 592.6, 637.1, 682.5,
               729.7, 515.7, 559.3, 603.9, 649.2, 695.1]

    transform_coeffs = [-538.757, 204.1564, 530.1255]
    interp_data = [(t0d1_xs, t0d1_ys), (t2q1_xs, t2q1_ys), (t2d1_xs, t2d1_ys)]
    magnets = ['T0_D01', 'T2_Q1', 'T2_D1']
    current_set = []
    magnet_get_pvs = []
    for coeff, (x, y), m in zip(transform_coeffs, interp_data, magnets):

        current = coeff * rigidity
        f = interp1d(x, y)
        print(energy)
        current = f(current).item()
        print(energy, current)
        current_set.append(current)
        print(energy, current, 2)
        PV(pvs.loc[f"{m}_set", "pv"]).put(round(current, 2))
        print(energy, 0000)
        magnet_get_pvs.append(PV(pvs.loc[f"{m}_get", "pv"]))

    epoch = 0
    while epoch < 120:
        print('1')
        if check_pv_setting(magnet_get_pvs, current_set, 2):
            break
        epoch += 1
        time.sleep(1)

    for label, m, t in zip(magnets, magnet_get_pvs, current_set):
        if abs(m.get() - t) > 2:
            raise_exception(f"{label}电流无法加载，请检查电源状态！")


def drop_T0D1_current():
    dipole_set_pv = PV(pvs.loc['T0_D01_set']['pv'])
    dipole_get_pv = PV(pvs.loc['T0_D01_get']['pv'])

    dipole_original = dipole_get_pv.get()
    dipole_set_pv.put(0)
    time.sleep(3)

    if abs(dipole_get_pv.get() - dipole_original) < 5:
        raise_exception("T0_D01电流无法退零，请检查电源状态！")


def switch_safe_mode():
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


def dipole_checking():
    dipole = PV(pvs.loc['T0_D01_get']['pv'])

    count = 0
    while abs(dipole.get()) > 0.1 and count < 45:
        time.sleep(2)
        count += 1

    if abs(dipole.get()) > 0.1:
        raise_exception("T0_D01电流回读值未变零，请检查！")
    return "HEBT二极铁电流为零"


def lebt_collimator_setting():
    collimators = ['cm1', 'cm2', 'cm3']
    r = redis.Redis(host='127.0.0.1', port=6379)

    get_pvs = []
    set_vals = [120] * 3
    for cm in collimators:
        cm_rb = PV(pvs.loc[f'{cm}_set']['pv']).get()
        r.set(cm, str(cm_rb))
        cm_set_pv = PV(pvs.loc[f'{cm}_set']['pv'])
        cm_set_pv.put(120)
        cm_act_pv = PV(pvs.loc[f'{cm}_action']['pv'])
        cm_act_pv.put(1)
        cm_get_pv = PV(pvs.loc[f'{cm}_get']['pv'])
        get_pvs.append(cm_get_pv)

    epoch = 0
    while epoch < 10:
        if check_pv_setting(get_pvs, set_vals, 0.1):
            break
        time.sleep(1)
        epoch += 1
    else:
        raise_exception("LEBT光阑设定有误，请检查！")

    return "LEBT光阑已设定"

# def close_lfc():
#    moving_unit('LEBT_FC_in', 'LFC_driver', 'LFC', 'close')
 #   return 'LFC关闭'

# def open_lfc():
 #   moving_unit('LEBT_FC_out', 'LFC_driver', 'LFC', 'open')
#


def open_mfc():
    moving_unit('mfc_get', 'mfc_out_set', 'close',
                'MFC无法拔出，请手动操作！')  # "close" for open


def set_beam_current(current: float):
    current = float(current)
    close_t2fc()

    collimators = ['cm1', 'cm2', 'cm3']

    target_pv = PV(pvs.loc["T2FC", "pv"])

    put_pvs = []
    action_pvs = []
    get_pvs = []
    for cm in collimators:
        cm_set_pv = PV(pvs.loc[f'{cm}_set', 'pv'])
        put_pvs.append(cm_set_pv)
        cm_act_pv = PV(pvs.loc[f'{cm}_action', 'pv'])
        action_pvs.append(cm_act_pv)
        cm_get_pv = PV(pvs.loc[f"{cm}_get", "pv"])
        get_pvs.append(cm_get_pv)

    result = minimize_scalar(t2fc_target_func, bounds=(15, 120), method='bounded', args=(
        put_pvs, action_pvs, get_pvs, target_pv, current), options={ "maxiter": 10})
    currents = []
    for _ in range(100):
        currents.append(target_pv.get())
        time.sleep(0.1)
    
    if abs(np.median(currents) - current) > 2:
        raise_exception("T2 FC流强未限制到目标值.")

def hebt_orbit_correction():
    corr_bpms = [
        {
            'x': 'T0_CH1',
            'target': 'T2_BPM2_x',
        },
        {
            'x': 'T0_CV1',
            'target': 'T2_BPM2_y',
        },
        {
            'x': 'T2_CH3',
            'target': 'T2_BPM3_x',
        },
        {
            'x': 'T2_CV3',
            'target': 'T2_BPM3_y',
        }
    ]

    for corr in corr_bpms:
        print(corr['x'])
        x_setting = pvs.loc[f"{corr['x']}_set", "pv"]
        x_reading = pvs.loc[f"{corr['x']}_get", "pv"]
        target = pvs.loc[f"{corr['target']}", "pv"]
        print(PV(target).get(), target)
        if abs(PV(target).get()) < 0.1:
            print('hre')
            continue
        correction = Opt1d([x_setting], [x_reading],
                           [target], 180, 20, 10, 0.1)
        target = correction.optimize(target='min')


def hebt_ssfc_opt():
    #qs = ['T0_Q1', 'T0_Q2', 'T2_Q1', 'T2_Q2', 'T2_Q3', 'T2_Q4']
    qs = {
        #'T0_Q2': 370,
        'T2_Q1': 400,
        'T2_Q2': 600,
        'T2_Q3': 600,
        'T2_Q4': 600,
    }

    for q in qs:
        x_setting = pvs.loc[f"{q}_set", "pv"]
        x_reading = pvs.loc[f"{q}_get", "pv"]
        target = pvs.loc["SSFC", "pv"]
        opt = Opt1d([x_setting], [x_reading], [target], qs[q], 15, 50, 0.26)
        opt.optimize(target='max')

    corr_ssfcs = [
        {
            'x': 'T2_CH3',
            'target': 'SSFC',
        },
        {
            'x': 'T2_CV3',
            'target': 'SSFC',
        }
    ]

    for corr in corr_ssfcs:
        x_setting = pvs.loc[f"{corr['x']}_set", "pv"]
        x_reading = pvs.loc[f"{corr['x']}_get", "pv"]
        target = pvs.loc[f"{corr['target']}", "pv"]
        opt = Opt1d([x_setting], [x_reading],
                    [target], 180, 5, 50, 0.1)
        opt.optimize(target='max')

def hebt_hr_opt():
    print('here')
    corr_ssfcs = [
        {
            'x': 'T2_CH3',

            'target': 'SSFC',
        },
        {
            'x': 'T2_CV3',
            'target': 'SSFC',
        }
    ]
    x_setting = [pvs.loc[x, "pv"] for x in ("T2_Q2_set", "T2_Q3_set")]
    print('4')
    x_reading = [pvs.loc[x, "pv"] for x in ("T2_Q2_get", "T2_Q3_get")]
    print('5')
    halo_rings = ['SSFC', 't2_halo', 'halo1', 'halo2', 'halo3', 'halo4', 'halo5']
    halo_rings = [pvs.loc[r, "pv"] for r in halo_rings]
    print('1')
    opt = Opt1d(x_setting, x_reading, halo_rings, 600, 5, 50, 0.26)
    print('2')
    opt.optimize(target='max', direction='hetero')
    print('3')
    opt.optimize(target='max', direction='homo')

    x_setting = [pvs.loc[f'{corr["x"]}_set', 'pv'] for corr in corr_ssfcs]
    x_reading = [pvs.loc[f'{corr["x"]}_get', 'pv'] for corr in corr_ssfcs]
    halo_rings = ['SSFC', 't2_halo', 'halo1', 'halo2', 'halo3', 'halo4', 'halo5']
    halo_rings = [pvs.loc[r, "pv"] for r in halo_rings]
    for i, corr in enumerate(corr_ssfcs):
        opt = Opt1d([x_setting[i]], [x_reading[i]], halo_rings, 70, 2, 50, 0.1)
        opt.optimize(target='max')
