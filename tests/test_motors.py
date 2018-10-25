from unittest import TestCase
import time
from sonicmotors import Motors
import pigpio


class TestMotors(TestCase):
    def test_set(self):
        pi = pigpio.pi()
        motors = Motors(pi=pi)
        # motors.set((0, 0, 0))
        motors.set((0.25, 0.5, 0.75))
        time.sleep(20)

    def test_off(self):
        self.fail()
