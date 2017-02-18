import struct
import time
from select import select
from socket import socket, timeout

from typing import List, TypeVar


def write_bytes(sock: socket, b: bytes):
    sock.sendall(struct.pack('>I', len(b)) + b)


def read_bytes(sock: socket) -> bytes:
    length = struct.unpack('>I', read_or_eof(sock, 4))[0]
    return read_or_eof(sock, length)


def read_or_eof(sock: socket, count: int) -> bytes:
    b = bytearray(count)
    view = memoryview(b)
    while count:
        nbytes = sock.recv_into(view, count)
        if nbytes == 0:
            raise EOFError()

        view = view[nbytes:]
        count -= nbytes
    return bytes(b)


def wait_for_data(sock: socket, data: bytes, read_timeout: int = 0):
    time_limit = time.monotonic() + read_timeout
    rlist = [sock]
    data_to_go = memoryview(data)
    while time_limit > time.monotonic() and len(data_to_go) > 0:
        readable = get_readable(rlist)
        if not readable:
            time.sleep(0.01)
            continue

        try:
            data_in = sock.recv(len(data_to_go))
        except timeout:
            continue

        if len(data_in) == 0:
            raise EOFError()

        to_go_slice = data_to_go[:len(data_in)]
        if data_in != to_go_slice:
            raise ValueError(
                "Expected " + repr(to_go_slice) + ", got " + repr(data_in))

        data_to_go = data_to_go[len(data_in):]

    if time_limit < time.monotonic():
        raise TimeoutError()


T = TypeVar('T')


def get_readable(sockets: List[T]) -> List[T]:
    if not sockets:
        return []

    return select(sockets, (), (), 0)[0]


def get_writeable(sockets: List[T]) -> List[T]:
    if not sockets:
        return []

    return select((), sockets, (), 0)[1]
