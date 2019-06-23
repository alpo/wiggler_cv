from collections import namedtuple

import pigpio

Transition = namedtuple('Transition', ['time_us', 'pin', 'level'])


class WavePoint:
    def __init__(self, up_mask, down_mask, delay_us):
        self.up_mask = up_mask
        self.down_mask = down_mask
        self.delay_us = delay_us

    def __repr__(self):
        return self.__class__.__name__ + '(up_mask={:032b}, down_mask={:032b}, delay_us={})'.format(self.up_mask,
                                                                                                    self.down_mask,
                                                                                                    self.delay_us)
        # return self.__class__.__name__ + '(up_mask=%r, down_mask=%r, delay_us=%r)' % self


# WavePoint = namedtuple('WavePoint', ['up_mask', 'down_mask', 'delay_us'], verbose=True)


class Motors:
    def __init__(self, pi, freq=3000):
        self.pi = pi
        self.freq = freq
        self.pins = (19, 20, 21, 22)
        self.count = len(self.pins)
        for pin in self.pins:
            self.pi.set_mode(pin, pigpio.OUTPUT)

    def set(self, speeds):
        """

        :param speeds: max speed is 1
        :return:
        """
        self.period_us = 1e6 // self.freq
        self.phases = tuple(speeds)
        transitions = []
        transitions.append(Transition(time_us=0, pin=self.pins[0], level=1))
        transitions.append(Transition(time_us=int(self.period_us / 2), pin=self.pins[0], level=0))
        for i in range(self.count - 1):
            pin = self.pins[i + 1]
            delay_us = int(self.phases[i] * self.period_us)
            transitions.append(Transition(time_us=delay_us, pin=pin, level=1))
            transitions.append(
                Transition(time_us=int((delay_us + self.period_us / 2) % self.period_us), pin=pin, level=0))

        transitions = sorted(transitions)

        prev_time = 0
        up_mask = down_mask = delay_us = None
        wave_points = []
        for tr in transitions:
            if up_mask is not None and prev_time == tr.time_us:
                if tr.level:
                    up_mask |= (1 << tr.pin)
                else:
                    down_mask |= (1 << tr.pin)
            else:
                if up_mask is not None:
                    delay_us = tr.time_us - prev_time
                    print('emit (up_mask={:032b}, down_mask={:032b}, delay_us={})'.format(up_mask, down_mask, delay_us))
                    wave_points.append(pigpio.pulse(up_mask, down_mask, delay_us))

                up_mask = 0
                down_mask = 0
                if tr.level:
                    up_mask = 1 << tr.pin
                else:
                    down_mask = 1 << tr.pin
                # delay_us = tr.time_us - prev_time
                prev_time = tr.time_us

        if up_mask is not None:
            delay_us = int(self.period_us - prev_time)
            print('emit (up_mask={:032b}, down_mask={:032b}, delay_us={})'.format(up_mask, down_mask, delay_us))
            wave_points.append(pigpio.pulse(up_mask, down_mask, delay_us))

        # if prev_time < self.period_us:
        #     print('emit (up_mask={:032b}, down_mask={:032b}, delay_us={})'.format(0, 0, int(self.period_us - prev_time)))
        #     wave_points.append(pigpio.pulse(0, 0, int(self.period_us - prev_time)))


        self.pi.wave_clear()

        # wave_points = [
        #     pigpio.pulse((1 << self.pins[0]) | (1 << self.pins[1]) | (1 << self.pins[2]) | (1 << self.pins[3]), 0, 166),
        #     pigpio.pulse(0, (1 << self.pins[0]) | (1 << self.pins[1]) | (1 << self.pins[2]) | (1 << self.pins[3]), 166)
        # ]
        self.pi.wave_add_generic(wave_points)
        wave_id = self.pi.wave_create()

        self.pi.wave_send_repeat(wave_id)

    def off(self):
        self.pi.wave_tx_stop()
