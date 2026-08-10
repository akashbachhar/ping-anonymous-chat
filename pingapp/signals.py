"""Qt signals used to marshal events from worker threads onto the UI thread.

Networking and Tor run on background threads; Qt widgets may only be touched
from the main thread. Every cross-thread notification goes through one of these
signals so the UI updates safely.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    bootstrap_progress = pyqtSignal(int, str)   # (percent, phase description)
    onion_ready = pyqtSignal(str)               # our .onion address
    status_update = pyqtSignal(str)             # setup-screen status text
    connected = pyqtSignal(str)                 # a peer connection is live (peer address or "")
    message_received = pyqtSignal(str)          # decoded inbound text message
    file_received = pyqtSignal(str, object)     # (filename, data bytes)
    disconnected = pyqtSignal(bool)             # (was_intentional)
    connect_failed = pyqtSignal(str)            # outbound attempt gave up
    error = pyqtSignal(str)                     # fatal setup error
