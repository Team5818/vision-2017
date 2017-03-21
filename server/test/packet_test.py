from unittest import TestCase

from ..packet import Packet
from ..protos.packet_pb2 import Signal


class PacketTests(TestCase):
    def test_round_trip(self):
        sig = Signal()
        sig.type = Signal.SWITCH_FEED
        p = Packet(Signal())
        self.assertEqual(p.msg_id, 0)
        b = p.to_bytes()
        p_unpacked = Packet.from_bytes(b)
        self.assertEqual(p_unpacked.msg.type, sig.type)
