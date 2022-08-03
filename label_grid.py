from PyQt5.QtCore import QRectF, Qt, QTimer, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QWidget
from command_label import CommandLabel

from logger import *
from settings import *
from tiles import *


class GridState:
    lvl = ""
    hold = False
    modifiers = set()


class LabelGrid(QWidget):
    state = GridState()
    labels = {}
    hover_item = None
    hover_timer = None
    action_signal = pyqtSignal(object, object, bool)

    def __init__(self, parent, geometry):
        super().__init__(parent)
        self.setGeometry(geometry)
        self.setFocusPolicy(Qt.NoFocus)

        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self.select_item)

        dx = int(geometry.width() / Tiles.x)
        dy = int(geometry.height() / Tiles.y)

        for y in range(Tiles.y):
            for x in range(Tiles.x):
                label = CommandLabel(self)
                label.setAlignment(Qt.AlignCenter)
                label.setGeometry(x * dx, y * dy, dx, dy)
                label.installEventFilter(self)
                label.setFocusPolicy(Qt.NoFocus)

                self.labels[(x, y)] = label

    def activate(self, label):
        if label != "_hide":
            self.set_level(label)
            if not self.isVisible():
                self.show()
        elif self.isVisible():
            self.set_hovered_item(None)
            self.state.modifiers.clear()
            self.state.hold = False
            self.hover_timer.stop()
            self.hide()

    def set_level(self, levelId):
        self.state.lvl = levelId
        self.update_grid()

    def on_gaze(self, x, y, after_activation=False):
        if not QRectF(0, 0, 1, 1).contains(x, y):
            return log_debug("outside")

        xWidget = int(Tiles.x * x)
        yWidget = int(Tiles.y * y)
        if xWidget >= Tiles.x or yWidget >= Tiles.y:
            return log_debug("invalid indices: " + str(xWidget) + ", " + str(yWidget))

        widget = self.labels[(xWidget, yWidget)]

        if not widget.isVisible():
            return log_debug("invisible")

        if widget == self.hover_item:
            return log_debug("same")

        if not after_activation:
            self.hover_timer.start(int(Times.element_selection * 1000))
        else:
            self.hover_timer.stop()

        self.set_hovered_item(widget)

    def set_hovered_item(self, widget):
        if widget != self.hover_item:
            if widget:
                widget.setHovered(True)

            if self.hover_item:
                self.hover_item.setHovered(False)

            self.hover_item = widget

    def update_grid(self):
        for label in self.labels.values():
            label.id = None
            label.setToggled(False)
            # self.hoverItem.setHovered(False)

        for key, item in tiles[self.state.lvl].items():
            label = self.labels[(item.x, item.y)]
            label.id = key
            label.setItem(item)
            label.setModifiers(self.state.modifiers)
            label.setText(item.label)
            label.show()
            # special cases
            if label.id == "hold" and self.state.hold:
                label.setToggled(True)
            elif label.id in self.state.modifiers:
                label.setToggled(True)

        for label in self.labels.values():
            if label.id == None:
                label.hide()

    @pyqtSlot()
    def select_item(self):
        log_info("selectItem: " + self.hover_item.id)
        self.hover_timer.stop()
        self.hover_item.activate()

        if self.hover_item.id == "hold":
            self.state.hold = not self.state.hold
            self.update_grid()

        elif self.hover_item.id in tiles:
            self.set_level(self.hover_item.id)

        elif self.hover_item.id in modifierColors:
            if self.hover_item.id in self.state.modifiers:
                self.state.modifiers.remove(self.hover_item.id)
            else:
                self.state.modifiers.add(self.hover_item.id)
            self.update_grid()

        elif isinstance(self.hover_item.item, KeyAction):
            self.action_signal.emit(
                self.hover_item.item, self.state.modifiers, not self.state.hold
            )
            self.state.modifiers.clear()
            self.update_grid()

        else:
            self.action_signal.emit(self.hover_item.item, None, True)
