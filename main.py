#!/usr/bin/env python

import sys, signal, subprocess
from time import time

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, QRectF, QPoint, QPointF
from PyQt5.QtGui import QFont, QColor, QPainter, QPixmap
from pynput.mouse import Button, Controller

from levels import *
from command_label import CommandLabel as CommandLabel
from settings import *
from unix_socket import UnixSocket
from hotkey_thread import HotḱeyThread
from gaze_thread import GazeThread
from states import *
from gaze_pointer import GazePointer

mouse = Controller()

sock_keypress = UnixSocket(Sockets.keypress, 100)

# is set in App`s constructor
screenGeometry = None


def rel2abs(point):
    return QPoint(
        int(point.x() * screenGeometry.width()),
        int(point.y() * screenGeometry.height()),
    )


class App(QObject):
    widget = None
    gridWidget = None
    labels = {}
    gazePointer = None

    gridState = GridState()

    hoverItem = None

    hoverTimer = None
    clickTimer = None
    currPos = QPointF(0, 0)
    lastPos = QPointF(0, 0)
    counter = 0

    def __init__(self):
        super().__init__()

        global screenGeometry
        screenGeometry = QApplication.primaryScreen().geometry()

        self.hoverTimer = QTimer(self)
        self.hoverTimer.timeout.connect(self.selectItem)

        self.clickTimer = QTimer(self)
        self.clickTimer.timeout.connect(self.processMouse)

        self.gridState.activate_grid_signal.connect(self.activateGrid)

        self.widget = QWidget()
        self.widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.widget.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.widget.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            # bypass is not stable (https://doc.qt.io/qt-5/qwidget.html#showFullScreen)
            | Qt.X11BypassWindowManagerHint
        )
        # full screen has issues (https://doc.qt.io/qt-5/qwidget.html#showFullScreen)
        # self.widget.setWindowState(Qt.WindowFullScreen)

        self.widget.setGeometry(screenGeometry)
        self.widget.setFocusPolicy(Qt.NoFocus)

        self.gridWidget = QWidget(self.widget)
        self.gridWidget.hide()
        self.gridWidget.setGeometry(screenGeometry)
        self.gridWidget.setFocusPolicy(Qt.NoFocus)

        dx = int(screenGeometry.width() / Tiles.x)
        dy = int(screenGeometry.height() / Tiles.y)

        for y in range(Tiles.y):
            for x in range(Tiles.x):
                label = CommandLabel(self.gridWidget)
                label.setAlignment(Qt.AlignCenter)
                label.setGeometry(x * dx, y * dy, dx, dy)
                label.installEventFilter(self)
                label.setFocusPolicy(Qt.NoFocus)

                self.labels[(x, y)] = label

        self.updateGrid()

        self.gazePointer = GazePointer(self.widget)

        self.widget.setWindowTitle("eyeput")
        self.widget.show()

    def setLevel(self, levelId):
        self.gridState.lvl = levelId
        self.updateGrid()

    def setHoveredItem(self, widget):
        if widget != self.hoverItem:
            if widget:
                widget.setHovered(True)

            if self.hoverItem:
                self.hoverItem.setHovered(False)

            self.hoverItem = widget

    def updateGrid(self):
        for label in self.labels.values():
            label.id = None
            # self.hoverItem.setHovered(False)

        for key, item in Levels[self.gridState.lvl].items():
            label = self.labels[(item.x, item.y)]
            label.id = key
            label.setItem(item)
            label.setModifiers(self.gridState.modifiers)
            label.setText(item.label)
            label.show()

        for label in self.labels.values():
            if label.id == None:
                label.hide()

    def onGridGaze(self, x, y):
        if not QRectF(0, 0, 1, 1).contains(x, y):
            widget = None
            log_debug("outside")
            return

        xWidget = int(Tiles.x * x)
        yWidget = int(Tiles.y * y)
        if xWidget >= Tiles.x or yWidget >= Tiles.y:
            log_debug("invalid indices: " + str(xWidget) + ", " + str(yWidget))
            return
        widget = self.labels[(xWidget, yWidget)]

        if not widget.isVisible():
            widget = None
            log_debug("invisible")
            return

        if widget == self.hoverItem:
            log_debug("same")
            return

        if widget != None and widget.isVisible():
            self.hoverTimer.start(int(Times.selectAfter * 1000))
        else:
            self.hoverTimer.stop()

        self.setHoveredItem(widget)

    @pyqtSlot(float, float)
    def onGaze(self, x, y):
        self.currPos = QPointF(x, y)
        self.gridState.setMousePos(x, y)
        if self.gridState.state == GridActivationState.SELECTING:
            self.onGridGaze(x, y)

        if self.gazePointer.isVisible():
            self.gazePointer.move(rel2abs(self.currPos))

    @pyqtSlot()
    def selectItem(self):
        log_info("selectItem: " + self.hoverItem.id)
        self.hoverTimer.stop()

        if self.hoverItem.id == "hold":
            self.gridState.hold = not self.gridState.hold

        elif self.hoverItem.id in Levels:
            self.setLevel(self.hoverItem.id)

        elif self.hoverItem.id in modifierColors:
            if self.hoverItem.id in self.gridState.modifiers:
                self.gridState.modifiers.remove(self.hoverItem.id)
            else:
                self.gridState.modifiers.add(self.hoverItem.id)
            self.updateGrid()

        elif self.hoverItem.id == "click":
            self.clickTimer.setInterval(int(Times.clickAfter * 1000))
            self.clickTimer.start()
            self.mouseMoveTime = time()
            self.gridState.hold = False
            self.gridState.selectionCompleted()

        elif isinstance(self.hoverItem.item, KeyAction):
            self.pressKey(self.hoverItem.item.pressKey)
            self.gridState.selectionCompleted()

        elif isinstance(self.hoverItem.item, CmdAction):
            subprocess.Popen(self.hoverItem.item.cmd, shell=True)
            self.gridState.selectionCompleted()

    @pyqtSlot()
    def toggle(self):
        self.setHoveredItem(None)
        self.gridWidget.setVisible(not self.gridWidget.isVisible())

        self.gridState.modifiers.clear()
        self.hoverTimer.stop()

    @pyqtSlot()
    def onHotkeyPressed(self):
        self.gridState.hotkeyTriggered()

        if not QRectF(0, 0, 1, 1).contains(self.currPos):
            log_debug("hotkey pressed outside")
            return

        xWidget = int(Tiles.x * self.currPos.x())
        yWidget = int(Tiles.y * self.currPos.y())
        widget = self.labels[(xWidget, yWidget)]
        self.setHoveredItem(widget)

        if widget:
            log_debug("hotkey pressed over: " + widget.id)

    @pyqtSlot(str)
    def activateGrid(self, lvl):
        if lvl:
            self.updateGrid()

        if lvl and not self.gridWidget.isVisible():
            self.toggle()
        elif not lvl and self.gridWidget.isVisible():
            self.toggle()

    @pyqtSlot()
    def processMouse(self):
        dist = rel2abs(self.currPos - self.lastPos).manhattanLength()

        if dist > 10:
            self.mouseMoveTime = time()
            log_debug("mouse moved: " + str(dist))

        elif time() - self.mouseMoveTime > Times.delayBeforeClick:
            log_debug("mouse click")
            pos = rel2abs(self.currPos)
            oldPos = mouse.position

            mouse.position = (pos.x(), pos.y())
            mouse.click(Button.left, 1)
            mouse.position = oldPos

            self.clickTimer.stop()

        self.lastPos = self.currPos

    def pressKey(self, keyCode):
        if activate_keypress:
            sock_keypress.try_send("+".join(list(self.gridState.modifiers) + [keyCode]))
        else:
            print("WARN: keypresses are deactivated in settings!")
        self.gridState.modifiers.clear()
        self.updateGrid()


qapp = QApplication(sys.argv)
app = App()
# design flaw, see https://stackoverflow.com/q/4938723/6040478
signal.signal(signal.SIGINT, signal.SIG_DFL)


# print(keyboard.read_event())

hotkey_thread = HotḱeyThread()
hotkey_thread.hotkey_signal.connect(app.onHotkeyPressed, Qt.QueuedConnection)

gaze_thread = GazeThread()
gaze_thread.gaze_signal.connect(app.onGaze, Qt.QueuedConnection)


hotkey_thread.start()
gaze_thread.start()
qapp.exec_()
