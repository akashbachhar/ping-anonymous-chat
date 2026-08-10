"""Lifecycle management for the bundled Tor process and its onion service."""

import contextlib
import os
import subprocess
import sys

import stem.process
from stem.control import Controller

from . import config
from .keystore import OnionKey

_CREATE_NO_WINDOW = 0x08000000


@contextlib.contextmanager
def _no_subprocess_window():
    """Launch child processes without a console window (Windows only).

    stem starts tor.exe via subprocess.Popen without creation flags. When the
    parent is a windowed app (the packaged ping.exe has no console of its own),
    Windows gives that child its own console window — a stray terminal next to
    the GUI. Injecting CREATE_NO_WINDOW for the duration of the launch keeps Tor
    invisible. On non-Windows platforms this is a no-op.
    """
    if sys.platform != "win32":
        yield
        return
    original = subprocess.Popen.__init__

    def patched(self, *args, **kwargs):
        kwargs["creationflags"] = kwargs.get("creationflags", 0) | _CREATE_NO_WINDOW
        original(self, *args, **kwargs)

    subprocess.Popen.__init__ = patched
    try:
        yield
    finally:
        subprocess.Popen.__init__ = original


class TorManager:
    """Launches Tor, publishes our onion service, and tears both down cleanly."""

    def __init__(self, on_bootstrap_line=None):
        self.on_bootstrap_line = on_bootstrap_line
        self.process = None
        self.controller = None
        self.service_id = None
        self._onion_key = OnionKey(config.SEED_FILE)

    def onion_address(self) -> str:
        """Our fixed onion address, derived locally from the key (no Tor needed)."""
        return self._onion_key.onion_address()

    def start(self):
        """Launch Tor and authenticate a control connection. Blocks until ready."""
        os.makedirs(config.DATA_DIR, exist_ok=True)  # writable Tor data dir
        with _no_subprocess_window():
            self.process = stem.process.launch_tor_with_config(
                config={
                    "SocksPort": str(config.SOCKS_PORT),
                    "ControlPort": str(config.CONTROL_PORT),
                    "DataDirectory": config.DATA_DIR,
                },
                tor_cmd=config.TOR_PATH,
                init_msg_handler=self.on_bootstrap_line,
            )
        self.controller = Controller.from_port(port=config.CONTROL_PORT)
        self.controller.authenticate()

    def create_onion_service(self) -> str:
        """Publish the onion service from our persistent seed-derived key.

        The key is deterministic, so this yields the same ``<id>.onion`` address
        on every launch.
        """
        key_type, key_content = self._onion_key.key_material()
        response = self.controller.create_ephemeral_hidden_service(
            {config.ONION_PORT: config.LOCAL_CHAT_PORT},
            key_type=key_type,
            key_content=key_content,
            await_publication=True,
        )
        self.service_id = response.service_id
        return f"{self.service_id}.onion"

    def shutdown(self):
        """Remove the service and stop Tor. Safe to call more than once."""
        if self.service_id and self.controller:
            try:
                self.controller.remove_ephemeral_hidden_service(self.service_id)
            except Exception:
                pass
            self.service_id = None
        if self.controller:
            try:
                self.controller.close()
            except Exception:
                pass
            self.controller = None
        if self.process:
            try:
                self.process.kill()
            except Exception:
                pass
            self.process = None
