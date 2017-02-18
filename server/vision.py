import multiprocessing as mp
import os
import time
from multiprocessing import Event
from multiprocessing.managers import Namespace, SyncManager
from typing import Optional, Tuple

import serial

from .dataclasses import Configuration, ConfigMode, MJImage
from .visionproc import process_image


def start_vision_process(manager: SyncManager) -> \
        Tuple[Namespace, Event, Event]:
    ns = manager.Namespace()
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

        try:
            self.serial = serial.Serial(
                port='/dev/ttyS0',
                baudrate=9600,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=0,
                writeTimeout=0,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
        except serial.SerialException as e:
            print('Ignoring serial exception', e.args[0])
            self.serial = None

        self.configurations = {
            ConfigMode.GEARS: Configuration(0, (18, 100, 100), (35, 255, 255)),
            ConfigMode.TAPE: Configuration(1, (60, 100, 70), (90, 255, 255))
        }
        self.active_config = ConfigMode.GEARS

    @property
    def configuration(self) -> Configuration:
        return self.configurations[self.active_config]

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
            # noinspection PyBroadException
            try:
                self.handle_serial()
            except Exception:
                import traceback
                traceback.print_exc()
            time.sleep(0.05)

    def get_vision_frame(self) -> Optional[MJImage]:
        cfg = self.configuration
        rc, image = cfg.camera.read()
        if not rc:
            return None

        x_center = process_image(self.active_config, cfg, image)
        if self.serial is not None:
            self.serial.flushOutput()
            self.serial.write("%+04d\n".format(int(x_center - 160)))

        return MJImage(image)

    def send_vision_frame(self, frame: MJImage):
        self.ns.image = frame

        if not getattr(self.ns, '_evt_set', False):
            self.evt.set()
            setattr(self.ns, '_evt_set', True)

    def handle_serial(self):
        ser = self.serial

        if ser is None:
            return

        if self.serial.inWaiting() > 0:
            read = str(ser.read(1))
            ser.flushInput()
            if "s" in read:
                self.shutdown_evt.set()
                os.system("sudo shutdown -h now")
            elif "q" in read:
                self.shutdown_evt.set()
            elif "l" in read:
                os.system("v4l2-ctl -d /dev/video1 -c exposure_absolute=5")
            elif "h" in read:
                os.system("v4l2-ctl -d /dev/video1 -c exposure_absolute=156")
            elif "t" in read:
                self.active_config = ConfigMode.TAPE
            elif "g" in read:
                self.active_config = ConfigMode.GEARS
