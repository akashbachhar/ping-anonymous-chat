"""Static configuration: filesystem paths, network ports, and tunables.

All paths are resolved relative to the current working directory, matching the
original launch assumption that Ping is started from the project root.
"""

import os

# ---- Filesystem layout ----
BASE_DIR = os.getcwd()
TOR_DIR = os.path.join(BASE_DIR, "tor_bin")     # bundled Tor executable
TOR_PATH = os.path.join(TOR_DIR, "tor.exe")
DATA_DIR = os.path.join(BASE_DIR, "tor_data")   # Tor runtime data + identity

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
