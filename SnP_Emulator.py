"""
SnP_Emulator.py
====================================
The Sip and Puff Emulator.
"""
import threading
import time
import spidev
import csv
NUM_SAMPLES = 3

class SnPState(threading.Thread):
    """Class for reading and translating pressure values received over SPI
    to sip and puff states.
    After instantiating this class, it should have the thread started and the setup method invoked.
    This class is intended to be used with ADC ADC: MCP3201-CI/P
    Ex: ::
        snp_state = SnPState()
        snp_state.start()
        time.sleep(0.1)
        snp_state.setup()
    """
    def __init__(self):
        """Constructor. Initializes the SPI bus for use with
        ADC: MCP3201-CI/P.
        The sip and puff parameters must be set up with the setup() method.
        """
        super().__init__(daemon=True)
        bus = 0
        device = 0
        self._port = spidev.SpiDev()
        self._port.open(bus, device)

        # Speed should be faster than 10kHz as recommended by ADC data sheet
        self._port.max_speed_hz = 16000
        self._port.bits_per_word = 8

        # Think this corresponds to the ADC sampling when the clock (or select?) has a rising edge
        # and shift out data on a falling edge
        self._port.mode = 0b10
        self._port.threewire = False

        # CS active low
        self._port.cshigh = False

        # Lock for protecting the pressure.
        self._press_lock = threading.Lock()
        self._curr_pressure = 0
        self._ambient_pressure = 0.0
        self._deadband = 0
        self._sip_threshold = 0
        self._sip_ramp_down = 0
        self._sip_ramp_up = 0
        self._puff_threshold = 0
        self._puff_ramp_down = 0
        self._puff_ramp_up = 0
        self._params_set = False
        self._state = 'deadband'
        self._ramp_wait = False
        self._ramp_time = 0.0
    
    def _setState(self, pressure):
        """Sets the sip and puff state according to the incoming pressure.

        Args:
            pressure (int): The input pressure value.
        """
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
        """Function ran by thread when ::meth::'start()' is called.
           It reads 2 bytes at a time and does bitmath to translate what it
           reads into the 12-bit number. The bitmath can be determined from the ADC data sheet.
        """
        while True:
            data_bytes = self._port.readbytes(2)
            # MSB is 5 bits of first received byte
            data_MSB = (data_bytes[0] & 0x1F) << 7
            # LSB has extra bit at end
            data_LSB = data_bytes[1] >> 1
            data = data_MSB+data_LSB
            self._setPressure(data)

    def _setPressure(self, pressure):
        """Sets the current pressure and updates the state if the user profile has been setup.
        This should only be called from within the run() method.

        Args:
            pressure (int): The input pressure.
        """
        with self._press_lock:
            self._curr_pressure = pressure
        if self._params_set:
            self._setState(pressure)
    def getPressure(self):
        """Safe external interface for getting the current pressure value.
        """
        with self._press_lock:
            return self._curr_pressure
    
    def getState(self):
        """Interface for getting current state.
        """
        return self._state            

    def setup(self):
        """Setup routine. This should always be called after class instantiation and thread starting.
        It:
            1. Reads in the user profile if told to.
            2. Samples NUM_SAMPLES times to determine an average ambient pressure.
            3. Runs through a routine to set all of the sip/puff thresholds.
            4. Allows manual changing of calculated parameters.
            5. Goes through a test to determine ramp times.
            6. Prompts user to save the user profile.
        """
        # 1. User identifier/profile load (assume new user)
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
            # time.sleep(0.1)
        avg_ambient_pressure = avg_ambient_pressure / NUM_SAMPLES
        self._ambient_pressure = avg_ambient_pressure

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
        """Sip and Puff threshold test.
        Reads in NUM_SAMPLES pressure values, one at a time depending on the user pressing ENTER.

        Returns:
            pressures (list): List of NUM_SAMPLES pressure values.
        """
        # Takes pressure readings when desired
        pressures = []
        for i in range(NUM_SAMPLES):
            input("Press Enter to take measurement {}".format(i + 1))
            # sleep to allow for data from read thread to come in
            # time.sleep(0.1)
            pressure = self.getPressure()
            pressures.append(pressure)
        print(pressures)
        next_state_prompt = input("Retry this state? (y/n)")
        if next_state_prompt is 'y':
            pressures = self._threshold_test()
        
        return pressures
            
    def _puff_ramp_times_test(self):
        """Determines puff ramp up and down times.
        It measures the time to go from the deadband range to a hard puff the time back to deadband.
        Allows for manual change of numbers at end.
        """
        # tests puff ramp up/down times
        # ramp up time starts when the pressure leaves the deadband
        deadband_threshold = self._ambient_pressure+self._deadband
        input("Press Enter when ready to begin")
        # time.sleep(0.1)
        pressure = self.getPressure()
        # loop blocks until pressure is outside deadband
        print("Looking for hard puff...")
        while pressure <= self._puff_threshold:
            # time.sleep(0.05)
            pressure = self.getPressure()
            # if pressure is within deadband, reset start time
            if pressure < deadband_threshold:
                ramp_up_start_time = time.time()
        ramp_up_time = time.time() - ramp_up_start_time
        while pressure >= deadband_threshold:
            # time.sleep(0.025)
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
        """Determines sip ramp up and down times.
        It measures the time to go from the deadband range to a hard sip the time back to deadband.
        Allows for manual change of numbers at end.
        """
        # tests sip ramp up/down times
        # ramp up time starts when the pressure leaves the deadband
        deadband_threshold = self._ambient_pressure-self._deadband
        input("Press Enter when ready to begin")
        # time.sleep(0.1)
        pressure = self.getPressure()
        # loop blocks until pressure is outside deadband
        print("Looking for hard sip...")
        while pressure >= self._sip_threshold:
            # time.sleep(0.025)
            pressure = self.getPressure()
            # if pressure is within deadband, reset start time
            if pressure > deadband_threshold:
                ramp_up_start_time = time.time()
        ramp_up_time = time.time() - ramp_up_start_time
        while pressure <= deadband_threshold:
            # time.sleep(0.025)
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
        """Writes a one-line file profile.csv with sip and puff parameters
        """
        # Should be called at end of setup routine
        with open('profile.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow([self._ambient_pressure,
                             self._sip_threshold,
                             self._deadband,
                             self._puff_threshold,
                             self._sip_ramp_down,
                             self._sip_ramp_up,
                             self._puff_ramp_down,
                             self._puff_ramp_up])
    def _readCsv(self):
        """Reads profile.csv for the last saved user profile and populates the class parameter values.
        """
        with open('profile.csv') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            # row = reader[0]
            for row in reader:
                self._ambient_pressure = float(row[0])
                self._sip_threshold = float(row[1])
                self._deadband = float(row[2])
                self._puff_threshold = float(row[3])
                self._sip_ramp_down = float(row[4])
                self._sip_ramp_up = float(row[5])
                self._puff_ramp_down = float(row[6])
                self._puff_ramp_up = float(row[7])
        
    def __del__(self):
        """Destructor to close spi port.
        """
        self._port.close()

def main():
    snp_state = SnPState()
    snp_state.start()
    time.sleep(0.1)
    snp_state.setup()
    prev_state = 'hard_puff'
    while True:
        curr_state = snp_state.getState()
        if prev_state is not curr_state:
            prev_state = curr_state
            pressure = snp_state.getPressure()
            print("State change: ", curr_state, pressure)

        time.sleep(0.025)
    return

if __name__ == '__main__':
    main()
