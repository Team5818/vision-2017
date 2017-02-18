import multiprocessing as mp
import os
from multiprocessing import Event
from multiprocessing.managers import Namespace

import cv2
import serial

from ..dataclasses import Configuration, ConfigMode
from ..dataclasses import MJImage


def start_processing_process(ns: Namespace, evt: Event, sh_evt: Event):
    proc = mp.Process(target=processing_starter, args=(ns, evt, sh_evt))
    proc.start()


def processing_starter(ns: Namespace, evt: Event, sh_evt: Event):
    try:
        ser = serial.Serial(
            port='/dev/ttyAMA0',
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
        # just die, there's no good we can do here
        ser = None

    configurations = {
        ConfigMode.GEARS: Configuration((18, 100, 100), (35, 255, 255)),
        ConfigMode.TAPE: Configuration((60, 100, 70), (90, 255, 255))
    }

    if not evt.is_set():
        evt.wait()

    while not sh_evt.is_set():
        # noinspection PyBroadException
        try:
            active_cfg = getattr(ns, 'active_config')
            image = getattr(ns, 'image').array
            x_center = process_image(active_cfg, configurations[active_cfg],
                                     image)

            setattr(ns, 'processed_image', MJImage(image))

            if ser is not None:
                ser.flushOutput()
                ser.write("%+04d\n".format(int(x_center - 160)))
        except Exception:
            import traceback
            traceback.print_exc()

        # noinspection PyBroadException
        try:
            if ser is not None:
                if ser.inWaiting() > 0:
                    read = str(ser.read(1))
                    ser.flushInput()
                    if "s" in read:
                        sh_evt.set()
                        os.system("sudo shutdown -h now")
                    elif "q" in read:
                        sh_evt.set()
                    elif "l" in read:
                        os.system(
                            "v4l2-ctl -d /dev/video1 -c exposure_absolute=5")
                    elif "h" in read:
                        os.system(
                            "v4l2-ctl -d /dev/video1 -c exposure_absolute=156")
                    elif "t" in read:
                        setattr(ns, 'active_config', ConfigMode.TAPE)
                    elif "g" in read:
                        setattr(ns, 'active_config', ConfigMode.GEARS)
        except Exception:
            import traceback
            traceback.print_exc()


def process_image(cfg_id: ConfigMode, cfg: Configuration, image) -> int:
    # Grab frame
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Remove Small Particles
    mask = cv2.inRange(hsv, cfg.lower_thresh, cfg.upper_thresh)
    mask = cv2.erode(mask, None, iterations=1)
    mask = cv2.dilate(mask, None, iterations=2)

    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)[-2]
    if cfg_id == ConfigMode.TAPE:
        if len(cnts) > 0:
            x_center = 160
            cnts = sorted(cnts, key=cv2.contourArea)
            (x, y, w, h) = cv2.boundingRect(cnts[-1])
            if len(cnts) < 2:
                (x2, y2, w2, h2) = (0, 0, 0, 0)
            else:
                (x2, y2, w2, h2) = cv2.boundingRect(cnts[-2])
            if w * h > 50 and w2 * h2 > 50:
                cv2.rectangle(image, (int(min(x, x2)), int(max(y, y2))),
                              (int(max(x + w, x2 + w2)),
                               int(min(y + h, y2 + h2))), (0, 0, 255), 2)
                x_center = int((min(x, x2) + max(x + w, x2 + w2)) / 2)
                y_center = int((min(y, y2) + max(y + h, y2 + h2)) / 2)
                cv2.circle(image, (x_center, y_center), 3, (0, 0, 255), 2)
            elif max(w * h, w2 * h2) > 50:
                cv2.rectangle(image, (int(x), int(y)), (int(x + w), int(y + h)),
                              (0, 0, 255), 2)
                x_center = int(x + w / 2)
                y_center = int(y + h / 2)
                cv2.circle(image, (x_center, y_center), 3, (0, 0, 255), 2)
        else:
            x_center = 160
    else:
        if len(cnts) > 0:
            x_center = 160
            c = max(cnts, key=cv2.contourArea)
            if len(c) > 5:
                rect = cv2.minAreaRect(c)
                ((x, y), (w, h), ang) = rect
                if w * h > 100:
                    cv2.ellipse(image, rect, (0, 255, 255), 2)
                    cv2.circle(image, (int(x), int(y)), 3, (0, 255, 0), 2)
                    x_center = x
        else:
            x_center = 160

    return x_center
