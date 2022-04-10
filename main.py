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
from levels import Levels


# alternative:  https://stackoverflow.com/questions/16615087/how-to-create-a-global-hotkey-on-windows-with-3-arguments
import keyboard
from pynput.mouse import Button, Controller

mouse = Controller()

selectionTime = 300
delayBeforeClick = 1.5
modifierColors = {
    "win": QColor(0x61A0AF),
    "alt": QColor(0x96C9DC),
    "ctrl": QColor(0xF9B9B7),
    "shift": QColor(0xF5D491),
}


class State:
    lvl = "➀"
    hold = False
    modifiers = set()


class CommandLabel(QLabel):
    modifiers = set()

    def setModifiers(self, modifiers):
        self.modifiers = modifiers
        self.update()

    def paintEvent(self, event):
        super(CommandLabel, self).paintEvent(event)
        if len(self.modifiers) > 0:

            painter = QPainter(self)
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


class App(QObject):
    togglePos = QPoint(0, 0)
    colors = {
        "item": "#4480f8ff",
        "hover": "#6600bce8",
    }
    labels = {}
    toggle_signal = pyqtSignal()
    state = State()

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
        for y, row in enumerate(Levels[self.state.lvl]):
            for x, labelKey in enumerate(row):
                self.labels[(x, y)].setText(labelKey)
                self.labels[(x, y)].setModifiers(self.state.modifiers)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter and self.togglePos != QCursor.pos():
            self.hoverTimer.start(selectionTime)
            self.hoverItem = obj.text()
            return True

        elif event.type() == QEvent.Leave:
            self.hoverTimer.stop()
            self.hoverItem = ""
            return True

        else:
            return super(App, self).eventFilter(obj, event)

    @pyqtSlot()
    def selectItem(self):
        print("selectItem: " + self.hoverItem)
        self.hoverTimer.stop()

        hold = self.state.hold

        if self.hoverItem == "hold":
            self.state.hold = not self.state.hold
            hold = self.state.hold

        elif self.hoverItem in modifierColors:
            self.state.modifiers.add(self.hoverItem)
            hold = True
            self.updateGrid()

        elif re.match(r"[A-Z]", self.hoverItem) != None:
            self.state.modifiers.add("shift")
            self.pressKey(self.hoverItem.lower())

        elif self.hoverItem in Levels:
            self.setLevel(self.hoverItem)
            hold = True

        elif self.hoverItem == "click":
            self.clickTimer.setInterval(50)
            self.clickTimer.start()
            self.mouseMoveTime = time()

        elif self.hoverItem == "":
            print("invalid symbol: ''")
        else:
            self.pressKey(self.hoverItem)

        if not hold:
            self.toggle()

    @pyqtSlot()
    def toggle(self):
        self.togglePos = QCursor.pos()
        self.widget.setVisible(not self.widget.isVisible())

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
        keyboard.press_and_release("+".join(list(self.state.modifiers) + [keyCode]))
        self.state.modifiers.clear()
        self.updateGrid()


qapp = QApplication(sys.argv)
app = App()
# design flaw, see https://stackoverflow.com/q/4938723/6040478
signal.signal(signal.SIGINT, signal.SIG_DFL)

keyboard.add_hotkey("^", app.toggle_signal.emit, suppress=True)

qapp.exec_()
