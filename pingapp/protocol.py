"""Wire protocol for chat messages and file transfers.

TCP is a byte stream with no message boundaries, so every frame is length-
prefixed with a 4-byte big-endian header. The first payload byte is a type tag
so the receiver can tell text from a file:

    text frame:  [4B length][0x00][utf-8 text]
    file frame:  [4B length][0x01][2B name-len][utf-8 name][raw file bytes]

Both peers (GUI and CLI) must run this same protocol.
"""

import struct

_HEADER = struct.Struct(">I")   # frame length
_NAME = struct.Struct(">H")     # filename length inside a file frame

TYPE_TEXT = 0x00
TYPE_FILE = 0x01

FILE_SIZE_LIMIT = 5 * 1024 * 1024              # 5 MiB cap on a transferred file
MAX_MESSAGE = FILE_SIZE_LIMIT + 64 * 1024      # frame cap (file + type + name)


class Message:
    """A decoded frame: either kind == 'text' or kind == 'file'."""

    __slots__ = ("kind", "text", "filename", "data")

    def __init__(self, kind, text=None, filename=None, data=None):
        self.kind = kind
        self.text = text
        self.filename = filename
        self.data = data


def encode_text(text: str) -> bytes:
    body = bytes([TYPE_TEXT]) + text.encode("utf-8")
    return _HEADER.pack(len(body)) + body


def encode_file(filename: str, data: bytes) -> bytes:
    name = filename.encode("utf-8")
    body = bytes([TYPE_FILE]) + _NAME.pack(len(name)) + name + data
    return _HEADER.pack(len(body)) + body


class StreamDecoder:
    """Accumulates raw socket bytes and yields complete :class:`Message` frames."""

    def __init__(self):
        self._buf = bytearray()

    def feed(self, data: bytes):
        self._buf.extend(data)
        messages = []
        while True:
            if len(self._buf) < _HEADER.size:
                break
            (length,) = _HEADER.unpack_from(self._buf, 0)
            if length > MAX_MESSAGE:
                raise ValueError("declared frame length exceeds limit")
            end = _HEADER.size + length
            if len(self._buf) < end:
                break
            payload = bytes(self._buf[_HEADER.size:end])
            del self._buf[:end]
            messages.append(self._parse(payload))
        return messages

    @staticmethod
    def _parse(payload: bytes) -> Message:
        if not payload:
            raise ValueError("empty frame")
        kind = payload[0]
        body = payload[1:]
        if kind == TYPE_TEXT:
            return Message("text", text=body.decode("utf-8", errors="replace"))
        if kind == TYPE_FILE:
            if len(body) < _NAME.size:
                raise ValueError("truncated file frame")
            (name_len,) = _NAME.unpack_from(body, 0)
            start = _NAME.size
            name = body[start:start + name_len].decode("utf-8", errors="replace")
            data = body[start + name_len:]
            return Message("file", filename=name, data=data)
        raise ValueError(f"unknown frame type {kind}")
