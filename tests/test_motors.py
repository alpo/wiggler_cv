from unittest import TestCase
import time
from sonicmotors import Motors
import pigpio


class TestMotors(TestCase):
    def test_set(self):
        pi = pigpio.pi()
        motors = Motors(pi=pi)
        motors.freq = 3000
        for ph13 in (x / 10.0 for x in range(0, 9)):
            #motors.set((0, 0, 0))
            motors.set((ph13, 0.0, ph13))
            time.sleep(4)

        motors.off()

    def test_off(self):
        self.fail()
