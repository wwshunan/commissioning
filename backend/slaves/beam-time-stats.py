from nameko.rpc import rpc
from nameko_redis import Redis
from epics import PV
import uuid
from datetime import datetime
import time

FC1 = 'LEBT_BD:FC_01:In'
class UsageTimeService:
    name = 'usage_time_service'
    redis = Redis('development')

    @rpc
    def accumulate_time(self, time_break_id):
        today_beam_time = 0
        timing_allow = False
        self.redis.set('finished', 'false')
        while True:
            FC1_val = PV(FC1).get()
            if FC1_val == 0 and not timing_allow:
                start_time = datetime.now().timestamp()
                timing_allow = True
            elif FC1_val == 1 and timing_allow:
                current_time = datetime.now().timestamp()
                today_beam_time += current_time - start_time
                timing_allow = False
            time_break = self.redis.get(time_break_id)
            if time_break == 'true':
                if FC1_val == 0:
                    current_time = datetime.now().timestamp()
                    today_beam_time += current_time - start_time
                    print(today_beam_time)
                self.redis.set('usage_time', today_beam_time)
                self.redis.set('finished', 'true')
                break
            time.sleep(1)

    @rpc
    def start(self):
        time_break_id = uuid.uuid4().hex
        self.redis.set(time_break_id, 'false')
        return time_break_id

    @rpc
    def stop(self, time_break_id):
        self.redis.set(time_break_id, 'true')
        while self.redis.get('finished') == 'false':
            time.sleep(0.1)
        usage_time = self.redis.get('usage_time')
        return str(usage_time)
