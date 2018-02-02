import time
from unittest import TestCase

from wiggler_cv import WigglerCV


class TestWigglerCV(TestCase):
    def test_load_config(self):
        wcv = WigglerCV()
        wcv.setup(cfg_file='wiggler_cv.json')
        self.assertIsInstance(wcv.input_res_h, int)

    def test_run(self):
        wcv = WigglerCV()
        wcv.setup(cfg_file='wiggler_cv.json')
        wcv.run()
        start_time = time.perf_counter()
        for position in wcv:
            # print(position)
            if time.perf_counter() > start_time + 150:
                break
        wcv.terminate()
