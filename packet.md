Wire Format for Vision Feed
====

Packet format, `<message>`s defined in `packet.proto`:

|Name  |Size (bytes)      |Description|
|------|------------------|-----------|
|`id`  |1 (unsigned byte) |Message ID, mapped to specific message types in code|
|`size`|4 (unsigned int)  |Size of the rest of the packet|
|`data`|`size`            |The data to deserialize to a message|
