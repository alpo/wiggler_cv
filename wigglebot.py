import colorsys

import pigpio
import time

from motors import Motors
from wiggler_cv import WigglerCV, OsdText


def main():
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
        # h, s, v = colorsys.rgb_to_hsv(modes[old_mode][0], modes[old_mode][1], modes[old_mode][2])
        # print(position)
        t = time.perf_counter() - start_time
        v = t / 150.0
        h = (t * 0.03) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, v)
        motors.set((r, g, b))
        osd_list = [
            OsdText(x=550, y=20, text='r {:.2f}'.format(r)),
            OsdText(x=550, y=40, text='g {:.2f}'.format(g)),
            OsdText(x=550, y=60, text='b {:.2f}'.format(b)),
            OsdText(x=550, y=80, text='h {:.2f}'.format(h)),
            OsdText(x=550, y=100, text='v {:.2f}'.format(v)),
        ]
        wcv.osd_update(osd_list)
        # mode = int(t / 10) % len(modes)
        # if mode != old_mode:
        #     motors.set(modes[mode])
        #     old_mode = mode
        if t > 150:
            break
    wcv.terminate()
    motors.off()
    pi.stop()


if __name__ == '__main__':
    main()