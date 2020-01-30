import threading
import time
from serial import Serial
import csv
NUM_SAMPLES = 3

class SnPState(threading.Thread):
    def __init__(self, serial_port):
        super().__init__(daemon=True)
        self._port = serial_port
        self._press_lock = threading.Lock()
        self._curr_pressure = 0
        self._ambient_pressure = 132.0
        self._deadband = 25
        self._sip_threshold = 40
        self._sip_ramp_down = 0.1
        self._sip_ramp_up = 0.1
        self._puff_threshold = 209
        self._puff_ramp_down = 0.4
        self._puff_ramp_up = 0.4
        self._params_set = False
        self._state = 'deadband'
        self._ramp_wait = False
        self._ramp_time = 0.0
    
    def _setState(self, pressure):
        if pressure > self._puff_threshold:
            self._state = 'hard_puff'
            self._ramp_wait = False
        elif pressure < self._sip_threshold:
            self._state = 'hard_sip'
            self._ramp_wait = False
        elif pressure >= self._ambient_pressure + self._deadband:
            if self._ramp_wait == False:
                self._ramp_wait = True
                self._ramp_time = time.time()
            else:
                curr_time = time.time()
                in_state = curr_time - self._ramp_time
                if self._state is 'hard_puff':
                    ramp_threshold = self._puff_ramp_down
                else:
                    ramp_threshold = self._puff_ramp_up
                if in_state > ramp_threshold:
                    self._state = 'soft_puff'
        elif pressure <= self._ambient_pressure - self._deadband:
            if self._ramp_wait == False:
                self._ramp_wait = True
                self._ramp_time = time.time()
            else:
                curr_time = time.time()
                in_state = curr_time - self._ramp_time
                if self._state is 'hard_sip':
                    ramp_threshold = self._sip_ramp_down
                else:
                    ramp_threshold = self._sip_ramp_up
                if in_state > ramp_threshold:
                    self._state = 'soft_sip'
        else:
            self._state = 'deadband'
            self._ramp_wait = False

    def run(self):
        # method run when ::meth::'start()' is called (comes from base class)
        while True:
            s = [0]
            read_serial = self._port.readline()
            try:
                s[0] = int(read_serial)
                self._setPressure(s[0])
                # want this sleep to be less than the period of the serial info (50 ms as of 1/20/20)
                # so that the read actually blocks until there's new data
                time.sleep(0.025)
            except ValueError:
                pass
    def _setPressure(self, pressure):
        with self._press_lock:
            self._curr_pressure = pressure
        if self._params_set:
            self._setState(pressure)
        # print(pressure)
    def getPressure(self):
        with self._press_lock:
            return self._curr_pressure
    
    def getState(self):
        return self._state            

    def setup(self):
        if input("Load user profile? (y/n) ") is 'y':
            self._readCsv()
            self._params_set = True
            return 
        pressures = {'hard_sip': [],
                    'soft_sip': [],
                    'hard_puff': [],
                    'soft_puff': []
                    }
        avg_ambient_pressure = 0
        i = 0
        while i < NUM_SAMPLES:
            pressure = self.getPressure()
            avg_ambient_pressure += pressure
            i = i + 1
            time.sleep(0.1)
        avg_ambient_pressure = avg_ambient_pressure / NUM_SAMPLES
        self._ambient_pressure = avg_ambient_pressure
        # 1. User identifier/profile load (assume new user)
        # if input("Setup a new user profile?") is 'n':
        #     print("Load profile")
        # 2. SnP thresholds
        for state in pressures.keys():
            print("Starting {} measurements".format(state))
            pressures[state] = self._threshold_test()
            # TODO: Put in error checking on pressures 
            #       (e.g. sips cannot be above ambient, pressures within certain range of each other etc)
        min_hard_puff = min(pressures['hard_puff'])
        max_soft_puff = max(pressures['soft_puff'])
        rec_puff_threshold = max_soft_puff + (min_hard_puff - max_soft_puff) / 2
        rec_puff_deadband = min(pressures['soft_puff']) - avg_ambient_pressure
        
        # hard sips are lower pressures than soft sips
        # sips are lower pressure than ambient
        max_hard_sip = max(pressures['hard_sip'])
        min_soft_sip = min(pressures['soft_sip'])
        rec_sip_threshold = min_soft_sip - (min_soft_sip - max_hard_sip) / 2
        rec_sip_deadband = avg_ambient_pressure - max(pressures['soft_sip'])

        rec_deadband_size = min(rec_puff_deadband, rec_sip_deadband)

        print("Recommended values:")
        print("\t AMBIENT = {}".format(self._ambient_pressure))
        print("\t PUFF: threshold = {}, deadband = {}".format(rec_puff_threshold, rec_puff_deadband))
        print("\t SIP: threshold = {}, deadband = {}".format(rec_sip_threshold, rec_sip_deadband))
        print("\t Overall Deadband: ", rec_deadband_size)

        # TODO AAM: let OTs manually change thresholds and deadband before timing tests
        self._deadband = rec_deadband_size
        self._sip_threshold = rec_sip_threshold
        self._puff_threshold = rec_puff_threshold

        print("Starting Ramp up/down timing tests...")
        self._puff_ramp_times_test()
        self._sip_ramp_times_test()

        if input("Write user profile to file? (y/n)") is 'y':
            self._writeCsv()
        self._params_set = True

    def _threshold_test(self):
        # Takes 5 pressure readings when desired
        pressures = []
        for i in range(NUM_SAMPLES):
            input("Press Enter to take measurement {}".format(i + 1))
            # sleep to allow for data from read thread to come in
            time.sleep(0.1)
            pressure = self.getPressure()
            pressures.append(pressure)
        print(pressures)
        next_state_prompt = input("Retry this state? (y/n)")
        if next_state_prompt is 'y':
            pressures = self._threshold_test()
        
        return pressures
            
    def _puff_ramp_times_test(self):
        # tests puff ramp up/down times
        # ramp up time starts when the pressure leaves the deadband
        deadband_threshold = self._ambient_pressure+self._deadband
        input("Press Enter when ready to begin")
        time.sleep(0.1)
        pressure = self.getPressure()
        # loop blocks until pressure is outside deadband
        print("Looking for hard puff...")
        while pressure <= self._puff_threshold:
            time.sleep(0.05)
            pressure = self.getPressure()
            # if pressure is within deadband, reset start time
            if pressure < deadband_threshold:
                ramp_up_start_time = time.time()
        ramp_up_time = time.time() - ramp_up_start_time
        while pressure >= deadband_threshold:
            time.sleep(0.025)
            pressure = self.getPressure()
            # if pressure is within deadband, reset start time
            if pressure > self._puff_threshold:
                ramp_down_start_time = time.time()
        ramp_down_time = time.time() - ramp_down_start_time

        # TODO: Check if took more than max allowable time (2000 ms)
        print("Hard puff ramped up in {}".format(ramp_up_time))
        print("Hard puff ramped down in {}".format(ramp_down_time))

        if input("Use these values? (y/n) ") is 'n':
            if input("Do you want to enter values manually or restart the test? (manual, restart): ") is "manual":
                ramp_up_time = input("Enter ramp up time in ms (must be an integer multiple of 50 less than 2000: ")
                ramp_down_time = input("Enter ramp down time in ms (must be an integer multiple of 50 less than 2000: ")
            else:
                self._puff_ramp_times_test()
        self._puff_ramp_down = ramp_down_time
        self._puff_ramp_up = ramp_up_time

    def _sip_ramp_times_test(self):
        # tests sip ramp up/down times
        # ramp up time starts when the pressure leaves the deadband
        deadband_threshold = self._ambient_pressure-self._deadband
        input("Press Enter when ready to begin")
        time.sleep(0.1)
        pressure = self.getPressure()
        # loop blocks until pressure is outside deadband
        print("Looking for hard sip...")
        while pressure >= self._sip_threshold:
            time.sleep(0.025)
            pressure = self.getPressure()
            # if pressure is within deadband, reset start time
            if pressure > deadband_threshold:
                ramp_up_start_time = time.time()
        ramp_up_time = time.time() - ramp_up_start_time
        while pressure <= deadband_threshold:
            time.sleep(0.025)
            pressure = self.getPressure()
            # if pressure is within deadband, reset start time
            if pressure < self._sip_threshold:
                ramp_down_start_time = time.time()
        ramp_down_time = time.time() - ramp_down_start_time

        # TODO: Check if took more than max allowable time (2000 ms)
        print("Hard sip ramped up in {}".format(ramp_up_time))
        print("Hard sip ramped down in {}".format(ramp_down_time))

        if input("Use these values? (y/n) ") is 'n':
            if input("Do you want to enter values manually or restart the test? (manual, restart): ") is "manual":
                ramp_up_time = input("Enter ramp up time in ms (must be an integer multiple of 50 less than 2000: ")
                ramp_down_time = input("Enter ramp down time in ms (must be an integer multiple of 50 less than 2000: ")
            else:
                self._sip_ramp_times_test()
        self._sip_ramp_down = ramp_down_time
        self._sip_ramp_up = ramp_up_time
    
    def _writeCsv(self):
        # Should be called at end of setup routine
        with open('profile.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([self._sip_threshold,
                             self._deadband,
                             self._puff_threshold,
                             self._sip_ramp_down,
                             self._sip_ramp_up,
                             self._puff_ramp_down,
                             self._puff_ramp_up])
    def _readCsv(self):
        with open('profile.csv') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            # row = reader[0]
            for row in reader:
                self._sip_threshold = float(row[0])
                self._deadband = float(row[1])
                self._puff_threshold = float(row[2])
                self._sip_ramp_down = float(row[3])
                self._sip_ramp_up = float(row[4])
                self._puff_ramp_down = float(row[5])
                self._puff_ramp_up = float(row[6])

def main():
    ser = Serial('/dev/ttyACM0',9600,timeout=None)
    snp_state = SnPState(ser)
    snp_state.start()
    time.sleep(0.1)
    snp_state.setup()
    # snp_state._sip_ramp_times_test()
    prev_state = 'hard_puff'
    while True:
        # pressure = snp_state.getPressure()
        # print(pressure, time.time())
        curr_state = snp_state.getState()
        if prev_state is not curr_state:
            prev_state = curr_state
            pressure = snp_state.getPressure()
            print("State change: ", curr_state, pressure)

        time.sleep(0.025)
    return

if __name__ == '__main__':
    main()