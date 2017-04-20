from unittest import TestCase

from google.protobuf.internal.well_known_types import Any
from google.protobuf.message import Message

from ..protos import Signal, SimplePacket


class PacketTests(TestCase):
    def test_round_trip(self):
        sig = Signal(type=Signal.SWITCH_FEED)

        p = SimplePacket()
        a = p.message  # type: Any
        a.Pack(sig)
        b = p.SerializeToString()

        p_unpacked = SimplePacket()  # type: Message
        p_unpacked.ParseFromString(b)

        a = getattr(p_unpacked, 'message')  # type: Any
        sig_up = Signal()
        a.Unpack(sig_up)
        self.assertEqual(sig_up.type, sig.type)
