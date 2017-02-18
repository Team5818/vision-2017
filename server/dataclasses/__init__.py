from enum import Enum, auto
from typing import Tuple

import cv2
from PIL import Image


class ConfigMode(Enum):
    GEARS = auto()
    TAPE = auto()


class Configuration:
    def __init__(self, lower_thresh: Tuple[int, int, int],
                 upper_thresh: Tuple[int, int, int]):
        self.lower_thresh = lower_thresh
        self.upper_thresh = upper_thresh


class MJImage:
    def __init__(self, cv2_img):
        self.array = cv2_img

    def to_pil(self):
        return Image.fromarray(cv2.cvtColor(self.array, cv2.COLOR_BGR2RGB))
