# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: packet.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='packet.proto',
  package='',
  syntax='proto3',
  serialized_pb=_b('\n\x0cpacket.proto\"M\n\x06Signal\x12\x1a\n\x04type\x18\x01 \x01(\x0e\x32\x0c.Signal.Type\"\'\n\x04Type\x12\x0f\n\x0bSWITCH_FEED\x10\x00\x12\x0e\n\nDISCONNECT\x10\x01\"R\n\x0c\x46rameRequest\x12 \n\x04type\x18\x01 \x01(\x0e\x32\x12.FrameRequest.Type\" \n\x04Type\x12\t\n\x05PLAIN\x10\x00\x12\r\n\tPROCESSED\x10\x01\"\x15\n\x05\x46rame\x12\x0c\n\x04jpeg\x18\x01 \x01(\x0c\x62\x06proto3')
)
_sym_db.RegisterFileDescriptor(DESCRIPTOR)



_SIGNAL_TYPE = _descriptor.EnumDescriptor(
  name='Type',
  full_name='Signal.Type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='SWITCH_FEED', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='DISCONNECT', index=1, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=54,
  serialized_end=93,
)
_sym_db.RegisterEnumDescriptor(_SIGNAL_TYPE)

_FRAMEREQUEST_TYPE = _descriptor.EnumDescriptor(
  name='Type',
  full_name='FrameRequest.Type',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='PLAIN', index=0, number=0,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='PROCESSED', index=1, number=1,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=145,
  serialized_end=177,
)
_sym_db.RegisterEnumDescriptor(_FRAMEREQUEST_TYPE)


_SIGNAL = _descriptor.Descriptor(
  name='Signal',
  full_name='Signal',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='Signal.type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _SIGNAL_TYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=16,
  serialized_end=93,
)


_FRAMEREQUEST = _descriptor.Descriptor(
  name='FrameRequest',
  full_name='FrameRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='FrameRequest.type', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _FRAMEREQUEST_TYPE,
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=95,
  serialized_end=177,
)


_FRAME = _descriptor.Descriptor(
  name='Frame',
  full_name='Frame',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='jpeg', full_name='Frame.jpeg', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=179,
  serialized_end=200,
)

_SIGNAL.fields_by_name['type'].enum_type = _SIGNAL_TYPE
_SIGNAL_TYPE.containing_type = _SIGNAL
_FRAMEREQUEST.fields_by_name['type'].enum_type = _FRAMEREQUEST_TYPE
_FRAMEREQUEST_TYPE.containing_type = _FRAMEREQUEST
DESCRIPTOR.message_types_by_name['Signal'] = _SIGNAL
DESCRIPTOR.message_types_by_name['FrameRequest'] = _FRAMEREQUEST
DESCRIPTOR.message_types_by_name['Frame'] = _FRAME

Signal = _reflection.GeneratedProtocolMessageType('Signal', (_message.Message,), dict(
  DESCRIPTOR = _SIGNAL,
  __module__ = 'packet_pb2'
  # @@protoc_insertion_point(class_scope:Signal)
  ))
_sym_db.RegisterMessage(Signal)

FrameRequest = _reflection.GeneratedProtocolMessageType('FrameRequest', (_message.Message,), dict(
  DESCRIPTOR = _FRAMEREQUEST,
  __module__ = 'packet_pb2'
  # @@protoc_insertion_point(class_scope:FrameRequest)
  ))
_sym_db.RegisterMessage(FrameRequest)

Frame = _reflection.GeneratedProtocolMessageType('Frame', (_message.Message,), dict(
  DESCRIPTOR = _FRAME,
  __module__ = 'packet_pb2'
  # @@protoc_insertion_point(class_scope:Frame)
  ))
_sym_db.RegisterMessage(Frame)


# @@protoc_insertion_point(module_scope)