# -*- coding: utf8 -*-
#
#          'r' : refresh frame
#          'q' : quit
#          'b' : increase blur
#          'v' : decrease blur
#          '+' : increase lightness (exposition)
#          '-' : decrease lightness
#         'd'  : delete parameters
#   left click : center of the circle of example
#  right click : a point on the radius
# middle click : calculating filter parameters
#

from symbol_detector import core
import numpy as np
from symbol_detector.settings import config
import cv2.cv2 as cv2


class Sampler:
    def __init__(self):
        self.mouse_x = 0
        self.mouse_y = 0
        self.y = 0
        self.cr = 0
        self.cb = 0
        self.im = 0
        self.im_y_cr_cb = None
        self.im_blur = 0
        self.im_show = None
        self.frame = 0
        self._blur = 1
        self._CP = None
        self._radius = None
        self._map = None
        self._points = None
        self._exposure = None
        self._ret = {}

    def _image_events(self, event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            self.mouse_x, self.mouse_y = y, x
            self.y = self.im_y_cr_cb[y][x][0]
            self.cr = self.im_y_cr_cb[y][x][1]
            self.cb = self.im_y_cr_cb[y][x][2]
        elif event == cv2.EVENT_FLAG_LBUTTON:
            self._CP = tuple([int(x), int(y)])
        elif event == cv2.EVENT_RBUTTONDOWN:
            dx = abs(float(self._CP[0]) - float(x))
            dy = abs(float(self._CP[1]) - float(y))
            self._radius = int((dx ** 2 + dy ** 2) ** 0.5)
        elif event == cv2.EVENT_MBUTTONDOWN:
            cv2.circle(self.im_show, self._CP, self._radius, (0, 0, 255), 1)
            self._map = np.zeros(
                [self.im_show.shape[0], self.im_show.shape[1], 1], np.uint8
            )
            cv2.circle(self._map, self._CP, self._radius, 255, -1)
            self._points = core.my_contour(self._map)
            self._calc_params(self.im_y_cr_cb, self._points)
            cv2.imshow("camera", self.im_show)

    def show_camera(self):
        cam = cv2.VideoCapture(config.camera_driver)
        cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        cam.set(cv2.CAP_PROP_EXPOSURE, config.camera_exposure)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera_width)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera_height)
        self._exposure = cam.get(cv2.CAP_PROP_EXPOSURE)
        ret, self.im = cam.read()
        self.im = cv2.flip(self.im, 1)
        self.im_show = self.im.copy()
        while True:
            cv2.imshow("camera", self.im_show)
            k = cv2.waitKey(0) & 0xFF
            if k == ord("q"):
                break
            elif k == ord("r"):
                ret, self.im = cam.read()
                self.im = cv2.flip(self.im, 1)
                if self._blur > 1:
                    self.im_blur = cv2.blur(self.im, (self._blur, self._blur))
                    self.im_show = self.im_blur
                else:
                    self.im_show = self.im.copy()
            elif k == ord("b"):
                self._blur += 2
                self.im_blur = cv2.blur(self.im, (self._blur, self._blur))
                self.im_show = self.im_blur
                print(self._blur)
            elif k == ord("v"):
                if self._blur > 1:
                    self._blur -= 2
                    if self._blur == 1:
                        self.im_show = self.im.copy()
                    else:
                        self.im_blur = cv2.blur(self.im, (self._blur, self._blur))
                        self.im_show = self.im_blur
                    print(self._blur)
            elif k == ord("d"):
                self._ret = {}
                self._CP = None
                self._radius = None
                self._map = None
                self._points = None
                self.im_blur = cv2.blur(self.im, (self._blur, self._blur))
                self.im_show = self.im_blur
            elif k == ord("+") or k == 171:
                future_value = self._exposure + 10
                cam.set(cv2.CAP_PROP_EXPOSURE, future_value)
                if cam.get(cv2.CAP_PROP_EXPOSURE) == future_value:
                    self._exposure = future_value
                print(self._exposure)
            elif k == 45 or k == 173 or k == ord("-"):  # '-'
                future_value = self._exposure - 10
                cam.set(cv2.CAP_PROP_EXPOSURE, future_value)
                if cam.get(cv2.CAP_PROP_EXPOSURE) == future_value:
                    self._exposure = future_value
                print(self._exposure)
            elif k == ord("s"):
                cv2.imwrite("out.jpg", self.im_show)
            self.im_y_cr_cb = cv2.cvtColor(self.im_show, cv2.COLOR_BGR2YCrCb)
            cv2.setMouseCallback("camera", self._image_events)
        cv2.destroyAllWindows()
        if self._ret:
            self.save_settings()

    def save_settings(self):
        config.blur = self._ret["blur"]
        config.camera_exposure = self._ret["exposure"]
        config.y_min = self._ret["y_min"]
        config.y_max = self._ret["y_max"]
        config.cr_min = self._ret["cr_min"]
        config.cr_max = self._ret["cr_max"]
        config.cb_min = self._ret["cb_min"]
        config.cb_max = self._ret["cb_max"]
        config.save()

    def _calc_params(self, image, points):
        im = image.copy()
        y = list()
        cr = list()
        cb = list()
        for p in points[0]:
            y.append(im[p[1], p[0], 0])
            cr.append(im[p[1], p[0], 1])
            cb.append(im[p[1], p[0], 2])
        y.sort()
        cr.sort()
        cb.sort()
        y_min = y[0]
        y_max = y[len(y) - 1]
        cr_min = cr[0]
        cr_max = cr[len(cr) - 1]
        cb_min = cb[0]
        cb_max = cb[len(cb) - 1]
        self._ret = {
            "blur": self._blur,
            "exposure": self._exposure,
            "y_min": y_min,
            "y_max": y_max,
            "cr_min": cr_min,
            "cr_max": cr_max,
            "cb_min": cb_min,
            "cb_max": cb_max,
        }
