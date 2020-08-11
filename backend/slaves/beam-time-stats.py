from nameko.rpc import rpc
from nameko_redis import Redis
from epics import PV
import uuid
from datetime import datetime
from backend.app import save_timing
import time
import json

monitor_pvs = {
    'FC1': 'LEBT_BD:FC_01:In',
    'ACCT1': 'ADS:ACCT1',
    'ACCT2': 'ADS:ACCT2',
    'ACCT3': 'ADS:ACCT3',
    'ACCT4': 'ADS:ACCT4',
    'duty_factor': 'ADS:DUTYFACTOR',
}

current_labels = ['ACCT1', 'ACCT2', 'ACCT3', 'ACCT4']

class UsageTimeService:
    name = 'usage_time_service'
    redis = Redis('development')

    def __init__(self):
        self.timing_allow = False
        self.current_low_bound = 0.015
        self.monitor_instance = {}
        self.timing_dict = {}
        for k in monitor_pvs:
            self.monitor_instance[k] = PV(monitor_pvs[k])

    @rpc
    def accumulate_time(self, interrupt_id, time_break_id):
        prev_duty_factor = str(self.monitor_instance['duty_factor'].get())
        prev_time = datetime.now().timestamp()
        while True:
            monitor_values = {}
            for k in self.monitor_instance:
                monitor_values[k] = self.monitor_instance[k].get()

            duty_factor = str(monitor_values['duty_factor'])
            if duty_factor is not None and duty_factor not in self.timing_dict:
                self.timing_dict[duty_factor] = self.new_duty_factor_timing()
            try:
                has_current = any(monitor_values[acct] > self.current_low_bound
                                  for acct in current_labels)
            except TypeError:
                print('PV disconnected!')

            current_time = datetime.now()
            # 打开束流开始进行不同占空比下的时间统计
            if monitor_values['FC1'] == 0 and has_current:
                self.trigger_and_timing(current_time, monitor_values,
                                        prev_duty_factor, duty_factor)
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
            elif monitor_values['FC1'] == 1 and self.timing_allow:
                # 关闭束流时，累计当前占空比的时间
                self.timing_and_reset(duty_factor, current_time)
            prev_time = self.timing_add_needed(current_time, prev_time, interrupt_id,
                                               monitor_values, has_current, duty_factor)

            # 停止计时
            time_break = self.redis.get(time_break_id)
            if time_break == 'true':
                break

            prev_duty_factor = duty_factor
            time.sleep(1)

    def new_duty_factor_timing(self):
        timing = {}
        timing['count'] = 0  # ACCT统计次数
        timing['beam_time'] = 0
        for acct in current_labels:
            timing[acct] = 0
        return timing

    def timing_and_reset(self, duty_factor, current_time):
        time_diff = current_time.timestamp() - self.timing_dict[duty_factor]['start_time']
        self.timing_dict[duty_factor]['beam_time'] += time_diff
        self.timing_dict[duty_factor].pop('start_time')
        self.timing_allow = False

    def trigger_and_timing(self, current_time, monitor_values,
                           prev_duty_factor, duty_factor):
        if not self.timing_allow:
            self.timing_allow = True
        if 'start_time' not in self.timing_dict[duty_factor]:
            self.timing_dict[duty_factor]['start_time'] = datetime.now().timestamp()
        # 当占空比改变时，累计先前占空比的时间
        if duty_factor != prev_duty_factor and prev_duty_factor in self.timing_dict:
            self.timing_dict[prev_duty_factor]['beam_time'] += \
                current_time.timestamp() - self.timing_dict[prev_duty_factor]['start_time']
            self.timing_dict[prev_duty_factor].pop('start_time')

        # 累计ACCT流强和次数，用于平均
        for acct in current_labels:
            self.timing_dict[duty_factor][acct] += monitor_values[acct]
        self.timing_dict[duty_factor]['count'] += 1

    def timing_add_needed(self, current_time, prev_time, interrupt_id,
                          monitor_values, has_current, duty_factor):
        time_diff = current_time.timestamp() - prev_time
        period_condition1 = current_time.strftime('%H:%M') == '20:30'
        period_condition2 = current_time.strftime('%H:%M') == '15:55'
        interrupted = self.redis.get(interrupt_id)
        if ((period_condition1 or period_condition2) and time_diff > 60) \
                or (interrupted == 'true'):
            # 早晚八点或人为需要计时
            if monitor_values['FC1'] == 0 and has_current:
                self.timing_dict[duty_factor]['beam_time'] += \
                    current_time.timestamp() - self.timing_dict[duty_factor]['start_time']
                self.timing_dict[duty_factor].pop('start_time')
            print(self.timing_dict)
            # 早晚八点
            if interrupted != 'true':
                save_timing(self.timing_dict)
                #self.timing_dict[duty_factor] = self.new_duty_factor_timing()
                #for d_factor in self.timing_dict:
                #    if d_factor != duty_factor:
                #        self.timing_dict.pop(d_factor)
                self.timing_dict = {}
                prev_time = current_time.timestamp()
            # 人为统计
            else:
                self.redis.set('usage_time', json.dumps(self.timing_dict))
                self.redis.set(interrupt_id, 'false')
        return prev_time

    @rpc
    def start(self):
        interrupt_id = uuid.uuid4().hex
        time_break_id = uuid.uuid4().hex
        self.redis.set(interrupt_id, 'false')
        self.redis.set(time_break_id, 'false')
        self.redis.set('finished', 'false')
        return interrupt_id, time_break_id

    @rpc
    def stop(self, time_break_id):
        self.redis.set(time_break_id, 'true')
        # while self.redis.get('finished') == 'false':
        #    time.sleep(0.1)
        # usage_time = self.redis.get('usage_time')
        return 'Success'

    @rpc
    def interrupt(self, interrupt_id):
        self.redis.set(interrupt_id, 'true')
        while self.redis.get(interrupt_id) == 'true':
            time.sleep(0.1)
        usage_time = self.redis.get('usage_time')
        return usage_time
