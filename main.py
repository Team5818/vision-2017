#!/usr/bin/env python3.6
from multiprocessing import Manager

from server import CaptureServer
from server.vision import start_vision_process
from server.visionproc import start_processing_process

PORT = 5800
COMMS_PORT = 5801


def main():
    manager = Manager()
    comms, evt, sh_evt = start_vision_process(manager)
    start_processing_process(comms, evt, sh_evt, COMMS_PORT)
    CaptureServer(('', PORT), comms, evt, sh_evt) \
        .serve_forever(poll_interval=0.005)


if __name__ == '__main__':
    main()
