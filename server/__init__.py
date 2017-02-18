from http.server import HTTPServer, BaseHTTPRequestHandler, \
    SimpleHTTPRequestHandler
from io import BytesIO
from multiprocessing import Event
from multiprocessing.managers import Namespace

from .dataclasses import MJImage
from .socketutil import get_readable, get_writeable


class CaptureHTTPServer(HTTPServer):
    def __init__(self, addr, ns: Namespace, evt: Event, sh_evt: Event):
        super().__init__(addr, BaseHTTPRequestHandler)
        self.ns = ns
        self.evt = evt
        self.shutdown_event = sh_evt
        self.conns = []

    def process_request(self, req, client_addr):
        handler = CaptureHTTPHandler(req, client_addr, self)
        if handler.simple_request:
            # close request here
            self.shutdown_request(req)
        else:
            self.conns.append(handler)

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

        image = getattr(self.ns, 'image')  # type: MJImage
        pil = image.to_pil()
        io = BytesIO()
        pil.save(io, 'JPEG')

        buf = io.getvalue()
        l = len(buf)
        for handler in handlers:
            # noinspection PyBroadException
            try:
                handler.send_image(l, buf)
            except Exception:
                SimpleHTTPRequestHandler.finish(handler)
                self.handle_error(handler.request, handler.client_address)
                self.shutdown_request(handler.request)
                self.conns.remove(handler)


class CaptureHTTPHandler(SimpleHTTPRequestHandler):
    def __init__(self, req, client_addr, server):
        self.simple_request = True
        super().__init__(req, client_addr, server)

    def do_GET(self):
        if self.path != '/cam':
            return SimpleHTTPRequestHandler.do_GET(self)
        self.send_response(200)
        self.send_header('Content-type',
                         'multipart/x-mixed-replace; '
                         'boundary=--jpgboundary')
        self.end_headers()
        self.simple_request = False

    def fileno(self):
        return self.request.fileno()

    def send_image(self, size: int, io: bytes):
        if self.simple_request:
            return
        try:
            self.wfile.write(b"--jpgboundary")
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', size)
            self.end_headers()
            self.wfile.write(io)
        except (OSError, BrokenPipeError):
            pass

    def finish(self):
        if not self.simple_request:
            # if serving later, don't finish now!
            return
        super().finish()
