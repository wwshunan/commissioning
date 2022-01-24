from .fit_service import SingleBPMFit, DoubleBPMFit
import numpy as np

class PhaseFit(object):
    def __init__(self, payload):
        self.payload = payload
        self.payload['bpm_phases'] = np.array(self.payload['bpm_phases'])

    def fit(self):
        if self.payload['bpm_model'] == 'double':
            fit_obj = DoubleBPMFit(**self.payload)
            rf_phase, w_in, w_gain, amp, e, x_plot, y_plot = fit_obj.bpm_fit()
        else:
            fit_obj = SingleBPMFit(**self.payload)
            rf_phase, w_gain, amp, e, x_plot, y_plot = fit_obj.bpm_fit()
            w_in = self.payload['Win']
        self.clear_up(rf_phase, w_in, w_gain, amp, x_plot, y_plot)
        w_out = w_in + w_gain
        return dict(rf_phase=rf_phase, w_gain=w_gain, w_out=w_out, amp=abs(amp),
                    x_plot=x_plot, y_plot=y_plot.tolist())

    def clear_up(self, rf_phase, w_in, w_gain, amp, x_plot, y_plot):
        pass