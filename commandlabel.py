from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QFont, QColor, QPainter
from PyQt5.QtCore import Qt, QPoint, QRect
from settings import *


class CommandLabel(QLabel):
    modifiers = set()
    id = ""
    item = None
    hovered = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet(f"background-color: {Colors.item};")

    def setModifiers(self, modifiers):
        self.modifiers = modifiers
        self.update()

    def setHovered(self, value):
        self.hovered = value
        self.update()

    def paintEvent(self, event):

        fontSize = 20
        painter = QPainter(self)
        painter.setFont(QFont("Arial", fontSize))

        painter.setPen(QColor(255, 255, 255, 0))
        if self.hovered:
            painter.setBrush(QColor(80, 255, 255, 150))
        else:
            painter.setBrush(QColor(255, 255, 255, 40))
        painter.drawEllipse(self.rect().center() + QPoint(1, 1), 14, 14)

        painter.setPen(QColor(0, 0, 0))
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            self.text(),
        )

        if len(self.modifiers) > 0:
            painter.setPen(QColor(168, 34, 3, 50))

            dotWidth = 10
            gap = 2
            leftBorder = 0.5 * self.width() - 2 * dotWidth - 2 * gap
            oldBrush = painter.brush()

            for i, key in enumerate(modifierColors):

                if key in self.modifiers:
                    painter.setBrush(modifierColors[key])
                else:
                    painter.setBrush(oldBrush)

                painter.drawRoundedRect(
                    int(i * (dotWidth + gap) + leftBorder), 10, dotWidth, dotWidth, 2, 2
                )

        painter.end()
