from asyncio import sleep, create_task, run, Task
from queue import Queue
from threading import Thread
from typing import Optional

import cv2.cv2 as cv2
import numpy as np

from symbol_detector.core import FilterProperty, filter_image, get_center, copy_drawing, draw_lines, \
    resize_to_standard, ceil_blur, compare_cos
from symbol_detector.settings import config


class BaseWorker:
    def __init__(self):
        self._running = False
        self._finished = True
        self._task: Optional[Task] = None

    def loop_start(self, *args, **kwargs):
        if self._running or not self._finished:
            return
        self._running = True
        self._finished = False
        coroutine = self.run(*args, **kwargs)

        try:
            self._task = create_task(coroutine)
        except RuntimeError:
            Thread(target=run, kwargs={'main': coroutine}).start()

    def loop_stop(self):
        self._running = False

    def run_end(self):
        self._finished = True

    @property
    def running(self):
        return self._running

    async def run(self, *args, **kwargs):
        raise NotImplementedError


class FrameProcessor(BaseWorker):
    _cam = None
    shape = None
    """ Recording the pointer's x,y coordinates, forwarding the movement's path """

    def __init__(self, callback_detect, out_queue: Queue = None):
        super().__init__()
        self._callback_detect = callback_detect
        self._out_queue = out_queue
        self._filter_property = FilterProperty(
            y_min=config.y_min,
            y_max=config.y_max,
            cb_min=config.cb_min,
            cb_max=config.cb_max,
            cr_min=config.cr_min,
            cr_max=config.cr_max,
            blur=config.blur,
        )
        self._NBREAK = 10
        self._points = list()
        self._n_break = 0
        self._sleep_time = 0.025
        self._i = 0

    @staticmethod
    def init_camera():
        FrameProcessor._cam = cv2.VideoCapture(config.camera_driver)
        FrameProcessor._cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        FrameProcessor._cam.set(cv2.CAP_PROP_EXPOSURE, config.camera_exposure)
        FrameProcessor._cam.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera_width)
        FrameProcessor._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera_height)
        ret, frame = FrameProcessor._cam.read()
        FrameProcessor.shape = frame.shape

    @staticmethod
    def release_camera():
        if FrameProcessor._cam.isOpened():
            FrameProcessor._cam.release()

    async def run(self):
        self._filter_property.load_from_settings(config)
        self.init_camera()
        while self.running and self._cam.isOpened():
            point = await self.capture_point()

            if not point[0] and self._sleep_time == 0.025:
                self._i += 1
                if self._i == 200:
                    self._sleep_time = 0.2
            elif point[0]:
                self._i = 0
                self._sleep_time = 0.025

            await self.analyze_point(point)
            await sleep(self._sleep_time)
        self.release_camera()
        self.run_end()

    async def capture_point(self):
        is_point = False
        point = 0
        ret, frame = self._cam.read()
        thresh = await filter_image(frame, self._filter_property)
        mask = thresh > 0

        if self._out_queue:
            out = cv2.flip(frame, 1)
            out[:, :, 0] *= mask
            out[:, :, 1] *= mask
            out[:, :, 2] *= mask
            out = cv2.cvtColor(out, cv2.COLOR_BGR2RGBA)
            self._out_queue.put(out)

        cnts, hier = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        for i in range(len(cnts)):
            area = cv2.contourArea(cnts[i])
            if (area > config.area_min) & (area < config.area_max):
                point = await get_center(cnts[i])
                is_point = True
        return is_point, point

    async def analyze_point(self, point):
        if not point[0] and len(self._points) > 3:
            self._n_break += 1
            if self._n_break == self._NBREAK:
                _ = create_task(self._callback_detect(self._points))
                self._points = list()
                self._n_break = 0
        elif point[0]:
            self._points.append(point[1])


class ShapeDetector:
    """Recognition of shapes"""

    def __init__(
        self,
        symbols,
        image_size,
        im_shape,
        ref_queue: Queue = None,
        result_queue: Queue = None,
        callback=None,
    ):
        super().__init__()
        self._im_shape = im_shape
        self._callback = callback
        self._ref_queue = ref_queue
        self._result_queue = result_queue
        self.symbols = symbols
        self.image_size = image_size
        self.max_diff = (float(image_size) ** 2.0) * 255.0
        self.current_image = None
        self._running = False

    def save_actual(self, filename):
        im = copy_drawing(self.current_image)
        cv2.imwrite(filename, im)

    async def process(self, points):
        if len(points) < 3:
            return
        gray_image = np.zeros([self._im_shape[0], self._im_shape[1]], np.uint8)
        await draw_lines(gray_image, points, 1)
        self.current_image = gray_image.copy()
        gray_image = resize_to_standard(gray_image, self.image_size)
        gray_image = ceil_blur(gray_image, 15, 3)
        typ, ref, diff = await compare_cos(gray_image, self.symbols)
        recognized = diff < config.max_rel_error
        if self._result_queue and recognized:
            im = np.zeros([ref.shape[0], ref.shape[1], 3], np.uint8)
            im[:, :, 1] = ref
            self._result_queue.put(im)
        elif self._result_queue and not recognized:
            im = np.zeros([ref.shape[0], ref.shape[1], 3], np.uint8)
            im[:, :, 0] = ref
            self._result_queue.put(im)
        if self._ref_queue:
            current_im = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2RGBA)
            self._ref_queue.put(current_im)
        if recognized:
            print(typ)
            if self._callback:
                _ = create_task(self._callback(typ))
