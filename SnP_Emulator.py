import threading
from serial import Serial
class SnPState():
    def __init__(self, hard_sip_threshold, soft_sip_threshold, soft_puff_threshold, hard_puff_threshold): # , sip_ramp_up, sip_ramp_down, puff_ramp_up, puff_ramp_down, deadband):
        # super().__init__(daemon=True)
        self.thresholds = {'hard_sip': hard_sip_threshold,
                            'soft_sip': soft_sip_threshold,
                            'soft_puff': soft_puff_threshold,
                            'hard_puff': hard_puff_threshold}
        self._state = ''
        # self.setup()
    
    # def _threshold_test(self, state):
    #     print("Starting {} measurements".format(state))
    #     pressures = []
    #     for i in range(5):
    #         input("Press Enter to take measurement {}".format(i + 1))
    #         if not data_queue.empty():
    #             pressure = data_queue.get_nowait()
    #         pressures.append(pressure)
    #     min_pressure = min(pressures)
    #     deadband = min_pressure - 5
    #     threshold = max(pressures) + 5
    #     print(state, pressures, "deadband = ", deadband, " threshold = ", threshold)
        


    # def setup(self):
    #     # 1. User identifier/profile load (assume new user)
    #     if input("Setup a new user profile?") is 'n':
    #         print("Load profile")
    #     # 2. SnP thresholds
    #     for state in self._thresholds.keys():
    #         self._threshold_test(state)
        # threshold_test()
    #     self._serial_port = Serial('dev/ttyACM0', 9600, timeout=None)

    # def run(self):
    #     connected = False
    #     while not connected:
    #         s = [0]
    #         read_serial = self._serial_port.readline()
    #         try:
    #             s[0] = int(read_serial)
    #             while 

    def setState(self, pressure):
        if pressure > 120 and pressure < 140:
            if self._state == '':
                self._state = 'hard_puff'
            return
        if pressure > self._thresholds['hard_puff']:
            self._state = 'hard_puff'
        elif pressure > self._thresholds['soft_puff']:
            self._state = 'soft_puff'
        elif pressure > self._thresholds['soft_sip']:
            self._state = 'soft_sip'
        elif pressure < self._thresholds['hard_sip']:
            self._state = 'hard_sip'
        print(self._state, pressure)

    def getState(self):
        return self._state
