import multiprocessing as mp
import time
from multiprocessing import Event
from multiprocessing.managers import Namespace, SyncManager
from typing import Optional, Tuple

import cv2

from .dataclasses import ConfigMode, MJImage


def start_vision_process(manager: SyncManager) -> \
        Tuple[Namespace, Event, Event]:
    ns = manager.Namespace()
    # init ns
    setattr(ns, 'active_config', ConfigMode.GEARS)

    evt = manager.Event()
    sh_evt = manager.Event()
    proc = mp.Process(target=vision_starter, args=(ns, evt, sh_evt))
    proc.start()
    return ns, evt, sh_evt


def vision_starter(ns: Namespace, evt: Event, shutdown_evt: Event):
    VisionMain(ns, evt, shutdown_evt).run()


class VisionMain:
    def __init__(self, ns: Namespace, evt: Event, shutdown_evt: Event):
        self.ns = ns
        self.evt = evt
        self.shutdown_evt = shutdown_evt

        def new_cam(cam_id: int):
            camera = cv2.VideoCapture(cam_id)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            return camera

        self.cameras = {
            ConfigMode.GEARS: new_cam(0),
            ConfigMode.TAPE: new_cam(2)
        }

    @property
    def camera(self) -> cv2.VideoCapture:
        return self.cameras[getattr(self.ns, 'active_config')]

    def run(self):
        while not self.shutdown_evt.is_set():
            # noinspection PyBroadException
            try:
                frame = self.get_vision_frame()

                if frame is not None:
                    self.send_vision_frame(frame)
            except Exception:
                import traceback
                traceback.print_exc()
            time.sleep(0.01)

    def get_vision_frame(self) -> Optional[MJImage]:
        rc, image = self.camera.read()
        if not rc:
            return None

        return MJImage(image)

    def send_vision_frame(self, frame: MJImage):
        self.ns.image = frame

        if not getattr(self.ns, '_evt_set', False):
            self.evt.set()
            setattr(self.ns, '_evt_set', True)
