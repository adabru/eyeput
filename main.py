#!/usr/bin/env python

import re, sys, os, signal, errno
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
    QThread,
)
from PyQt5.QtGui import QFont, QColor, QPainter
from pynput.mouse import Button, Controller

from levels import Levels
from commandlabel import CommandLabel as CommandLabel
from settings import *
from unix_socket import UnixSocket

mouse = Controller()

sock_keypress = UnixSocket(Sockets.keypress, 100)
sock_gaze = UnixSocket(Sockets.gaze, 100)


class State:
    lvl = "lvl1"
    hold = False
    modifiers = set()


class App(QObject):
    # prevent clicking first element when using mouse and pressing the hotkey
    gazeMoved = False
    labels = {}
    state = State()

    hoverItem = None

    hoverTimer = None
    clickTimer = None
    lastPos = (0, 0)
    counter = 0

    def __init__(self):
        super().__init__()

        self.hoverTimer = QTimer(self)
        self.hoverTimer.timeout.connect(self.selectItem)

        self.clickTimer = QTimer(self)
        self.clickTimer.timeout.connect(self.processMouse)

        self.widget = QWidget()
        self.widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.widget.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.X11BypassWindowManagerHint
        )
        # self.widget.setWindowState(Qt.WindowFullScreen)

        screenGeometry = QApplication.primaryScreen().geometry()

        self.widget.setGeometry(screenGeometry)
        self.widget.setFocusPolicy(Qt.NoFocus)

        dx = int(screenGeometry.width() / Tiles.x)
        dy = int(screenGeometry.height() / Tiles.y)

        for y in range(Tiles.y):
            for x in range(Tiles.x):
                label = CommandLabel(self.widget)
                label.setAlignment(Qt.AlignCenter)
                label.setGeometry(x * dx, y * dy, dx, dy)
                label.installEventFilter(self)
                label.setFocusPolicy(Qt.NoFocus)

                self.labels[(x, y)] = label

        self.updateGrid()

        self.widget.setWindowTitle("eyeput")
        # self.widget.show()

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

    @pyqtSlot(int, int)
    def onGaze(self, x, y):
        if not self.widget.isVisible():
            self.hoverTimer.stop()
            return

        screenGeometry = QApplication.primaryScreen().geometry()
        if screenGeometry.contains(x, y):
            xWidget = int(Tiles.x * x / screenGeometry.width())
            yWidget = int(Tiles.y * y / screenGeometry.height())
            widget = self.labels[(xWidget, yWidget)]
        else:
            widget = None

        if widget != self.hoverItem and self.gazeMoved:
            if self.hoverItem:
                self.hoverItem.setHovered(False)

            if widget != None and widget.isVisible():
                self.hoverTimer.start(selectionTime)
                widget.setHovered(True)
            else:
                self.hoverTimer.stop()

        self.gazeMoved = True
        self.hoverItem = widget

    @pyqtSlot()
    def selectItem(self):
        print("selectItem: " + self.hoverItem.id)
        self.hoverTimer.stop()
        self.hoverItem.setHovered(False)

        hold = self.state.hold

        if self.hoverItem.id == "hold":
            self.state.hold = not self.state.hold
            hold = self.state.hold

        elif self.hoverItem.id in Levels:
            self.setLevel(self.hoverItem.id)
            hold = True

        elif self.hoverItem.id in modifierColors:
            if self.hoverItem.id in self.state.modifiers:
                self.state.modifiers.remove(self.hoverItem.id)
            else:
                self.state.modifiers.add(self.hoverItem.id)
            hold = True

            self.updateGrid()

        elif self.hoverItem.id == "click":
            self.clickTimer.setInterval(50)
            self.clickTimer.start()
            self.mouseMoveTime = time()
            self.state.hold = False
            hold = False

        elif self.hoverItem.item.pressKey:
            self.pressKey(self.hoverItem.item.pressKey)
        else:
            self.pressKey(self.hoverItem.item.label)

        if not hold:
            self.toggle()

    @pyqtSlot()
    def toggle(self):
        self.gazeMoved = False
        self.widget.setVisible(not self.widget.isVisible())

        self.state.modifiers.clear()
        self.hoverTimer.stop()

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
        sock_keypress.try_send("+".join(list(self.state.modifiers) + [keyCode]))
        self.state.modifiers.clear()
        self.updateGrid()


class HotḱeyThread(QThread):
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        FIFO = Sockets.eyeput

        try:
            os.unlink(FIFO)
        except OSError:
            if os.path.exists(FIFO):
                raise

        os.mkfifo(FIFO)

        while True:
            with open(FIFO) as fifo:
                data = fifo.read()
                if len(data) > 0:
                    self.toggle_signal.emit()


class GazeThread(QThread):
    gaze_signal = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()

    def run(self):
        sock_gaze.listen()
        while True:
            print("Wait for a connection")
            sock_gaze.accept()
            print("Connected. Listening for keys ...")
            try:
                # Receive the data in small chunks and retransmit it
                while True:
                    gaze_frame = sock_gaze.receive()
                    [t, x, y] = gaze_frame.split(" ")
                    screenGeometry = QApplication.primaryScreen().geometry()
                    x = float(x) * screenGeometry.width()
                    y = float(y) * screenGeometry.height()

                    self.gaze_signal.emit(int(x), int(y))

            except RuntimeError as err:
                print(err)

            finally:
                print("Clean up the connection")
                sock_gaze.close_connection()


qapp = QApplication(sys.argv)
app = App()
# design flaw, see https://stackoverflow.com/q/4938723/6040478
signal.signal(signal.SIGINT, signal.SIG_DFL)


# print(keyboard.read_event())

hotkey_thread = HotḱeyThread()
hotkey_thread.toggle_signal.connect(app.toggle, Qt.QueuedConnection)

gaze_thread = GazeThread()
gaze_thread.gaze_signal.connect(app.onGaze, Qt.QueuedConnection)


hotkey_thread.start()
gaze_thread.start()
qapp.exec_()
