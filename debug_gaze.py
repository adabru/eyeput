import os.path

from PySide2.QtWidgets import QWidget
from PySide2.QtGui import QPainter, QPixmap
from PySide2.QtCore import Qt, QPoint, QPointF, QRect, QTimer
from gaze_filter import FilteredFrame

from settings import *
from util import *


class Circle(QWidget):
    def __init__(self, parent, color):
        super().__init__(parent)
        self.color = color
        self.setGeometry(0, 0, 5, 5)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.color)
        painter.drawRect(QRect(0, 0, 5, 5))


class DebugGaze(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(get_screen_geometry())
        self.left = Circle(self, Colors.eye_left)
        self.right = Circle(self, Colors.eye_right)

    def on_frame(self, frame: FilteredFrame):
        if self.isVisible():
            self.left.move(rel2abs(frame.l_screen_position))
            self.right.move(rel2abs(frame.r_screen_position))
