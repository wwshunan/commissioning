from epics import PV

class PhaseScanPVController(object):
    def __init__(self):
        #self.pvs = {}
        self.ready = PV('NCSC_RF:LLRF_All:CavRFRdy')
        #self.lattice = PV('CA_RF:LLRF_ALL:Lattice')
        self.calibrated_epk = PV('CA_RF:LLRF_ALL:Calibrated_epk')
        self.finished = PV('CA_RF:LLRF_ALL:Finish')
        self.amps = {}
        self.phases = {}
        self.cavity_bypass = {}
        self.pvs_one_cavity = {}
        self.mode = PV('CAFe2:CTL_01:Mode')
        self.current = PV('Bpm:2-S')
        self.bpm_sum_limit = 0.0
        self.orbit_offset_limit = 0.0

    def set_bpm_sum_and_offset_limit(self, sum_limit: float, offset_limit: float):
        print(sum_limit, offset_limit)
        self.bpm_sum_limit = sum_limit
        self.orbit_offset_limit = offset_limit

    def get_ready_factory(self, which):
        if which == 'orbit':
            return self.get_orbit_ready() 
        elif which == 'cavity':
            return self.get_cavity_ready()
        else:
            return self.get_current_ready()

    def get_orbit_ready(self) -> bool:
        if {'x', 'y'} <= set(self.pvs_one_cavity.keys()):
            return all([self.pvs_one_cavity['x'].get() < self.orbit_offset_limit, 
                        self.pvs_one_cavity['y'].get() < self.orbit_offset_limit])

    def get_cavity_ready(self) -> bool:
        return self.ready.get()

    def get_current_ready(self) -> bool:
        return self.current.get() > self.bpm_sum_limit
        #if 'current_ready' in list(self.pvs_one_cavity.keys()):
        #    return self.pvs_one_cavity['current_ready'].get() > 4e3

    def set_cavity_amp(self, cavity_name: str, amp: float):
        self.amps[cavity_name].put(amp)

    def set_cavity_phase(self, cavity_name: str, phase: float):
        self.phases[cavity_name].put(phase)

    def get_cavity_amp_limit(self):
        return self.pvs_one_cavity['amp_limit_pv'].get()

    def set_cavity_bypass(self, cavity_name: str, val: int):
        self.cavity_bypass[cavity_name].put(val)
    #def get_ready(self):
    #    ready = all(self.pvs["ready_pv"][pv_name].get()
    #               for pv_name in self.pvs["ready_pv"])
    #    return ready


    #def register_pvs(self, pvs):
    #    for kind in pvs:
    #        self.pvs[kind] = {}
    #        for pv_name in pvs[kind]:
    #            self.pvs[kind][pv_name] = PV(pv_name)

    #def get(self, kind, pv_name):
    #    return self.pvs[kind][pv_name].get()


    #def put(self, kind, pv_name, value):
    #    self.pvs[kind][pv_name].put(value)

