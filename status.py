import os.path

from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5.QtGui import QFont, QColor, QPainter, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRect, QTimer

from settings import *


class Status(QWidget):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.setGeometry(QRect(5, 5, 100, 50))
        self.mode = mode
        self.eyes = (0, 0)

    def _lerp(self, x, y, a):
        return int(a * y + (1 - a) * x)

    def _get_color(self, variance):
        if variance == 0:
            return Colors.eye_closed
        else:
            a = variance
            return QColor.fromHsv(
                self._lerp(Colors.eye_flickering.hue(), Colors.eye_opened.hue(), a),
                self._lerp(
                    Colors.eye_flickering.saturation(),
                    Colors.eye_opened.saturation(),
                    a,
                ),
                self._lerp(Colors.eye_flickering.value(), Colors.eye_opened.value(), a),
            )

    def on_gaze(self, l_variance, r_variance):
        l = self._get_color(l_variance)
        r = self._get_color(r_variance)
        if self.eyes != (l, r):
            self.eyes = (l, r)
            self.update()

    def set_mode(self, mode):
        self.mode = mode
        self.update()
        # if self.item and self.item.img:
        #     self.pixmap = QPixmap(self.item.img)
        #     if self.pixmap.height() == 0:
        #         self.pixmap = QPixmap(
        #             f"{os.path.dirname(__file__)}/resources/missing.png"
        #         )

    def paintEvent(self, event):
        painter = QPainter(self)

        # draw image
        # if self.pixmap:
        #     pixmapRatio = float(self.pixmap.width()) / self.pixmap.height()
        #     windowRatio = float(self.width()) / self.height()

        #     newWidth = min(self.width(), Tiles.maxSide)
        #     newHeight = int(newWidth / pixmapRatio)
        #     dx = int((newHeight - self.width()) / -2)
        #     dy = int((newHeight - self.height()) / -2)

        #     painter.drawPixmap(dx, dy, newWidth, newHeight, self.pixmap)

        # draw eye cirlces
        painter.setPen(Colors.eye_border)
        painter.setBrush(self.eyes[0])
        painter.drawEllipse(QRect(0, 0, 30, 30))
        painter.setBrush(self.eyes[1])
        painter.drawEllipse(QRect(40, 0, 30, 30))

        # draw text
        fontSize = 8
        painter.setFont(QFont("Arial", fontSize))
        painter.setPen(Colors.text)
        painter.drawText(
            QRect(0, 0, 45, 20),
            Qt.AlignCenter,
            self.mode,
        )
