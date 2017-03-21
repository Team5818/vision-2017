import struct
from functools import lru_cache
from io import BytesIO, RawIOBase
from typing import Union

from google.protobuf.message import Message

from .protos.packet_pb2 import Frame, FrameRequest, Signal

MESSAGE_TO_ID = {cls: x for x, cls in
                 enumerate([Signal, FrameRequest, Frame])}
ID_TO_MESSAGE = {x: cls for cls, x in MESSAGE_TO_ID.items()}


def _read_bytes(b: RawIOBase, count: int) -> bytes:
    barr = bytearray(count)
    view = memoryview(barr)
    while count:
        nbytes = b.readinto(view)
        if nbytes == 0:
            raise EOFError()

        view = view[nbytes:]
        count -= nbytes
    return bytes(barr)


class Packet:
    @classmethod
    def from_bytes(cls, b: Union[bytes, RawIOBase]) -> 'Packet':
        if isinstance(b, bytes):
            b = BytesIO(b)
        packet_data = _read_bytes(b, 5)
        msg_id, length = struct.unpack('>BI', packet_data)
        data = _read_bytes(b, length)
        if msg_id not in ID_TO_MESSAGE:
            raise ValueError(f'Unknown msg_id {msg_id}')
        message: Message = ID_TO_MESSAGE[msg_id]()
        message.ParseFromString(data)
        return cls(message)

    def __init__(self, message: Message):
        self.msg = message
        msg_type = type(message)
        if msg_type not in MESSAGE_TO_ID:
            raise ValueError(f'Unknown message type {msg_type}')
        self.msg_id = MESSAGE_TO_ID[msg_type]

    # cache result since we're "immutable"...
    @lru_cache(None)
    def to_bytes(self) -> bytes:
        data = self.msg.SerializeToString()
        return struct.pack('>BI', self.msg_id, len(data)) + data
