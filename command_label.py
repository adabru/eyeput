import os.path

from PySide2.QtWidgets import QLabel
from PySide2.QtGui import QFont, QColor, QPainter, QPixmap
from PySide2.QtCore import Qt, QPoint, QRect, QTimer

from settings import *


class CommandLabel(QLabel):
    modifiers = set()
    id = ""
    item = None
    hovered = False
    toggled = False
    activated = False
    pixmap = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(f"background-color: {Colors.item};")
        self.deactivate_timer = QTimer(self)
        self.deactivate_timer.timeout.connect(self._deactivate)

    def setItem(self, item):
        self.item = item
        if self.item and self.item.img:
            self.pixmap = QPixmap(self.item.img)
            if self.pixmap.height() == 0:
                self.pixmap = QPixmap(
                    f"{os.path.dirname(__file__)}/resources/missing.png"
                )

    def setModifiers(self, modifiers):
        self.modifiers = modifiers
        self.update()

    def setHovered(self, value):
        self.hovered = value
        self.update()

    def setToggled(self, value):
        self.toggled = value
        self.update()

    def activate(self):
        """..."""
        self.activated = True
        self.deactivate_timer.start(int(Times.selection_feedback * 1000))
        self.update()

    def _deactivate(self):
        """..."""
        self.activated = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        # draw image
        if self.pixmap:
            pixmapRatio = float(self.pixmap.width()) / self.pixmap.height()
            windowRatio = float(self.width()) / self.height()

            newWidth = min(self.width(), Tiles.maxSide)
            newHeight = int(newWidth / pixmapRatio)
            dx = int((newHeight - self.width()) / -2)
            dy = int((newHeight - self.height()) / -2)

            painter.drawPixmap(dx, dy, newWidth, newHeight, self.pixmap)

        # draw text
        fontSize = 20
        painter.setFont(QFont("Arial", fontSize))
        painter.setPen(Colors.text_label)
        painter.drawText(
            0,
            0,
            self.width(),
            0.5 * self.height(),
            Qt.AlignCenter,
            self.text(),
        )

        # draw hover cirlce
        painter.setPen(Colors.circle_border)
        if self.activated:
            painter.setBrush(Colors.circle_activated)
        elif self.toggled:
            painter.setBrush(Colors.circle_toggled)
        elif self.hovered:
            painter.setBrush(Colors.circle_hovered)
        else:
            painter.setBrush(Colors.circle)
        painter.drawEllipse(self.rect().center() + QPoint(1, 1), 5, 5)

        # draw modifier cirlces
        if len(self.modifiers) > 0:
            painter.setPen(Colors.modifierBorder)

            dotWidth = 10
            gap = 2
            leftBorder = 0.5 * self.width() - 2 * dotWidth - 2 * gap

            for i, key in enumerate(modifierColors):

                if key in self.modifiers:
                    painter.setBrush(modifierColors[key])
                else:
                    painter.setBrush(QColor(0, 0, 0, 0))

                painter.drawRoundedRect(
                    int(i * (dotWidth + gap) + leftBorder), 10, dotWidth, dotWidth, 2, 2
                )
