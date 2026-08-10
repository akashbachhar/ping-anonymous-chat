# main.py
#
# Entry point for the Ping GUI. The implementation lives in the `pingapp`
# package; this file only launches it:
#
#     python main.py

import sys

from PyQt6.QtWidgets import QApplication

from pingapp.ui.main_window import ChatApp
from pingapp.ui.styles import STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
