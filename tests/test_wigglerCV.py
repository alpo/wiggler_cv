import math
import time
from unittest import TestCase

from markers import Markers
from wiggler_cv import WigglerCV, OsdText, OsdVector


class TestWigglerCV(TestCase):
    def test_load_config(self):
        wcv = WigglerCV()
        wcv.setup(cfg_file='../wiggler_cv.json')
        self.assertIsInstance(wcv.input_res_h, int)

    def test_run(self):
        wcv = WigglerCV()
        wcv.setup(cfg_file='../wiggler_cv.json')
        wcv.run()
        start_time = time.perf_counter()
        position = None
        for corners, ids in wcv:
            # print(corners, ids)
            new_position = Markers.get_location(corners, ids)
            if new_position is not None:
                position = new_position
            if new_position is not None:
                # print(position)
                scale = math.sqrt(position.rotscale[0] ** 2 + position.rotscale[1] ** 2)
                wcv.osd_update([
                    # OsdText(x=20, y=20, text='xc1 {:.1f}px'.format(corners[0][0][0])),
                    # OsdText(x=20, y=40, text='yc1 {:.1f}px'.format(corners[0][0][1])),
                    OsdVector(x1=position.coordinates[0],
                              y1=position.coordinates[1],
                              x2=position.coordinates[0] + 20 * position.rotscale[0],
                              y2=position.coordinates[1] + 20 * position.rotscale[1]),
                    OsdText(x=20, y=60, text='x {:.1f}px'.format(position.coordinates[0])),
                    OsdText(x=20, y=80, text='y {:.1f}px'.format(position.coordinates[1])),
                    OsdText(x=20, y=100, text='scale {:.1f}px/mm'.format(scale)),
                    OsdText(x=20, y=120, text='RMSE {:.1f}px'.format(position.cost))
                ])
            if time.perf_counter() > start_time + 150:
                break
        wcv.terminate()
