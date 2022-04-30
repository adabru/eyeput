import os.path

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRect

from settings import *


class GazePointer(QWidget):
    pixmap = None
    pos = (int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pixmap = QPixmap(f"{os.path.dirname(__file__)}/resources/gazePointer.png")
        self.setGeometry(0, 0, self.pixmap.width(), self.pixmap.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(
            0,
            0,
            self.pixmap,
        )
