import multiprocessing as mp
import os
from collections import deque
from multiprocessing import Event
from multiprocessing.managers import Namespace
from socket import socket
from socketserver import TCPServer, BaseRequestHandler
from typing import Tuple

import cv2
import serial

from ..dataclasses import Configuration, ConfigMode
from ..dataclasses import MJImage
from ..socketutil import read_bytes, write_bytes, get_readable

CAM0_SET = "v4l2-ctl -d /dev/video0 -c "
CAM1_SET = "v4l2-ctl -d /dev/video1 -c "

LOW_EXPOSURE = 10
HIGH_EXPOSURE = 156

NO_VISION = 254

ns = None
sh_evt = None


def handle_command_global(read: str):
    global sh_evt, ns

    if "s" in read and sh_evt is not None:
        sh_evt.set()
        os.system("sudo shutdown -h now")
    elif "q" in read and sh_evt is not None:
        sh_evt.set()
    elif "l" in read:
        os.system(
            f"{CAM1_SET} exposure_absolute={LOW_EXPOSURE}")
    elif "h" in read:
        os.system(
            f"{CAM1_SET} exposure_absolute={HIGH_EXPOSURE}")
    elif "t" in read:
        setattr(ns, 'active_config', ConfigMode.TAPE)
    elif "g" in read:
        setattr(ns, 'active_config', ConfigMode.GEARS)


class Comm:
    def __init__(self, request: socket, client_addr: str):
        self.request = request
        self.client_addr = client_addr
        self.comm_queue = deque()
        self._need_frame = False
        self._frame = None

    def read_next_command(self):
        if get_readable([self.request]):
            # read command
            cmd = read_bytes(self.request).decode('utf-8')
            if cmd == 'send_frame':
                if self._frame is not None:
                    write_bytes(self.request, self._frame)
                else:
                    self._need_frame = True
            else:
                self.comm_queue.append(cmd)

            return True
        return False

    def has_command(self):
        return len(self.comm_queue) > 0

    def next_command(self):
        return self.comm_queue.popleft()

    def set_frame(self, frame: bytes):
        self._frame = frame
        if self._need_frame:
            self.request.sendall(frame)
            self._need_frame = False


class Server(TCPServer):
    timeout = 0

    def __init__(self, port: int):
        super().__init__(('', port), BaseRequestHandler)
        self.active_comm: Comm = None

    def process_request(self, request, client_address):
        self._shutdown_active_comm()
        self.active_comm = Comm(request, client_address)

    def service_actions(self):
        if self.active_comm is None:
            return

        try:
            while self.active_comm.read_next_command():
                pass

            while self.active_comm.has_command():
                cmd = self.active_comm.next_command()
                handle_command_global(cmd)
        except EOFError:
            self._shutdown_active_comm()

    def _shutdown_active_comm(self):
        if self.active_comm is not None:
            self.shutdown_request(self.active_comm.request)
            self.active_comm = None


def start_processing_process(namespace: Namespace, evt: Event,
                             shutdown_event: Event, port: int):
    proc = mp.Process(target=processing_starter,
                      args=(namespace, evt, shutdown_event, port))
    proc.start()


def processing_starter(namespace: Namespace, evt: Event, shutdown_evt: Event,
                       port: int):
    global ns, sh_evt
    ns = namespace
    sh_evt = shutdown_evt
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
        ser = None
    try:
        server = Server(port)
    except Exception as e:
        print('Ignoring server init exception', e.args[0])
        server = None

    configurations = {
        ConfigMode.GEARS: Configuration((18, 100, 100), (35, 255, 255)),
        ConfigMode.TAPE: Configuration((60, 50, 70), (90, 255, 255))
    }

    # le camera setup
    os.system(f"{CAM0_SET} exposure_auto=1")
    os.system(f"{CAM1_SET} exposure_auto=1")
    os.system(f"{CAM0_SET} exposure_absolute={HIGH_EXPOSURE}")
    os.system(f"{CAM1_SET} exposure_absolute={LOW_EXPOSURE}")

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

            if x_center is not None:
                x_center -= 160
            else:
                x_center = NO_VISION

            x_center_bytes = f"{int(x_center):+04d}".encode('utf-8')

            if server is not None:
                ready = get_readable([server])
                if ready:
                    server.handle_request()

                if server.active_comm is not None:
                    server.active_comm.set_frame(x_center_bytes)
                server.service_actions()

            if ser is not None:
                ser.flushOutput()
                ser.write(x_center_bytes)
                ser.write(b'\n')
        except Exception:
            import traceback
            traceback.print_exc()

        # noinspection PyBroadException
        try:
            if ser is not None:
                if ser.inWaiting() > 0:
                    read = str(ser.read(1))
                    ser.flushInput()
                    handle_command_global(read)
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
            x_center = None
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
            x_center = None
    else:
        if len(cnts) > 0:
            x_center = None
            c = max(cnts, key=cv2.contourArea)
            if len(c) > 5:
                rect = cv2.minAreaRect(c)
                ((x, y), (w, h), ang) = rect
                if w * h > 100:
                    cv2.ellipse(image, rect, (0, 255, 255), 2)
                    cv2.circle(image, (int(x), int(y)), 3, (0, 255, 0), 2)
                    x_center = x
        else:
            x_center = None

    return x_center
