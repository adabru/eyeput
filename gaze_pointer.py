import os.path

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer

from settings import *


class Circle(QWidget):
    def __init__(self, parent, color):
        super().__init__(parent)
        self.color = color
        self.setGeometry(0, 0, 20, 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.color)
        painter.drawRect(QRect(0, 0, 20, 20))


class GazePointer(QWidget):
    pixmap = None
    position = (int, int)
    flash_state = True

    correction = (None, None)
    is_moving = False

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(self.flash)
        self.flash_timer.setInterval(int(0.05 * 1000))
        self.pixmap = QPixmap(f"{os.path.dirname(__file__)}/resources/gaze_pointer.png")
        self.setGeometry(0, 0, self.pixmap.width(), self.pixmap.height())
        self.correction = (
            Circle(parent, QColor(255, 255, 0, 255)),
            Circle(parent, QColor(80, 80, 0, 255)),
        )

    def flash(self):
        # self.setVisible(not self.isVisible())
        self.flash_state = not self.flash_state
        self.update()

    def stop_move(self, position):
        self.is_moving = False
        self.flash_timer.stop()
        self.hide()
        self.correction[0].hide()
        self.correction[1].hide()

        diff = self.correction[1].pos() - self.correction[0].pos()
        return self.pos() + diff / 5

    def start_move(self, position):
        self.show()
        self.correction[0].show()
        self.correction[1].show()
        self.is_moving = True
        self.move(position)
        self.correction[0].move(position + QPoint(0, 30))
        self.flash_timer.start()

    def on_gaze(self, position):
        if self.is_moving:
            self.correction[1].move(position + QPoint(0, 30))

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.flash_state:
            painter.setPen(QColor(255, 0, 0, 255))
        else:
            painter.setPen(QColor(0, 255, 0, 255))
        painter.drawRect(QRect(0, 0, 1, 1))

        # painter.drawPixmap(
        #     0,
        #     0,
        #     self.pixmap,
        # )
