"""Application-wide Qt style sheet (a compact dark theme)."""

STYLESHEET = """
QWidget {
    background-color: #14161a;
    color: #e6e8ea;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
}

QLabel#Title {
    font-size: 26px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#Subtle {
    color: #8b929b;
    font-size: 12px;
}

QLabel#Header {
    font-weight: 600;
    padding: 6px 2px;
    color: #cfd3d8;
}

/* ---- chat screen ---- */

QLabel#PeerAddress {
    color: #b085f5;               /* purple */
    font-size: 13px;
    font-weight: 600;
    padding: 2px 2px;
}

QTextEdit#ChatLog {
    background-color: #101216;
    border: 1px solid #2b2f37;
    border-radius: 10px;
    padding: 6px 8px;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #3a3f48;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #4a505b;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QLineEdit, QTextEdit {
    background-color: #1d2026;
    border: 1px solid #2b2f37;
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #3d7dfc;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #3d7dfc;
}

QLineEdit[readOnly="true"] {
    color: #9aa0a8;
}

QPushButton {
    background-color: #3d7dfc;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover { background-color: #5590ff; }
QPushButton:pressed { background-color: #2f6ae0; }
QPushButton:disabled { background-color: #2b2f37; color: #6b7178; }

QPushButton#Ghost {
    background-color: transparent;
    border: 1px solid #2b2f37;
    color: #cfd3d8;
}
QPushButton#Ghost:hover { border-color: #3d7dfc; color: #ffffff; }

QProgressBar {
    background-color: #1d2026;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #3d7dfc;
    border-radius: 6px;
}
"""
