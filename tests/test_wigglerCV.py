import time
from unittest import TestCase

import pigpio

from motors import Motors
from wiggler_cv import WigglerCV, OsdText


class TestWigglerCV(TestCase):
    def test_load_config(self):
        wcv = WigglerCV(None)
        wcv.setup(cfg_file='wiggler_cv.json')
        self.assertIsInstance(wcv.config.input_res_h, int)

    def test_run(self):
        pi = pigpio.pi()
        motors = Motors(pi)
        motors.off()
        wcv = WigglerCV(pi)
        wcv.setup(cfg_file='wiggler_cv.json')
        wcv.run()
        modes = [
            (1., 0., 0.),
            (0., 1., 0.),
            (0., 0., 1.)
        ]
        start_time = time.perf_counter()
        old_mode = 0
        motors.set(modes[old_mode])
        for position in wcv:
            osd_list = [
                OsdText(x=550, y=20, text='r {:.1f}'.format(modes[old_mode][0])),
                OsdText(x=550, y=40, text='g {:.1f}'.format(modes[old_mode][1])),
                OsdText(x=550, y=60, text='b {:.1f}'.format(modes[old_mode][2])),
            ]
            wcv.osd_update(osd_list)
            # print(position)
            t = time.perf_counter() - start_time
            mode = int(t / 10) % len(modes)
            if mode != old_mode:
                motors.set(modes[mode])
                old_mode = mode
            if t > 150:
                break
        wcv.terminate()
        motors.off()
        pi.stop()
