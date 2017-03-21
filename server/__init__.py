import zlib
from enum import Enum, auto
from io import BytesIO
from multiprocessing import Event
from multiprocessing.managers import Namespace
from socket import socket
from socketserver import TCPServer, BaseRequestHandler
from typing import List

from .dataclasses import ConfigMode
from .dataclasses import MJImage
from .packet import Packet
from .protos import Signal, Frame, FrameRequest
from .socketutil import get_readable, get_writeable


class FrameType(Enum):
    PLAIN = auto()
    PROCESSED = auto()


class CaptureServer(TCPServer):
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
        # process any requests running using select
        handlers = get_readable(self.conns)
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
                    self.conns.remove(handler)
            finally:
                if handler.done:
                    self.shutdown_request(handler.request)
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
        self.done = False

        self.rfile = req.makefile('rb')
        self.wfile = req.makefile('wb')

    def fileno(self):
        return self.request.fileno()

    def handle_message(self):
        packet = Packet.from_bytes(self.rfile)
        if isinstance(packet.msg, Signal):
            sig = packet.msg.type
            if sig == Signal.SWITCH_FEED:
                cm = getattr(self.server.ns, 'active_config', ConfigMode.GEARS)
                if cm == ConfigMode.GEARS:
                    setattr(self.server.ns, 'active_config', ConfigMode.TAPE)
                elif cm == ConfigMode.TAPE:
                    setattr(self.server.ns, 'active_config', ConfigMode.GEARS)
            elif sig == Signal.DISCONNECT:
                self.close()
        elif isinstance(packet.msg, FrameRequest):
            frame_type = FrameType[FrameRequest.Type.Name(packet.msg.type)]

            frame = self.server.get_frame(frame_type)
            self.wfile.write(Packet(frame).to_bytes())
        else:
            raise ValueError('Unhandled message ' + str(packet.msg))

    def close(self):
        self.done = True
        try:
            self.rfile.close()
        finally:
            self.wfile.close()
