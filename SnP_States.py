class State():
    def __init__(self, hard_sip_threshold, soft_sip_threshold, soft_puff_threshold, hard_puff_threshold):
        self._thresholds = {'hard_sip': hard_sip_threshold,
                            'soft_sip': soft_sip_threshold,
                            'soft_puff': soft_puff_threshold,
                            'hard_puff': hard_puff_threshold}
        self._state = ''

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
