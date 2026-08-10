"""Persistent onion identity for a fixed address.

Instead of letting Tor generate the key, Ping owns the randomness: a single
32-byte seed is generated once with a CSPRNG and saved. On every launch the seed
is deterministically expanded into Tor's 64-byte ``ED25519-V3`` secret key, so
the onion service — and therefore the onion address — is identical every run.

The seed IS the identity: anyone holding it can impersonate the address, so it
is stored under the Tor data directory with owner-only permissions and is never
shown in the UI.
"""

import base64
import hashlib
import os
import secrets
import stat

from .onion_address import onion_address

SEED_SIZE = 32   # ed25519 seed length in bytes
KEY_TYPE = "ED25519-V3"


class OnionKey:
    def __init__(self, seed_path: str):
        self.seed_path = seed_path

    def key_material(self) -> tuple[str, str]:
        """Return ``(key_type, key_content)`` for a stem hidden service."""
        seed = self._load_or_create_seed()
        return KEY_TYPE, self._expand(seed)

    def onion_address(self) -> str:
        """Compute our fixed ``.onion`` address locally, without Tor."""
        _key_type, key_content = self.key_material()
        return onion_address(key_content)

    # ---- seed persistence ----

    def _load_or_create_seed(self) -> bytes:
        if os.path.exists(self.seed_path):
            with open(self.seed_path, "rb") as f:
                seed = f.read()
            if len(seed) == SEED_SIZE:
                return seed  # ignore a corrupt file and regenerate below

        seed = secrets.token_bytes(SEED_SIZE)
        os.makedirs(os.path.dirname(self.seed_path), exist_ok=True)
        with open(self.seed_path, "wb") as f:
            f.write(seed)
        _lock_down(self.seed_path)
        return seed

    # ---- derivation ----

    @staticmethod
    def _expand(seed: bytes) -> str:
        """Expand a 32-byte seed into Tor's base64 ED25519-V3 secret key.

        This mirrors the standard ed25519 secret expansion: SHA-512 the seed,
        then clamp the low half into a valid scalar. Tor stores this expanded
        64-byte form directly and derives the public key (and address) from it,
        so the same seed always yields the same address.
        """
        h = bytearray(hashlib.sha512(seed).digest())  # 64 bytes
        h[0] &= 0xF8
        h[31] &= 0x7F
        h[31] |= 0x40
        return base64.b64encode(bytes(h)).decode("ascii")


def _lock_down(path: str):
    """Best-effort owner-only permissions (no-op on some Windows setups)."""
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
