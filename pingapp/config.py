"""Static configuration: filesystem paths, network ports, and tunables.

Paths adapt to how the app runs:

* Development (``python main.py``): the bundled Tor executable and all data live
  in the project directory.
* Frozen (the packaged ``ping.exe``): ``tor.exe`` comes from the PyInstaller
  bundle, while writable state (Tor data + onion identity) goes to
  ``%LOCALAPPDATA%\\Ping`` so it works regardless of where the exe sits.
"""

import os
import sys

_FROZEN = getattr(sys, "frozen", False)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resource_base() -> str:
    """Directory holding bundled read-only files (tor.exe)."""
    if _FROZEN:
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return _PROJECT_ROOT


def _data_root() -> str:
    """Directory for per-user writable state."""
    if _FROZEN:
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Ping")
    return _PROJECT_ROOT


RESOURCE_DIR = _resource_base()
DATA_ROOT = _data_root()

# ---- Filesystem layout ----
TOR_DIR = os.path.join(RESOURCE_DIR, "tor_bin")   # bundled Tor executable
TOR_PATH = os.path.join(TOR_DIR, "tor.exe")
DATA_DIR = os.path.join(DATA_ROOT, "tor_data")    # Tor runtime data + identity

# Onion identity. A 32-byte random seed (owned by Ping, not Tor) is stored here
# and deterministically expanded into the ED25519-V3 key each launch, giving a
# fixed onion address every run. See pingapp.keystore.
SEED_FILE = os.path.join(DATA_DIR, "onion_seed")

# ---- Network ports ----
SOCKS_PORT = 9060        # Tor SOCKS proxy for outbound connections
CONTROL_PORT = 9061      # Tor control port (stem)
LOCAL_CHAT_PORT = 5001   # local port the onion service forwards to
ONION_PORT = 80          # virtual port advertised by the onion service

# ---- Behaviour ----
CONNECT_RETRIES = 5
CONNECT_RETRY_DELAY = 4  # seconds between outbound connection attempts
RECV_BUFFER = 4096

# ---- Presentation ----
APP_NAME = "Ping"
TAGLINE = "Anonymous P2P Chat"
WINDOW_TITLE = "Ping"
