import io
import json
import math
import threading
from collections import namedtuple
from subprocess import Popen, PIPE
from threading import Thread, Condition

import cv2
import picamera
import pigpio
from picamera.array import bytes_to_rgb

OsdText = namedtuple('OsdText', ['x', 'y', 'text'])
OsdDot = namedtuple('OsdDot', ['x', 'y'])
OsdVector = namedtuple('OsdVector', ['x1', 'y1', 'x2', 'y2'])


class WigglerCV(io.IOBase):
    font = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_res_h = None
        self.input_res_v = None
        self.input_fps = None
        self.debug_scale = None
        self.debug_level = None
        self.stream_cmd = None
        self.gstreamer_pipe = None
        self._thread = None
        self._terminate = False
        self._corners = None
        self._camera = None
        self._ready = Condition()
        self._aruco_dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
        self._stream_proc = None
        self._gstreamer = None
        self._osd_list = None
        self._osd_list_lock = threading.Lock()

    def writable(self):
        return True

    def write(self, b):
        input_frame = bytes_to_rgb(b, self._camera.resolution)
        gray = cv2.cvtColor(input_frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = cv2.aruco.detectMarkers(gray, self._aruco_dictionary)
        with self._ready:
            if len(corners):
                self._corners = (corners, ids)
            if self._corners is not None:
                self._ready.notify_all()

        if self.debug_level >= 2:
            cv2.aruco.drawDetectedMarkers(input_frame, corners, ids)

        with self._osd_list_lock:
            if self._osd_list is not None:
                for item in self._osd_list:
                    if isinstance(item, OsdText):
                        cv2.putText(input_frame, item.text, (int(item.x), int(item.y)), fontFace=self.font,
                                    fontScale=0.5,
                                    color=(255, 255, 255), thickness=1)#, lineType=cv2.LINE_AA)
                    elif isinstance(item, OsdDot):
                        cv2.circle(input_frame, (int(item.x), int(item.y)), radius=2,
                                   color=(0, 0, 255), thickness=3)
                    elif isinstance(item, OsdVector):
                        cv2.arrowedLine(input_frame, (int(item.x1), int(item.y1)),
                                        (int(item.x2), int(item.y2)),
                                        color=(0, 255, 0), thickness=2)

        if self._stream_proc:
            try:
                self._stream_proc.stdin.write(cv2.cvtColor(input_frame, cv2.COLOR_BGR2YUV_I420).tobytes())
            except Exception as e:
                print(e)
        if self._gstreamer:
            try:
                self._gstreamer.write(input_frame)
            except Exception as e:
                print(e)

    def osd_update(self, osd_list):
        with self._osd_list_lock:
            self._osd_list = osd_list[:]

    def terminate(self):
        self._terminate = True
        self._thread.join()

    def setup(self, cfg_file='wiggler_cv.json'):
        with open(cfg_file, 'r') as f:
            config = json.load(f)

        for k, v in config.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def run(self):
        self._thread = Thread(target=self._run)
        self._thread.start()

    def _run(self):
        self._camera = picamera.PiCamera(resolution='{}x{}'.format(self.input_res_h, self.input_res_v),
                                         framerate=self.input_fps)
        pi = pigpio.pi()
        if self.stream_cmd:
            self._stream_proc = Popen(self.stream_cmd, stdin=PIPE)
        if self.gstreamer_pipe:
            pipe = ' ! '.join(self.gstreamer_pipe)
            # noinspection PyArgumentList
            self._gstreamer = cv2.VideoWriter(pipe,
                                              cv2.CAP_GSTREAMER,
                                              self.input_fps,
                                              (self.input_res_h, self.input_res_v))

        try:
            self._camera.start_recording(self, 'bgr')
            pi.write(26, 1)
            while not self._terminate:
                try:
                    self._camera.wait_recording(1)
                except KeyboardInterrupt:
                    break
        finally:
            pi.write(26, 0)
            self._camera.stop_recording()
            self._camera.close()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        with self._ready:
            try:
                self._ready.wait()
            except KeyboardInterrupt:
                self._terminate = True
            return self._corners
