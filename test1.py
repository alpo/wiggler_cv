import subprocess
import time

import cv2
import cv2.aruco as aruco
import numpy as np
import picamera
import pigpio
from picamera.array import PiRGBAnalysis

res_h = 320
res_v = 240
fps = 25

show = False
encode = False

class VideoEncoder:
    def start(self, filename, size, fps=30, crf=15):
        self.filename = filename
        self.fps = fps
        self.crf = crf
        self.size = size
        self.proc = subprocess.Popen([
            'ffmpeg', '-y', '-pix_fmt', 'rgb24', '-f', 'rawvideo',
            '-s', '%dx%d' % self.size, '-r', str(self.fps),
            '-i', '-', '-crf', str(self.crf),
            self.filename],
            stdin=subprocess.PIPE)

    def encode(self, img):
        self.proc.stdin.write(img.tobytes())


class ImageAnalyser(PiRGBAnalysis):
    font = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self, camera, encoder):
        super(ImageAnalyser, self).__init__(camera)
        self.encoder = encoder
        self.x = None
        self.y = None
        self.r = None

    def analyse(self, frame):
        start_time = time.perf_counter()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # gray = cv2.medianBlur(gray, 5)

        circles = None
        # circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
        #                            param1=50,
        #                            param2=30,
        #                            minRadius=int(res_h / 20),
        #                            maxRadius=int(res_h / 16))

        corners, ids, rejected = aruco.detectMarkers(gray,
                                                     aruco.Dictionary_get(aruco.DICT_4X4_100))
        if len(corners):
            # print(corners)
            frame = aruco.drawDetectedMarkers(gray, corners, ids)

        cv_time = time.perf_counter() - start_time

        print('{}ms'.format(cv_time * 1000))

        if circles is not None:
            self.x, self.y, self.r = circles[0, 0, :]
            # print('x={},y={},r={}'.format(self.x, self.y, self.r))

        if self.x is not None and self.y is not None and self.r is not None:
            x_display, y_display, r_display = np.uint16(np.around([self.x, self.y, self.r]))

            cv2.circle(frame, (x_display, y_display), radius=r_display,
                       color=(0, 255, 0), thickness=2)
            cv2.circle(frame, (x_display, y_display), radius=2,
                       color=(0, 0, 255), thickness=3)

            cv2.putText(frame,
                        '{},{}'.format(self.x, self.y),
                        (x_display, y_display),
                        fontFace=self.font,
                        fontScale=0.5,
                        color=(255, 255, 255),
                        thickness=1,
                        lineType=cv2.LINE_AA)

        cv2.putText(frame,
                    '{}ms'.format(cv_time * 1000),
                    (20, 20),
                    fontFace=self.font,
                    fontScale=0.5,
                    color=(255, 255, 255),
                    thickness=1,
                    lineType=cv2.LINE_AA)

        if show:
            cv2.imshow('', frame)
            if cv2.waitKey(1) & 0xff == ord('q'):
                raise Exception
        if encode:
            self.encoder.encode(frame)


encoder = VideoEncoder()
encoder.start('debug.mp4', size=(res_h, res_v), fps=fps)

with picamera.PiCamera(resolution='{}x{}'.format(res_h, res_v), framerate=fps) as camera:
    with ImageAnalyser(camera, encoder) as analyzer:
        camera.start_recording(analyzer, 'bgr')
        pi = pigpio.pi()
        try:
            pi.write(26, 1)
            while True:
                try:
                    camera.wait_recording(1)
                except KeyboardInterrupt:
                    break
        finally:
            pi.write(26, 0)
            camera.stop_recording()
