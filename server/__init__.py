import zlib
from enum import Enum, auto
from io import BytesIO
from multiprocessing import Event
from multiprocessing.managers import Namespace
from socket import socket
from socketserver import TCPServer, BaseRequestHandler
from typing import List

from google.protobuf.internal.well_known_types import Any
from google.protobuf.message import Message

from .dataclasses import ConfigMode
from .dataclasses import MJImage
from .protos import Signal, Frame, SetFrameType, SimplePacket
from .socketutil import get_readable, get_writeable, read_bytes, write_bytes


class FrameType(Enum):
    PLAIN = auto()
    PROCESSED = auto()


class CaptureServer(TCPServer):
    allow_reuse_address = True

    def __init__(self, addr, ns: Namespace, evt: Event, sh_evt: Event):
        super().__init__(addr, BaseRequestHandler)
        self.ns = ns
        self.evt = evt
        self.shutdown_event = sh_evt
        self.conns: List['CaptureHandler'] = []

        self._loop_reg_image: Frame = None
        self._loop_proc_image: Frame = None

    def process_request(self, req, client_addr):
        # noinspection PyBroadException
        try:
            handler = CaptureHandler(req, client_addr, self)
            print('add', client_addr)
            self.conns.append(handler)
        except Exception:
            self.handle_error(req, client_addr)
            self.shutdown_request(req)

    def service_actions(self):
        self._loop_reg_image = None
        self._loop_proc_image = None
        # die if shutdown
        if self.shutdown_event.is_set():
            raise Exception("Shutdown requested!")
        # wait for ns.image to appear
        if not self.evt.is_set():
            self.evt.wait()
        handlers = list(self.conns)
        if not handlers:
            return

        for handler in handlers:
            # noinspection PyBroadException
            try:
                handler.handle_message()
            except Exception:
                try:
                    handler.close()
                finally:
                    self.handle_error(handler.request, handler.client_addr)
                    self.shutdown_request(handler.request)
                    if handler in self.conns:
                        self.conns.remove(handler)
            finally:
                if handler.done:
                    self.shutdown_request(handler.request)
                    if handler in self.conns:
                        self.conns.remove(handler)

    def get_frame(self, ftype: FrameType) -> Frame:
        """
        Docs to get pycharm to shut up and stop being dumb...
        :rtype: Frame
        """
        if ftype == FrameType.PLAIN:
            if self._loop_reg_image is None:
                self._loop_reg_image = self._get_frame('image')
            return self._loop_reg_image

        elif ftype == FrameType.PROCESSED:
            if self._loop_proc_image is None:
                self._loop_proc_image = self._get_frame('processed_image')
            return self._loop_proc_image

        else:
            raise ValueError('unhandled type ' + str(type))

    def _get_frame(self, name: str) -> Frame:
        l, buf = self.get_jpeg(name)
        zcomp = zlib.compress(buf)
        frame = Frame()
        frame.jpeg = zcomp
        return frame

    def get_jpeg(self, attr_name: str):
        image = getattr(self.ns, attr_name)  # type: MJImage
        pil = image.to_pil()
        io = BytesIO()
        pil.save(io, 'JPEG')

        buf = io.getvalue()
        l = len(buf)
        return l, buf


class CaptureHandler:
    def __init__(self, req: socket, client_addr, server: CaptureServer):
        self.request = req
        self.client_addr = client_addr
        self.server = server
        self.frame_type = FrameType.PLAIN
        self.done = False

    def fileno(self):
        return self.request.fileno()

    def handle_message(self):
        # always send frames!
        self.send_frame()

        if len(get_readable([self])) == 0:
            return

        packet = SimplePacket()  # type: Message
        packet_bytes = read_bytes(self.request)
        packet.ParseFromString(packet_bytes)

        any_val = getattr(packet, 'message')  # type: Any

        if any_val.Is(Signal.DESCRIPTOR):
            sig = Signal()
            any_val.Unpack(sig)

            sig = sig.type
            if sig == Signal.SWITCH_FEED:
                cm = getattr(self.server.ns, 'active_config', ConfigMode.GEARS)
                if cm == ConfigMode.GEARS:
                    setattr(self.server.ns, 'active_config', ConfigMode.TAPE)
                elif cm == ConfigMode.TAPE:
                    setattr(self.server.ns, 'active_config', ConfigMode.GEARS)
            elif sig == Signal.DISCONNECT:
                self.close()
        elif any_val.Is(SetFrameType.DESCRIPTOR):
            fr = SetFrameType()
            any_val.Unpack(fr)

            self.frame_type = FrameType[SetFrameType.Type.Name(fr.type)]
        else:
            raise ValueError('Unhandled message ' + repr(any_val))

    def send_frame(self):
        frame = self.server.get_frame(self.frame_type)

        sp = SimplePacket()
        sp.message.Pack(frame)

        write_bytes(self.request, sp.SerializeToString())

    def close(self):
        self.done = True
