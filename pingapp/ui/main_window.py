"""The top-level window that wires the backend to the two screens."""

import os
import threading

from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..connection import ConnectionManager
from ..protocol import FILE_SIZE_LIMIT
from ..signals import AppSignals
from ..tor_manager import TorManager
from ..util import human_size, safe_filename
from .chat_screen import ChatScreen
from .setup_screen import SetupScreen


class ChatApp(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = AppSignals()
        self.tor = TorManager(on_bootstrap_line=self._on_bootstrap_line)
        self.conn = ConnectionManager(self.signals)

        self._build_ui()
        self._wire_signals()

        threading.Thread(target=self._init_backend, daemon=True).start()

    # ---------------- UI construction ----------------

    def _build_ui(self):
        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(460, 640)

        self.stack = QStackedWidget()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.stack)

        self.setup_screen = SetupScreen()
        self.chat_screen = ChatScreen()
        self.stack.addWidget(self.setup_screen)
        self.stack.addWidget(self.chat_screen)
        self.stack.setCurrentWidget(self.setup_screen)

    def _wire_signals(self):
        s = self.signals
        s.bootstrap_progress.connect(self.setup_screen.set_progress)
        s.onion_ready.connect(self.setup_screen.set_address)
        s.status_update.connect(self.setup_screen.set_status)
        s.connected.connect(self._on_connected)
        s.message_received.connect(self._on_message)
        s.disconnected.connect(self._on_disconnected)
        s.connect_failed.connect(self.setup_screen.on_connect_failed)
        s.error.connect(self.setup_screen.set_status)
        s.file_received.connect(self._on_file_received)

        self.setup_screen.connect_requested.connect(self.conn.connect_to)
        self.chat_screen.send_requested.connect(self._on_send)
        self.chat_screen.leave_requested.connect(self._on_leave)
        self.chat_screen.attach_requested.connect(self._on_attach)

    # ---------------- Backend bootstrap ----------------

    def _init_backend(self):
        # The address is a pure function of our key, so show it immediately —
        # no waiting on Tor bootstrap or service publication.
        try:
            self.signals.onion_ready.emit(self.tor.onion_address())
        except Exception:
            pass  # fall back to showing it once Tor confirms it below

        try:
            self.tor.start()
            self.signals.status_update.emit("Publishing onion service...")
            address = self.tor.create_onion_service()
            self.signals.onion_ready.emit(address)
            self.conn.start_listener()
            self.signals.status_update.emit(
                "Ready. Share your address or connect to a peer."
            )
        except Exception as e:  # surface any setup failure to the user
            self.signals.error.emit(f"❌ Error: {e}")

    def _on_bootstrap_line(self, line: str):
        if "Bootstrapped" not in line:
            return
        try:
            pct = int(line.split("Bootstrapped ")[1].split("%")[0])
            phase = line.split(": ", 1)[1] if ": " in line else ""
            self.signals.bootstrap_progress.emit(pct, phase)
        except (ValueError, IndexError):
            pass

    # ---------------- Connection events ----------------

    def _on_connected(self, peer_address: str):
        self.chat_screen.reset()
        self.chat_screen.set_peer(peer_address)
        self.stack.setCurrentWidget(self.chat_screen)

    def _on_message(self, text: str):
        self.chat_screen.add_message(text, is_self=False)

    def _on_send(self, text: str):
        if self.conn.send(text):
            self.chat_screen.add_message(text, is_self=True)
        else:
            self.chat_screen.add_system("Failed to send — connection closed.")

    def _on_attach(self):
        path, _ = QFileDialog.getOpenFileName(self, "Send a file")
        if not path:
            return
        try:
            size = os.path.getsize(path)
        except OSError:
            self.chat_screen.add_system("Could not read that file.")
            return
        if size > FILE_SIZE_LIMIT:
            limit = human_size(FILE_SIZE_LIMIT)
            self.chat_screen.add_system(f"File too large — the limit is {limit}.")
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            self.chat_screen.add_system("Could not read that file.")
            return

        name = os.path.basename(path)
        if self.conn.send_file(name, data):
            self.chat_screen.add_message(
                f"📎 {name} ({human_size(size)})", is_self=True
            )
        else:
            self.chat_screen.add_system("Failed to send file — connection closed.")

    def _on_file_received(self, filename: str, data: bytes):
        size = human_size(len(data))
        self.chat_screen.add_message(f"📎 {filename} ({size})", is_self=False)

        choice = QMessageBox.question(
            self,
            "Incoming file",
            f'Peer sent "{filename}" ({size}).\n\nDownload it?',
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Save:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save file", safe_filename(filename)
        )
        if not save_path:
            return
        try:
            with open(save_path, "wb") as f:
                f.write(data)
            self.chat_screen.add_system(f"Saved to {save_path}")
        except OSError:
            self.chat_screen.add_system("Failed to save file.")

    def _on_disconnected(self, intentional: bool):
        self.setup_screen.reset_after_disconnect()
        if not intentional:
            self.setup_screen.set_status("Peer disconnected. Ready to reconnect.")
        else:
            self.setup_screen.set_status(
                "Ready. Share your address or connect to a peer."
            )
        self.stack.setCurrentWidget(self.setup_screen)

    def _on_leave(self):
        # Closing the socket makes the receive thread emit `disconnected`,
        # which performs the actual screen transition.
        self.conn.disconnect()

    # ---------------- Shutdown ----------------

    def closeEvent(self, event):
        self.conn.shutdown()
        self.tor.shutdown()
        event.accept()
