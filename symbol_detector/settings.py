import os
from json import loads, dumps
from pathlib import Path
from typing import Union
import numpy as np
from pydantic import BaseModel
from pydantic.fields import Field

from symbol_detector.constants import DEFAULT_CONFIG_PATH


class FilteringParametersAttribute:
    y_min: int
    y_max: int
    cb_min: int
    cb_max: int
    cr_min: int
    cr_max: int
    area_max: int
    area_min: int
    blur: int


FilteringParametersModel = type(
    "FilteringParametersModel",
    (BaseModel,),
    {
        "__annotations__": FilteringParametersAttribute.__annotations__
    }
)


class CameraAttribute:
    camera_driver: str
    camera_exposure: int
    camera_width: int
    camera_height: int


CameraModel = type(
    "CameraModel",
    (BaseModel,),
    {
        "__annotations__": CameraAttribute.__annotations__,
        "camera_driver": Field(alias="driver"),
        "camera_exposure": Field(alias="exposure"),
        "camera_width": Field(alias="width"),
        "camera_height": Field(alias="height"),
    },
)


class DetectingOptionsAttribute:
    max_rel_error: float
    symbol_set: str


DetectingOptionsModel = type(
    "DetectingOptionsModel",
    (BaseModel,),
    {"__annotations__": DetectingOptionsAttribute.__annotations__}
)


class SettingsModel(BaseModel):
    filtering_parameters: FilteringParametersModel
    camera: CameraModel
    detecting_options: DetectingOptionsModel


class Config(FilteringParametersAttribute, CameraAttribute, DetectingOptionsAttribute):
    def __init__(self, file: Union[Path, str]):
        self._file: Path = Path(file).resolve() if isinstance(file, str) else file
        self._model: SettingsModel = ...

    def load(self):
        text = self._file.read_text()
        self._model = SettingsModel(**loads(text))

    def save(self):
        data = self._model.dict(by_alias=True)
        json_ = dumps(data, default=_default, indent=2)
        self._file.write_text(json_)

    def __getattr__(self, item: str):
        if item.startswith("_"):
            return super().__getattribute__(item)

        model_name = self._get_model_name(item)
        model = getattr(self._model, model_name)
        return getattr(model, item)

    def __setattr__(self, key: str, value):
        if key.startswith("_"):
            return super().__setattr__(key, value)

        model_name = self._get_model_name(key)
        model = getattr(self._model, model_name)
        setattr(model, key, value)

    def _get_model_name(self, item: str) -> str:
        for base in self.__class__.__bases__:
            if item in base.__annotations__.keys():
                return _CLASS_MODEL_NAME_MAP[base]


def _default(obj):
    if isinstance(obj, np.uint8):
        return int(obj)

    return obj


_CLASS_MODEL_NAME_MAP = {
    FilteringParametersAttribute: "filtering_parameters",
    CameraAttribute: "camera",
    DetectingOptionsAttribute: "detecting_options",
}

config = Config(os.getenv("CONFIG_FILE_PATH", f"{DEFAULT_CONFIG_PATH}"))
