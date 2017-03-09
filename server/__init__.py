from enum import Enum, auto
from http.server import HTTPServer, BaseHTTPRequestHandler, \
    SimpleHTTPRequestHandler
from io import BytesIO
from multiprocessing import Event
from multiprocessing.managers import Namespace

from .dataclasses import ConfigMode, MJImage
from .socketutil import get_readable, get_writeable


class RequestType(Enum):
    SIMPLE = auto()
    PLAIN = auto()
    PROCESSED = auto()


class CaptureHTTPServer(HTTPServer):
    def __init__(self, addr, ns: Namespace, evt: Event, sh_evt: Event):
        super().__init__(addr, BaseHTTPRequestHandler)
        self.ns = ns
        self.evt = evt
        self.shutdown_event = sh_evt
        self.conns = []

    def process_request(self, req, client_addr):
        # noinspection PyBroadException
        try:
            handler = CaptureHTTPHandler(req, client_addr, self)
            if handler.request_type == RequestType.SIMPLE:
                # close request here
                print('close', getattr(handler, 'path', client_addr))
                self.shutdown_request(req)
            else:
                print('add', handler.path, 'from', client_addr)
                self.conns.append(handler)
        except Exception:
            self.handle_error(req, client_addr)
            self.shutdown_request(req)

    def service_actions(self):
        # die if shutdown
        if self.shutdown_event.is_set():
            raise Exception("Shutdown requested!")
        # wait for ns.image to appear
        if not self.evt.is_set():
            self.evt.wait()
        # process any requests running using select
        handlers = get_writeable(self.conns)
        if not handlers:
            return

        regular_image = None
        processed_image = None
        if any(x.request_type == RequestType.PLAIN for x in handlers):
            regular_image = self.get_jpeg('image')
        if any(x.request_type == RequestType.PROCESSED for x in handlers):
            processed_image = self.get_jpeg('processed_image')

        for handler in handlers:
            # noinspection PyBroadException
            try:
                if handler.request_type == RequestType.PLAIN:
                    assert regular_image is not None
                    handler.send_image(*regular_image)
                elif handler.request_type == RequestType.PROCESSED:
                    assert processed_image is not None
                    handler.send_image(*processed_image)
            except Exception:
                SimpleHTTPRequestHandler.finish(handler)
                self.handle_error(handler.request, handler.client_address)
                self.shutdown_request(handler.request)
                self.conns.remove(handler)
            finally:
                if handler.done:
                    self.shutdown_request(handler.request)
                    self.conns.remove(handler)

    def get_jpeg(self, attr_name: str):
        image = getattr(self.ns, attr_name)  # type: MJImage
        pil = image.to_pil()
        io = BytesIO()
        pil.save(io, 'JPEG')

        buf = io.getvalue()
        l = len(buf)
        return l, buf


class CaptureHTTPHandler(SimpleHTTPRequestHandler):
    timeout = 0.1

    def __init__(self, req, client_addr, server):
        self.request_type = RequestType.SIMPLE
        self.done = False
        super().__init__(req, client_addr, server)

    def do_GET(self):
        if self.path not in ('/cam', '/cam-proc'):
            if self.path == '/feed-change':
                cm = getattr(self.server.ns, 'active_config', ConfigMode.GEARS)
                if cm == ConfigMode.GEARS:
                    setattr(self.server.ns, 'active_config', ConfigMode.TAPE)
                elif cm == ConfigMode.TAPE:
                    setattr(self.server.ns, 'active_config', ConfigMode.GEARS)
                return
            return SimpleHTTPRequestHandler.do_GET(self)
        self.send_response(200)
        self.send_header('Content-type',
                         'multipart/x-mixed-replace; '
                         'boundary=--jpgboundary')
        self.end_headers()
        if self.path == '/cam-proc':
            self.request_type = RequestType.PROCESSED
        elif self.path == '/cam':
            self.request_type = RequestType.PLAIN

    def fileno(self):
        return self.request.fileno()

    def send_image(self, size: int, io: bytes):
        if self.request_type == RequestType.SIMPLE:
            return
        try:
            self.wfile.write(b"--jpgboundary")
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', size)
            self.end_headers()
            self.wfile.write(io)
            self.wfile.flush()
        except (OSError, BrokenPipeError, ValueError):
            self.request_type = None
            self.finish()

    def finish(self):
        if self.request_type is None or self.request_type != RequestType.SIMPLE:
            # if serving later, don't finish now!
            return
        self.done = True
        super().finish()
