import threading
from serial import Serial
from queue import Queue
from SnP_Emulator import SnPState
import time

NUM_SAMPLES = 5
serial_port = Serial('/dev/ttyACM0', 9600, timeout=None)
data_queue = Queue()
def read_from_port(ser):
    connected = False
    while not connected:
        #serin = ser.read()
        connected = True

        while True:
            s = [0]
            read_serial = ser.readline()
            # print(read_serial)
            try:
                s[0] = int(read_serial)
                # print(s[0])
            # print("test")
                # reading = ser.readline()
                while not data_queue.empty():
                    data_queue.get_nowait()
                data_queue.put(s[0])
                # handle_data()
                # time.sleep(0.002)
                time.sleep(0.025)
            except ValueError:
                # print("Value Error")
                pass


def threshold_test():
    # Takes 5 pressure readings when desired
    pressures = []
    for i in range(NUM_SAMPLES):
        input("Press Enter to take measurement {}".format(i + 1))
        # sleep to allow for data from read thread to come in
        time.sleep(0.1)
        if not data_queue.empty():
            pressure = data_queue.get_nowait()
            pressures.append(pressure)
            
        else:
            i = i - 1
    print(pressures)
    next_state_prompt = input("Move to next state? (y/n)")
    if next_state_prompt is 'n':
        pressures = threshold_test()
    
    return pressures
        
def puff_ramp_times_test(deadband_threshold, puff_threshold):
    # tests puff ramp up/down times
    # ramp up time starts when the pressure leaves the deadband
    
    input("Press Enter when ready to begin")
    time.sleep(0.1)
    while not data_queue.empty():
            pressure = data_queue.get_nowait()
    # loop blocks until pressure is outside deadband
    print("Looking for hard puff...")
    while pressure <= puff_threshold:
        if not data_queue.empty():
            pressure = data_queue.get_nowait()
        # if pressure is within deadband, reset start time
        if pressure < deadband_threshold:
            ramp_up_start_time = time.time()
        print(pressure)
        time.sleep(0.025)
    ramp_up_time = time.time() - ramp_up_start_time
    while pressure >= deadband_threshold:
        if not data_queue.empty():
            pressure = data_queue.get_nowait()
        # if pressure is within deadband, reset start time
        if pressure > puff_threshold:
            ramp_down_start_time = time.time()
        print(pressure)
        time.sleep(0.025)
    ramp_down_time = time.time() - ramp_down_start_time

    # TODO: Check if took more than max allowable time (2000 ms)
    print("Hard puff ramped up in {}".format(ramp_up_time))
    print("Hard puff ramped down in {}".format(ramp_down_time))

    if input("Use these values? (y/n) ") is 'n':
        if input("Do you want to enter values manually or restart the test? (manual, restart): ") is "manual":
            ramp_up_time = input("Enter ramp up time in ms (must be an integer multiple of 50 less than 2000: ")
            ramp_down_time = input("Enter ramp down time in ms (must be an integer multiple of 50 less than 2000: ")
        else:
            puff_ramp_times_test(deadband_threshold, puff_threshold)
    return ramp_up_time, ramp_down_time

def sip_ramp_times_test(deadband_threshold, sip_threshold):
    # tests sip ramp up/down times
    # ramp up time starts when the pressure leaves the deadband
    
    input("Press Enter when ready to begin")
    time.sleep(0.1)
    while not data_queue.empty():
            pressure = data_queue.get_nowait()
            time.sleep(0.025)
    # time.sleep(0.05)
    # loop blocks until pressure is outside deadband
    print("Looking for hard sip...")
    while pressure >= sip_threshold:
        if not data_queue.empty():
            pressure = data_queue.get_nowait()
        # if pressure is within deadband, reset start time
        if pressure > deadband_threshold:
            ramp_up_start_time = time.time()
        print(pressure)
        time.sleep(0.025)
    ramp_up_time = time.time() - ramp_up_start_time
    while pressure <= deadband_threshold:
        if not data_queue.empty():
            pressure = data_queue.get_nowait()
        # if pressure is within deadband, reset start time
        if pressure < sip_threshold:
            ramp_down_start_time = time.time()
        print(pressure)
        time.sleep(0.025)
    ramp_down_time = time.time() - ramp_down_start_time

    # TODO: Check if took more than max allowable time (2000 ms)
    print("Hard sip ramped up in {}".format(ramp_up_time))
    print("Hard sip ramped down in {}".format(ramp_down_time))

    if input("Use these values? (y/n) ") is 'n':
        if input("Do you want to enter values manually or restart the test? (manual, restart): ") is "manual":
            ramp_up_time = input("Enter ramp up time in ms (must be an integer multiple of 50 less than 2000: ")
            ramp_down_time = input("Enter ramp down time in ms (must be an integer multiple of 50 less than 2000: ")
        else:
            sip_ramp_times_test(deadband_threshold, sip_threshold)
    return ramp_up_time, ramp_down_time

def setup():
    # snp_state = SnPState(0, 0, 0, 0)
    pressures = {'hard_sip': [],
                  'soft_sip': [],
                  'hard_puff': [],
                  'soft_puff': []
                  }
    avg_ambient_pressure = 0
    i = 0
    while i < NUM_SAMPLES:
        if not data_queue.empty():
            pressure = data_queue.get_nowait()
            avg_ambient_pressure += pressure
            i = i + 1
        time.sleep(0.025)
    avg_ambient_pressure = avg_ambient_pressure/NUM_SAMPLES
    # 1. User identifier/profile load (assume new user)
    # if input("Setup a new user profile?") is 'n':
    #     print("Load profile")
    # 2. SnP thresholds
    for state in pressures.keys():
        print("Starting {} measurements".format(state))
        pressures[state] = threshold_test()
        # print(pressures[state])
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
    print("\t PUFF: threshold = {}, deadband = {}".format(rec_puff_threshold, rec_puff_deadband))
    print("\t SIP: threshold = {}, deadband = {}".format(rec_sip_threshold, rec_sip_deadband))
    print("\t Overall Deadband: ", rec_deadband_size)

    # TODO AAM: let OTs manually change thresholds and deadband before timing tests

    print("Starting Ramp up/down timing tests...")
    puff_ramp_up, puff_ramp_down = puff_ramp_times_test(avg_ambient_pressure + rec_deadband_size, rec_puff_threshold)
    sip_ramp_up, sip_ramp_down = sip_ramp_times_test(avg_ambient_pressure - rec_deadband_size, rec_sip_threshold)

    
    

def main():
    thread = threading.Thread(target=read_from_port, args=(serial_port,),daemon=True)
    thread.start()

    # snp_state = State(100, 120, 150, 200)
    # snp_state = SnPState(0,0,0,0)
    setup()
    # while True:
    #     # if not data_queue.empty():
    #     #     pressure = data_queue.get_nowait()
    #     #     print(pressure, data_queue.qsize())
    #     # time.sleep(0.025)
    #     # else:
    #     #     print("data queue is empty")
    #     time.sleep(0.025)
    thread.join(timeout=1)
    return

if __name__ == '__main__':
    main()