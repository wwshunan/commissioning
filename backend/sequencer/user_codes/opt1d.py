from epics import PV
from scipy.optimize import brent
import numpy as np
import time


class Opt1d(object):
    def __init__(self, x_setting: list, x_reading: list, target_name: list, x_limit: float,
                 x_step_max: float, read_num: int, xtol: float) -> None:
        self.x_limit = x_limit
        self.x_step_max = x_step_max
        self.x_setting = [PV(x) for x in x_setting] 
        self.x_reading = [PV(x) for x in x_reading]
        self.target = [PV(x) for x in target_name] 
        self.read_num = read_num
        self.xtol = xtol
        self.prev_dx = np.inf
        self.x_setting_original = [x.get() for x in self.x_setting]

    def get_target_val(self, interval):
        #bpm_xs = []
        target_vals = []
        for i in range(self.read_num):
            if len(self.target) == 1:
                target_val = self.target[0].get()
            else:
                #weights = np.array([6, 18, 18, 18, 18, 18]) / 16
                weights = np.array([0.1815, 0.4956, 0.5658, 0.3773, 0.2345, 0.0]) 
                target_val = self.target[0].get() * 0.2579 - np.array([v.get() for v in self.target[1:]])*weights
            target_vals.append(target_val)
            time.sleep(interval)
        return np.median(target_vals)

    def check_current_load(self, rb_pv, target):
        if abs(rb_pv.get() - target) > self.xtol * 1.2:
            return False
        return True

    def target_func(self, dx, direction, target):
        print(dx, 'dx')
         
        if abs(dx-self.prev_dx) < self.xtol:
            raise StopIteration
        self.prev_dx = dx
        large_val = 1e5 
        if len(self.x_setting) == 1:
            x_val = self.x_setting_original[0] + dx
            if abs(x_val) < self.x_limit:
                self.x_setting[0].put(round(x_val, 2))
                while not self.check_current_load(self.x_reading[0], x_val):
                    time.sleep(1)
            else:
                return large_val
        else:
            for i, (x_set_pv, x_rb_pv, x_original) in enumerate(zip(self.x_setting, self.x_reading, self.x_setting_original)):
                if direction == 'homo':
                    x_val = x_original + dx
                else:
                    x_val = x_original + (-1)**i * dx
                if abs(x_val) < self.x_limit:
                    x_set_pv.put(round(x_val, 2))
                    while not self.check_current_load(x_rb_pv, x_val):
                        time.sleep(1)
                else:
                    return large_val

        target_val = self.get_target_val(0.1)
        return abs(target_val) if target == 'min' else -target_val

    def optimize(self, target: str, direction: str = 'homo'):
        try:
            brent(self.target_func, args=(direction, target), brack=(0.5, self.x_step_max), maxiter=10)
        except StopIteration:
            pass

def check_pv_setting(get_pvs, targets, tol):
    for rb, t in zip(get_pvs, targets):
        if abs(rb.get() - t) > tol:
            return False
    return True

def t2fc_target_func(x, put_pvs, action_pvs, get_pvs, target_pv, target):
    set_vals = []
    for i, (s, act) in enumerate(zip(put_pvs, action_pvs)):
        if i == 1:
            set_val = x - 5
        else:
            set_val = x
        set_vals.append(set_val)
        s.put(round(set_val, 1))
        act.put(1)

    while True:
        if check_pv_setting(get_pvs, set_vals, 0.1):
            break
        time.sleep(1)
    
    targets = []
    for _ in range(50):
        t = target_pv.get()
        time.sleep(0.1)
        targets.append(t)
    return (np.median(targets) - target) ** 2

    
