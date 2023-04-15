from epics import PV
import numpy as np
import time


class Opt1d(object):
    def __init__(self, x_setting: list, x_reading: list, target_name: list, x_limit: float,
                 x_step_max: float, read_num: int, epsilon: float, learning_rate: float) -> None:
        self.x_limit = x_limit
        self.x_step_max = x_step_max
        self.x_setting = [PV(x) for x in x_setting] 
        self.x_reading = [PV(x) for x in x_reading]
        self.target = [PV(x) for x in target_name] 
        self.read_num = read_num
        self.target_original = self.get_target_val(0.1)
        self.learning_rate = learning_rate
        self.epsilon = epsilon

    def get_target_val(self, interval):
        target_vals = []
        for i in range(self.read_num):
            if len(self.target) == 1:
                target_val = self.target[0].get()
            else:
                target_val = self.target[0].get() - sum([v.get() for v in self.target[1:]])
            target_vals.append(target_val)
            time.sleep(interval)
        return np.median(target_vals)

    def optimize(self, delta: float, target: str, epoches: int, direction: str = 'homo'):
        epoch = 0
        x_current = [x.get() for x in self.x_setting]
        if x_current[0] + delta > self.x_limit:
            delta = -delta

        grad = 10000
        while abs(grad) > self.epsilon and epoch < epoches:
            if epoch <= 5:
                x_step_max = self.x_step_max
            elif epoch <= 10:
                x_step_max = self.x_step_max / 3
            elif epoch <= 15:
                x_step_max = self.x_step_max / 10
            else:
                x_step_max = self.x_step_max / 30


            grad, delta = self.update(
                x_current, delta, x_step_max, target, direction)
            epoch += 1
        return self.target_original

    def update(self, x_current, delta, x_step_max, target, direction):
        #x_current = round(x_current+delta, 1)
        if abs(x_current[0]+delta) > self.x_limit:
            delta = np.sign(x_current[0]) * self.x_limit - x_current[0]
        x_current[0] = round(x_current[0] + delta, 1)

        if len(x_current) == 2 and direction == 'homo':
            x_current[1] = round(x_current[1] + delta, 1)

        if len(x_current) == 2 and direction == 'hetero':
            x_current[1] = round(x_current[1] - delta, 1)

        [x_setting.put(x) for x_setting, x in zip(self.x_setting, x_current)]

        for i, x_reading in enumerate(self.x_reading):
            while abs(x_reading.get() - x_current[i]) > 1:
                time.sleep(1)

        target_current = self.get_target_val(0.1)
        var = abs(target_current) - abs(self.target_original)
        grad = var / delta
        print(var, delta, grad)
        if target == 'min':
            delta = np.clip(-self.learning_rate *
                            grad, -x_step_max, x_step_max)
        else:
            delta = np.clip(self.learning_rate * grad, -x_step_max, x_step_max)

        self.target_original = target_current
        print('delta', delta)
        return grad, delta
