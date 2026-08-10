"""The conversation screen: colour-coded plain-text chat (no bubbles).

Messages are distinguished by colour and side only — green on the right for you,
blue on the left for the peer — with no name labels. Peer text is HTML-escaped
and rendered as plain content, never markup.
"""

import html
import time

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTextBlockFormat, QTextCursor, QTextOption
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

SELF_COLOR = "#46d17f"   # green — your messages (right)
PEER_COLOR = "#58a6ff"   # blue — peer messages (left)
TIME_COLOR = "#6b7178"


class ChatScreen(QWidget):
    send_requested = pyqtSignal(str)
    leave_requested = pyqtSignal()
    attach_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._peer_address = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ---- top bar: peer address (left) + leave (right) ----
        header_row = QHBoxLayout()
        self.peer_label = QLabel()
        self.peer_label.setObjectName("PeerAddress")
        header_row.addWidget(self.peer_label, 1)

        self.leave_btn = QPushButton("Leave")
        self.leave_btn.setObjectName("Ghost")
        self.leave_btn.clicked.connect(self.leave_requested.emit)
        header_row.addWidget(self.leave_btn)
        layout.addLayout(header_row)

        # ---- message log ----
        self.chat_log = QTextEdit()
        self.chat_log.setObjectName("ChatLog")
        self.chat_log.setReadOnly(True)
        # Wrap long lines to the widget, breaking mid-word if a token is huge
        # (e.g. a pasted onion address) so nothing overflows horizontally.
        self.chat_log.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.chat_log.setWordWrapMode(
            QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere
        )
        # Scroll vertically as messages accumulate; never scroll horizontally.
        self.chat_log.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.chat_log.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        layout.addWidget(self.chat_log, 1)

        # ---- composer ----
        input_row = QHBoxLayout()

        attach_btn = QPushButton("📎")
        attach_btn.setObjectName("Ghost")
        attach_btn.setFixedWidth(40)
        attach_btn.setToolTip("Attach a file (max 5 MB)")
        attach_btn.clicked.connect(self.attach_requested.emit)
        input_row.addWidget(attach_btn)

        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message...")
        self.msg_input.returnPressed.connect(self._request_send)
        input_row.addWidget(self.msg_input)

        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._request_send)
        input_row.addWidget(send_btn)
        layout.addLayout(input_row)

    # ---- public API ----

    def set_peer(self, address: str):
        self._peer_address = address or "Anonymous"
        self._update_peer_label()

    def reset(self):
        self.chat_log.clear()
        self.msg_input.clear()
        self.msg_input.setFocus()

    def add_message(self, text: str, is_self: bool):
        color = SELF_COLOR if is_self else PEER_COLOR
        align = Qt.AlignmentFlag.AlignRight if is_self else Qt.AlignmentFlag.AlignLeft
        stamp = time.strftime("%H:%M")
        safe = html.escape(text)
        self._append_block(
            align,
            f'<span style="color:{color};">{safe}</span> '
            f'<span style="color:{TIME_COLOR}; font-size:11px;">{stamp}</span>',
        )

    def add_system(self, text: str):
        safe = html.escape(text)
        self._append_block(
            Qt.AlignmentFlag.AlignHCenter,
            f'<span style="color:#8b929b; font-size:12px; '
            f'font-style:italic;">{safe}</span>',
        )

    # ---- internal ----

    def _append_block(self, alignment, html_fragment: str):
        # Insert the text first, THEN set the block alignment. Setting it before
        # insertHtml() is unreliable — insertHtml resets the block format, which
        # silently left-aligns the first message after every reset().
        cursor = self.chat_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if not self.chat_log.document().isEmpty():
            cursor.insertBlock()
        cursor.insertHtml(html_fragment)

        block_fmt = QTextBlockFormat()
        block_fmt.setAlignment(alignment)
        block_fmt.setTopMargin(4)
        cursor.mergeBlockFormat(block_fmt)  # applies to the block just filled
        self._scroll_to_bottom()

    def _request_send(self):
        text = self.msg_input.text().strip()
        if not text:
            return
        self.send_requested.emit(text)
        self.msg_input.clear()

    def _scroll_to_bottom(self):
        # Move to the end and reveal it; reliable even before the scrollbar
        # range has caught up with the newly appended text.
        self.chat_log.moveCursor(QTextCursor.MoveOperation.End)
        self.chat_log.ensureCursorVisible()

    def _update_peer_label(self):
        # Middle-elide the long onion address to fit; full value in the tooltip.
        metrics = self.peer_label.fontMetrics()
        available = max(self.peer_label.width(), 120)
        elided = metrics.elidedText(
            self._peer_address, Qt.TextElideMode.ElideMiddle, available
        )
        self.peer_label.setText(elided)
        self.peer_label.setToolTip(self._peer_address)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_peer_label()
