"""python -m sma4py で起動する。"""

import sys


def main():
    from PySide6.QtWidgets import QApplication

    from .mainwindow import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Sma4Py")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
