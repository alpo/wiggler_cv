import io
import json
import math
import queue
import threading
import time
from collections import namedtuple
from subprocess import Popen, PIPE

import cv2
import picamera
import pigpio
from picamera.array import bytes_to_rgb

from markers import Markers

OsdText = namedtuple('OsdText', ['x', 'y', 'text'])
OsdDot = namedtuple('OsdDot', ['x', 'y'])
OsdVector = namedtuple('OsdVector', ['x1', 'y1', 'x2', 'y2'])


class WigglerCV(io.IOBase):
    font = cv2.FONT_HERSHEY_SIMPLEX
    Config = type('Config', (object,), {})

    def __init__(self, pi, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = WigglerCV.Config()

        self._thread = None
        self._terminate = False
        self._pi = pi
        self._picamera = None
        self._aruco_dictionary = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_100)
        self._stream_proc = None
        self._gstreamer = None
        self._osd_list = None
        self._osd_list_lock = threading.Lock()
        self._position = None
        self._position_queue = queue.Queue(2)
        self.streaming_time = 0
        self.osd_time = 0
        self.aruco_time = 0

    def setup(self, cfg_file='wiggler_cv.json'):
        with open(cfg_file, 'r') as f:
            config = json.load(f)

        for k, v in config.items():
            setattr(self.config, k, v)

    def run(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def _run(self):
        """
        Thread function
        """
        pi = pigpio.pi()

        try:
            self._picamera = picamera.PiCamera(
                resolution='{}x{}'.format(self.config.input_res_h, self.config.input_res_v),
                framerate=self.config.input_fps)
            if hasattr(self.config, 'stream_cmd'):
                stream_cmd = self.config.stream_cmd.format(width=self.config.input_res_h,
                                                           height=self.config.input_res_v,
                                                           fps=self.config.input_fps, host='brix.local', port=5000,
                                                           ds='brix.local:5000')
                self._stream_proc = Popen(stream_cmd, stdin=PIPE)
            if hasattr(self.config, 'gstreamer_pipe'):
                pipe = ' ! '.join(self.config.gstreamer_pipe).format(width=self.config.input_res_h,
                                                                     height=self.config.input_res_v,
                                                                     fps=self.config.input_fps, host='brix.local',
                                                                     port=5000,
                                                                     ds='brix.local:5000')
                # noinspection PyArgumentList
                self._gstreamer = cv2.VideoWriter(pipe,
                                                  cv2.CAP_GSTREAMER,
                                                  self.config.input_fps,
                                                  (self.config.input_res_h, self.config.input_res_v))

            self._picamera.start_recording(self, format='bgr')
            pi.write(26, 1)
            pi.write(23, 1)
            while not self._terminate:
                try:
                    self._picamera.wait_recording(1)
                except KeyboardInterrupt:
                    break
        finally:
            pi.write(26, 0)
            pi.write(23, 0)
            try:
                self._picamera.stop_recording()
            except:
                pass
            try:
                self._picamera.close()
            except:
                pass
            try:
                self._position_queue.put_nowait(StopIteration)
            except:
                pass
            print('thread finished')

    def writable(self):
        return True

    def write(self, buffer):
        """
        Workhorse. Called by picamera and receives frame.
        :param buffer: frame in picamera format
        """
        start_time = time.perf_counter()
        input_frame = picamera.array.bytes_to_rgb(buffer, self._picamera.resolution)
        corners = []
        ids = None
        left = 0
        top = 0
        if self._position is not None:
            left = int(max(0, self._position.coordinates[0] - self.config.fast_area_size / 2))
            top = int(max(0, self._position.coordinates[1] - self.config.fast_area_size / 2))
            right = int(min(self.config.input_res_h, self._position.coordinates[0] + self.config.fast_area_size / 2))
            bottom = int(min(self.config.input_res_v, self._position.coordinates[1] + self.config.fast_area_size / 2))
            gray = cv2.cvtColor(input_frame[top:bottom + 1, left:right + 1], cv2.COLOR_BGR2GRAY)
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self._aruco_dictionary)
        if len(corners) == 0:
            gray = cv2.cvtColor(input_frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self._aruco_dictionary)
        else:
            for marker_idx in range(len(corners)):
                for corner_idx in range(4):
                    corners[marker_idx][0][corner_idx][0] += left
                    corners[marker_idx][0][corner_idx][1] += top

        if len(corners) > 0:
            try:
                new_position = Markers.get_location(corners, ids)
                if new_position is not None:
                    self._position = new_position
            except:
                pass

        aruco_time = time.perf_counter()

        own_osd_list = []
        if self._position is not None:
            try:
                self._position_queue.put_nowait(self._position)
            except:
                pass

            if self.config.debug_level >= 2:
                cv2.aruco.drawDetectedMarkers(input_frame, corners, ids)
                cv2.rectangle(input_frame,
                              (int(self._position.coordinates[0]) - self.config.fast_area_size // 2,
                               int(self._position.coordinates[1]) - self.config.fast_area_size // 2),
                              (int(self._position.coordinates[0]) + self.config.fast_area_size // 2,
                               int(self._position.coordinates[1]) + self.config.fast_area_size // 2),
                              color=(0, 255, 255), thickness=1)

            if self.config.debug_level >= 1:
                scale = math.sqrt(self._position.rotscale[0] ** 2 + self._position.rotscale[1] ** 2)
                own_osd_list = [
                    OsdVector(x1=self._position.coordinates[0],
                              y1=self._position.coordinates[1],
                              x2=self._position.coordinates[0] + 20 * self._position.rotscale[0],
                              y2=self._position.coordinates[1] + 20 * self._position.rotscale[1]),
                    OsdText(x=5, y=20, text='x {:4.0f}px'.format(self._position.coordinates[0])),
                    OsdText(x=5, y=40, text='y {:4.0f}px'.format(self._position.coordinates[1])),
                    OsdText(x=5, y=60, text='angle {:4.0f}deg'.format(math.atan2(self._position.rotscale[1],
                                                                                 self._position.rotscale[
                                                                                     0]) / math.pi * 180)),
                    OsdText(x=5, y=80, text='scale {:3.1f}px/mm'.format(scale)),
                    OsdText(x=5, y=100, text='RMSE {:4.0f}px'.format(self._position.cost)),
                    OsdText(x=5, y=120, text='{:3.0f}:{:3.0f}:{:3.0f}'.format(self.aruco_time * 1000,
                                                                              self.osd_time * 1000,
                                                                              self.streaming_time * 1000))
                ]

        self.draw_osd_list(input_frame, own_osd_list)
        with self._osd_list_lock:
            if self._osd_list is not None:
                self.draw_osd_list(input_frame, self._osd_list)
        osd_time = time.perf_counter()

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

        streaming_time = time.perf_counter()
        self.streaming_time = streaming_time - osd_time
        self.osd_time = osd_time - aruco_time
        self.aruco_time = aruco_time - start_time
        # print('aruco {:3.0f}ms,osd {:3.0f}ms,stream {:3.0f}ms'.format(self.aruco_time * 1000,
        #                                                               self.osd_time * 1000,
        #                                                               self.streaming_time * 1000))

    def draw_osd_list(self, input_frame, osd_list):
        for item in osd_list:
            if isinstance(item, OsdText):
                cv2.putText(input_frame, item.text, (int(item.x), int(item.y)), fontFace=self.font,
                            fontScale=0.5,
                            color=(255, 255, 255), thickness=1)  # , lineType=cv2.LINE_AA)
            elif isinstance(item, OsdDot):
                cv2.circle(input_frame, (int(item.x), int(item.y)), radius=2,
                           color=(0, 0, 255), thickness=3)
            elif isinstance(item, OsdVector):
                cv2.arrowedLine(input_frame, (int(item.x1), int(item.y1)),
                                (int(item.x2), int(item.y2)),
                                color=(0, 255, 0), thickness=2)

    def osd_update(self, osd_list):
        with self._osd_list_lock:
            self._osd_list = osd_list[:]

    def terminate(self):
        self._terminate = True
        self._thread.join()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        position = self._position_queue.get()
        if position == StopIteration:
            raise StopIteration
        else:
            return position
