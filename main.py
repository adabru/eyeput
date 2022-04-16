import re
from time import time
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
    Qt,
    QEvent,
    QTimer,
    QPoint,
)
from PyQt5.QtGui import QFont, QCursor, QColor, QPainter

import sys
import signal

# alternative:  https://stackoverflow.com/questions/16615087/how-to-create-a-global-hotkey-on-windows-with-3-arguments
import keyboard
from pynput.mouse import Button, Controller

from levels import Levels
from commandlabel import CommandLabel as CommandLabel
from settings import *

mouse = Controller()


class State:
    lvl = "lvl1"
    hold = False
    modifiers = set()


class App(QObject):
    togglePos = QPoint(0, 0)
    colors = {
        "item": "#4480f8ff",
        "hover": "#6600bce8",
    }
    labels = {}
    toggle_signal = pyqtSignal()
    state = State()

    hoverItem = None
    hoverItemId = None

    hoverTimer = None
    clickTimer = None
    lastPos = (0, 0)
    counter = 0

    def __init__(self):
        super().__init__()
        self.toggle_signal.connect(self.toggle, Qt.QueuedConnection)

        self.hoverTimer = QTimer(self)
        self.hoverTimer.timeout.connect(self.selectItem)

        self.clickTimer = QTimer(self)
        self.clickTimer.timeout.connect(self.processMouse)

        self.widget = QWidget()
        self.widget.setStyleSheet(
            f"""
          QLabel {{ font-size: 20pt; background-color: {self.colors["item"]} ; }}
          QLabel:hover {{  background-color: {self.colors["hover"]} ; }}
        """
        )
        self.widget.setAttribute(Qt.WA_TranslucentBackground, True)
        # self.widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.widget.setWindowState(Qt.WindowFullScreen)
        screenGeometry = QApplication.primaryScreen().availableGeometry()
        self.widget.setGeometry(screenGeometry)
        self.widget.setFocusPolicy(Qt.NoFocus)

        screenGeometry = QApplication.primaryScreen().availableGeometry()
        dx = int(screenGeometry.width() / 14)
        dy = int(screenGeometry.height() / 6)
        for y in range(6):
            for x in range(14):
                label = CommandLabel(self.widget)
                label.setAlignment(Qt.AlignCenter)
                label.setGeometry(x * dx, y * dy, dx, dy)
                label.installEventFilter(self)
                label.setFocusPolicy(Qt.NoFocus)

                self.labels[(x, y)] = label

        self.updateGrid()

        self.widget.setWindowTitle("speechwindow")
        self.widget.show()

    def setLevel(self, levelId):
        self.state.lvl = levelId
        self.updateGrid()

    def updateGrid(self):
        for label in self.labels.values():
            label.id = None

        for key, item in Levels[self.state.lvl].items():
            self.labels[(item.x, item.y)].id = key
            self.labels[(item.x, item.y)].item = item
            self.labels[(item.x, item.y)].setText(item.label)
            self.labels[(item.x, item.y)].setModifiers(self.state.modifiers)
            self.labels[(item.x, item.y)].setVisible(True)

        for label in self.labels.values():
            if label.id == None:
                label.setVisible(False)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter and self.togglePos != QCursor.pos():
            self.hoverTimer.start(selectionTime)
            self.hoverItemId = obj.id
            self.hoverItem = obj.item
            return True

        elif event.type() == QEvent.Leave:
            self.hoverTimer.stop()
            self.hoverItemId = None
            self.hoverItem = None
            return True

        else:
            return super(App, self).eventFilter(obj, event)

    @pyqtSlot()
    def selectItem(self):
        print("selectItem: " + self.hoverItemId)
        self.hoverTimer.stop()

        hold = self.state.hold

        if self.hoverItemId == "hold":
            self.state.hold = not self.state.hold
            hold = self.state.hold

        elif self.hoverItemId in Levels:
            self.setLevel(self.hoverItemId)
            hold = True

        elif self.hoverItemId in modifierColors:
            if self.hoverItemId in self.state.modifiers:
                self.state.modifiers.remove(self.hoverItemId)
            else:
                self.state.modifiers.add(self.hoverItemId)
            hold = True

            self.updateGrid()

        elif self.hoverItemId == "click":
            self.clickTimer.setInterval(50)
            self.clickTimer.start()
            self.mouseMoveTime = time()
            self.state.hold = False
            hold = False

        elif self.hoverItem.pressKey:
            self.pressKey(self.hoverItem.pressKey)
        else:
            self.pressKey(self.hoverItem.label)

        if not hold:
            self.toggle()

    @pyqtSlot()
    def toggle(self):
        self.togglePos = QCursor.pos()
        self.widget.setVisible(not self.widget.isVisible())
        self.state.modifiers.clear()

    @pyqtSlot()
    def processMouse(self):
        dist = abs(mouse.position[0] - self.lastPos[0]) + abs(
            mouse.position[1] - self.lastPos[1]
        )

        if dist > 10:
            self.mouseMoveTime = time()

        elif time() - self.mouseMoveTime > delayBeforeClick:
            mouse.click(Button.left, 1)
            self.clickTimer.stop()

        self.lastPos = currentPos = mouse.position

    def pressKey(self, keyCode):
        print(self.state.modifiers)
        print("+".join(list(self.state.modifiers) + [keyCode]))
        keyboard.press_and_release("+".join(list(self.state.modifiers) + [keyCode]))
        self.state.modifiers.clear()
        self.updateGrid()


qapp = QApplication(sys.argv)
app = App()
# design flaw, see https://stackoverflow.com/q/4938723/6040478
signal.signal(signal.SIGINT, signal.SIG_DFL)

keyboard.add_hotkey("alt+a", app.toggle_signal.emit, suppress=True)
# print(keyboard.read_event())

qapp.exec_()
