"""The initial screen: Tor bootstrap progress, our address, and a connect box."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import config


class SetupScreen(QWidget):
    """Emits :attr:`connect_requested` with a normalised ``.onion`` address."""

    connect_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 34, 30, 30)
        layout.setSpacing(12)

        layout.addSpacing(6)

        title = QLabel(config.APP_NAME)
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(config.TAGLINE)
        subtitle.setObjectName("Subtle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Starting Tor...")
        self.status_label.setObjectName("Subtle")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addSpacing(14)
        layout.addWidget(QLabel("Your onion address"))

        addr_row = QHBoxLayout()
        self.my_address_field = QLineEdit()
        self.my_address_field.setReadOnly(True)
        self.my_address_field.setPlaceholderText("Waiting for Tor...")
        addr_row.addWidget(self.my_address_field)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("Ghost")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_address)
        addr_row.addWidget(self.copy_btn)
        layout.addLayout(addr_row)

        layout.addSpacing(20)
        layout.addWidget(QLabel("Connect to a peer"))

        self.peer_input = QLineEdit()
        self.peer_input.setPlaceholderText("xxxxxxxx....onion")
        self.peer_input.returnPressed.connect(self._request_connect)
        layout.addWidget(self.peer_input)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._request_connect)
        layout.addWidget(self.connect_btn)

        layout.addStretch()

    # ---- Slots driven by AppSignals ----

    def set_progress(self, pct: int, phase: str):
        self.progress.setValue(pct)
        self.status_label.setText(f"Bootstrapping Tor: {pct}% — {phase}")

    def set_address(self, address: str):
        self.my_address_field.setText(address)
        self.copy_btn.setEnabled(True)
        self.progress.setValue(100)

    def set_status(self, text: str):
        self.status_label.setText(text)

    def on_connect_failed(self, message: str):
        self.status_label.setText(f"❌ {message}")
        self.connect_btn.setEnabled(True)

    def reset_after_disconnect(self):
        self.connect_btn.setEnabled(True)
        self.peer_input.clear()

    # ---- Internal ----

    def _request_connect(self):
        address = self.peer_input.text().strip()
        if not address:
            self.set_status("Please enter an onion address.")
            return
        if not address.endswith(".onion"):
            address += ".onion"
        self.connect_btn.setEnabled(False)
        self.connect_requested.emit(address)

    def _copy_address(self):
        address = self.my_address_field.text()
        if address:
            QGuiApplication.clipboard().setText(address)
            self.set_status("Address copied to clipboard.")
