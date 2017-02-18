from typing import Tuple

import cv2
from PIL import Image
from enum import Enum, auto


class ConfigMode(Enum):
    GEARS = auto()
    TAPE = auto()


class Configuration:
    def __init__(self, cam_id: int, lower_thresh: Tuple[int, int, int],
                 upper_thresh: Tuple[int, int, int]):
        self.id = cam_id
        self.lower_thresh = lower_thresh
        self.upper_thresh = upper_thresh

        self.camera = cv2.VideoCapture(cam_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)


class MJImage:
    def __init__(self, cv2_img):
        self.rgb_array = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)

    def to_pil(self):
        return Image.fromarray(self.rgb_array)
