import os

from datek_utils.da_config import Config, Option

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
FILE = os.path.join(BASE_DIR, "settings.ini")
IMAGE_SIZE = 150
SYMBOLS_DIR = "syms"
PAD_X = 5
PAD_Y = 5


class Settings(Config):
    y_min = Option("filtering parameters", "y min", int, 0)
    y_max = Option("filtering parameters", "y max", int, 0)
    cb_min = Option("filtering parameters", "cb min", int, 0)
    cb_max = Option("filtering parameters", "cb max", int, 0)
    cr_min = Option("filtering parameters", "cr min", int, 0)
    cr_max = Option("filtering parameters", "cr max", int, 0)
    area_max = Option("filtering parameters", "area max", int, 0)
    area_min = Option("filtering parameters", "area min", int, 0)
    blur = Option("filtering parameters", "blur", int, 0)
    camera_driver = Option("camera", "driver", fallback="/dev/video0")
    camera_exposure = Option("camera", "exposure", int, 0)
    camera_width = Option("camera", "width", int, 800)
    camera_height = Option("camera", "height", int, 600)
    max_rel_error = Option("detecting options", "maximum relative error", float, 20.0)
    symbol_set = Option("detecting options", "symbol set")


settings = Settings(FILE)
