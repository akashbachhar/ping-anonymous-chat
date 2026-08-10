"""Derive a v3 onion address locally from our ED25519 secret key.

The onion address is a pure function of the key, so we can compute it offline —
no running Tor, no waiting for publication. This lets the UI show the address
the instant the app starts, and guarantees the shown address always matches the
current key.

Contains a compact pure-Python ed25519 point multiplication (stdlib only) to
recover the public key from the expanded secret, then applies Tor's rend-spec-v3
address encoding:

    checksum = SHA3-256(".onion checksum" || pubkey || version)[:2]
    address  = base32(pubkey || checksum || version) + ".onion"
"""

import base64
import hashlib

# ---- ed25519 curve constants ----
_Q = 2 ** 255 - 19
_D = (-121665 * pow(121666, _Q - 2, _Q)) % _Q
_I = pow(2, (_Q - 1) // 4, _Q)


def _inv(x: int) -> int:
    return pow(x, _Q - 2, _Q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1)
    x = pow(xx, (_Q + 3) // 8, _Q)
    if (x * x - xx) % _Q != 0:
        x = (x * _I) % _Q
    if x % 2 != 0:
        x = _Q - x
    return x


_BY = (4 * _inv(5)) % _Q
_BX = _xrecover(_BY)
_B = (_BX % _Q, _BY % _Q)  # base point


def _edwards_add(p, q):
    x1, y1 = p
    x2, y2 = q
    common = _D * x1 * x2 * y1 * y2 % _Q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + common) % _Q
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - common) % _Q
    return (x3 % _Q, y3 % _Q)


def _scalarmult(point, scalar: int):
    result = (0, 1)  # identity
    while scalar > 0:
        if scalar & 1:
            result = _edwards_add(result, point)
        point = _edwards_add(point, point)
        scalar >>= 1
    return result


def _encodepoint(point) -> bytes:
    x, y = point
    bits = [(y >> i) & 1 for i in range(255)] + [x & 1]
    return bytes(
        sum(bits[i * 8 + j] << j for j in range(8)) for i in range(32)
    )


def public_key(expanded_secret: bytes) -> bytes:
    """Return the 32-byte ed25519 public key for a 64-byte expanded secret.

    The first 32 bytes of the expanded secret are the (already clamped) scalar
    in little-endian form; the public key is that scalar times the base point.
    """
    scalar = int.from_bytes(expanded_secret[:32], "little")
    return _encodepoint(_scalarmult(_B, scalar))


_VERSION = b"\x03"


def onion_address(expanded_secret_b64: str) -> str:
    """Compute the ``<id>.onion`` address from a base64 expanded secret key."""
    expanded = base64.b64decode(expanded_secret_b64)
    pub = public_key(expanded)
    checksum = hashlib.sha3_256(b".onion checksum" + pub + _VERSION).digest()[:2]
    encoded = base64.b32encode(pub + checksum + _VERSION).decode("ascii").lower()
    return f"{encoded}.onion"
