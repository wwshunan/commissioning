from epics import PV, caget
from datetime import datetime
from . import celery
from .factory import redis_client, db
from .models import Timing
import time
import json

monitor_pvs = {
    'FC1': 'LEBT_BD:FC_01:In',
    'chopper': 'LEBT_PS:CHP_01:VMon',
    'hv': 'LIPS_PS:HV_01:VMon',
    'trig': 'EVG1.TRIGSRC',
    'ACCT1': 'ADS:ACCT1',
    'ACCT2': 'ADS:ACCT2',
    'ACCT3': 'ADS:ACCT3',
    'ACCT4': 'ADS:ACCT4',
    'duty_factor': 'MPS_Soft:DUTYFACTOR',
}

current_labels = ['ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']

@celery.task
def period_saving(interrupt_id, time_break_id):
    monitor_instance = {}
    timing_dict = {}
    list_easy_lost = ['duty_factor', 'ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']
    for k in monitor_pvs:
        if k not in list_easy_lost:
            monitor_instance[k] = PV(monitor_pvs[k])

    while True:
        monitor_values = {}
        for k in monitor_instance:
            monitor_values[k] = monitor_instance[k].get()

        try:
            for k in list_easy_lost:
                monitor_values[k] = caget(monitor_pvs[k])
            duty_factor = monitor_values['duty_factor']
        except Exception:
            print('disconnect')

        if duty_factor and duty_factor > 1e-5:
            duty_factor = str(duty_factor)
        if duty_factor not in timing_dict:
            timing_dict[duty_factor] = new_duty_factor_timing()



def save_timing(timing_data):
    for dutyfactor in timing_data:
        for acct in ['ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']:
            if timing_data[dutyfactor]['count'] == 0:
                timing_data[dutyfactor][acct] = 0
            else:
                timing_data[dutyfactor][acct] /= timing_data[dutyfactor]['count']

        timing_item = Timing(
            dutyfactor=dutyfactor,
            times=timing_data[dutyfactor]['beam_time'],
            acct1=timing_data[dutyfactor]['ACCT1'],
            acct2=timing_data[dutyfactor]['ACCT2'],
            acct3=timing_data[dutyfactor]['ACCT3'],
            acct4=timing_data[dutyfactor]['ACCT4'],
        )
        db.session.add(timing_item)
    db.session.commit()


def new_duty_factor_timing():
    timing = {}
    timing['count'] = 0  # ACCT统计次数
    timing['beam_time'] = 0
    for acct in current_labels:
        timing[acct] = 0
    return timing


def timing_and_reset(duty_factor,
                     current_time,
                     timing_dict):
    time_diff = current_time.timestamp() - timing_dict[duty_factor]['start_time']
    timing_dict[duty_factor]['beam_time'] += time_diff
    timing_dict[duty_factor].pop('start_time')
    timing_allow = False
    return timing_allow


def trigger_and_timing(current_time,
                       monitor_values,
                       prev_duty_factor,
                       duty_factor,
                       timing_allow,
                       timing_dict):
    if not timing_allow:
        timing_allow = True
    if 'start_time' not in timing_dict[duty_factor]:
        timing_dict[duty_factor]['start_time'] = datetime.now().timestamp()
    # 当占空比改变时，累计先前占空比的时间
    if duty_factor != prev_duty_factor and prev_duty_factor in timing_dict:
        timing_dict[prev_duty_factor]['beam_time'] += \
            current_time.timestamp() - timing_dict[prev_duty_factor]['start_time']
        timing_dict[prev_duty_factor].pop('start_time')

    # 累计ACCT流强和次数，用于平均
    for acct in current_labels:
        timing_dict[duty_factor][acct] += monitor_values[acct]
    timing_dict[duty_factor]['count'] += 1
    return timing_allow


def timing_add_needed(current_time,
                      prev_time,
                      interrupt_id,
                      monitor_values,
                      has_current,
                      duty_factor,
                      timing_dict):
    time_diff = current_time.timestamp() - prev_time
    period_condition1 = current_time.strftime('%H:%M') == '20:30'
    period_condition2 = current_time.strftime('%H:%M') == '08:30'
    interrupted = redis_client.get(interrupt_id)
    if ((period_condition1 or period_condition2) and time_diff > 60) \
            or (interrupted == b'true'):
        # 早晚八点或人为需要计时
        if monitor_values['FC1'] == 0 and has_current:
            timing_dict[duty_factor]['beam_time'] += \
                current_time.timestamp() - timing_dict[duty_factor]['start_time']
            timing_dict[duty_factor].pop('start_time')
        # 早晚八点
        if interrupted != b'true':
            save_timing(timing_dict)
            # self.timing_dict[duty_factor] = self.new_duty_factor_timing()
            # for d_factor in self.timing_dict:
            #    if d_factor != duty_factor:
            #        self.timing_dict.pop(d_factor)
            timing_dict = {}
            prev_time = current_time.timestamp()
        # 人为统计
        else:
            redis_client.set('usage_time', json.dumps(timing_dict))
            redis_client.set(interrupt_id, 'false')
    return prev_time, timing_dict


@celery.task
def accumulate_time(interrupt_id, time_break_id):
    timing_allow = False
    bpm_sum_lb = 1e4
    monitor_instance = {}
    timing_dict = {}
    list_easy_lost = ['duty_factor', 'ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']
    for k in monitor_pvs:
        if k not in list_easy_lost:
            monitor_instance[k] = PV(monitor_pvs[k])

    # prev_duty_factor = str(monitor_instance['duty_factor'].get())
    prev_duty_factor = str(caget(monitor_pvs['duty_factor']))
    prev_time = datetime.now().timestamp()
    while True:
        monitor_values = {}
        for k in monitor_instance:
            monitor_values[k] = monitor_instance[k].get()

        # duty_factor = str(monitor_values['duty_factor'])
        try:
            for k in list_easy_lost:
                monitor_values[k] = caget(monitor_pvs[k])
            duty_factor = monitor_values['duty_factor']
        except Exception:
            print('disconnect')

        if duty_factor and duty_factor > 1e-5:
            duty_factor = str(duty_factor)
        if duty_factor not in timing_dict:
            timing_dict[duty_factor] = new_duty_factor_timing()
        try:
            has_current = all([monitor_values['hv'] > 19, monitor_values['chopper'] > 3800,
                               monitor_values['FC1'] == 0, monitor_values['trig'] == 0])
        except TypeError:
            print('PV disconnected!')

        current_time = datetime.now()
        # 打开束流开始进行不同占空比下的时间统计
        if monitor_values['FC1'] == 0 and has_current:
            timing_allow = trigger_and_timing(current_time, monitor_values,
                                              prev_duty_factor, duty_factor,
                                              timing_allow, timing_dict)
        # if not timing_allow:
        #    timing_allow = True
        # if 'start_time' not in timing_dict[duty_factor]:
        #    timing_dict[duty_factor]['start_time'] = datetime.now().timestamp()
        ##当占空比改变时，累计先前占空比的时间
        # if duty_factor != prev_duty_factor and prev_duty_factor in timing_dict:
        #    timing_dict[prev_duty_factor]['beam_time'] += \
        #        current_time.timestamp() - timing_dict[prev_duty_factor]['start_time']
        #    timing_dict[prev_duty_factor].pop('start_time')

        ##累计ACCT流强和次数，用于平均
        # for acct in current_labels:
        #    timing_dict[duty_factor][acct] += monitor_values[acct]
        # timing_dict[duty_factor]['count'] += 1
        elif monitor_values['FC1'] == 1 and timing_allow:
            # 关闭束流时，累计当前占空比的时间
            timing_allow = timing_and_reset(duty_factor, current_time, timing_dict)
        prev_time, timing_dict = timing_add_needed(current_time, prev_time,
                                                   interrupt_id, monitor_values,
                                                   has_current, duty_factor,
                                                   timing_dict)

        # 停止计时
        time_break = redis_client.get(time_break_id)
        if time_break == b'true':
            break

        prev_duty_factor = duty_factor
        time.sleep(1)
