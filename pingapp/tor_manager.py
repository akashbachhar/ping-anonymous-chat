"""Lifecycle management for the bundled Tor process and its onion service."""

import stem.process
from stem.control import Controller

from . import config
from .keystore import OnionKey


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
