from queue import Queue

from settings import IMAGE_SIZE
from workers import FrameProcessor, ShapeDetector


class Detector:
    def __init__(self, symbols, gui=True, callback=None):
        FrameProcessor.init_camera()

        self._gui = gui

        if self._gui:
            self.ref_queue = Queue()
            self.thresh_queue = Queue()
            self.result_queue = Queue()
        else:
            self.ref_queue = None
            self.thresh_queue = None
            self.result_queue = None

        self._shape_detector = ShapeDetector(
            symbols,
            IMAGE_SIZE,
            FrameProcessor.shape,
            self.ref_queue,
            self.result_queue,
            callback,
        )
        self._frame_handler = FrameProcessor(
            self._shape_detector.process, self.thresh_queue
        )

        FrameProcessor.release_camera()

    def save_im(self, filename: str):
        self._shape_detector.save_actual(filename)

    def loop_start(self):
        # manager.loop_start()
        self._frame_handler.loop_start()

    def loop_stop(self):
        self._frame_handler.loop_stop()
        # manager.loop_stop()
