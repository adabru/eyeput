#!/usr/bin/env python

from statistics import mode
import sys, signal, time

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, QPoint, QPointF

from settings import *
from hotkey_thread import HotḱeyThread
from gaze_thread import GazeThread
from gaze_filter import *
from activation import *
from gaze_pointer import GazePointer
from label_grid import *
from status import *
import external
from tiles import *

from graph import *


# is set in App`s constructor
screen_geometry = None

gaze_filter = GazeFilter()


def rel2abs(point):
    return QPoint(
        int(point.x() * screen_geometry.width()),
        int(point.y() * screen_geometry.height()),
    )


class App(QObject):
    widget = None
    grid_widget = None
    status_widget = None
    gaze_pointer = None

    activation = GridActivation()
    mode = Modes.enabled

    click_timer = None
    currPos = QPointF(0, 0)
    lastPos = QPointF(0, 0)
    counter = 0

    def __init__(self):
        super().__init__()

        global screen_geometry
        screen_geometry = QApplication.primaryScreen().geometry()

        self.click_timer = QTimer(self)
        self.click_timer.timeout.connect(self.processMouse)

        self.activation.activate_grid_signal.connect(self.activation_changed)

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

        self.widget.setGeometry(screen_geometry)
        self.widget.setFocusPolicy(Qt.NoFocus)

        self.grid_widget = LabelGrid(self.widget, screen_geometry)
        self.grid_widget.hide()
        self.grid_widget.action_signal.connect(self.grid_action)

        self.status_widget = Status(self.widget, self.mode)

        self.gaze_pointer = GazePointer(self.widget)

        self.widget.setWindowTitle("eyeput")
        self.widget.show()

        # self.graph = Graph()
        # self.graph.setup()

    def on_blink(self, l, r):
        if l and not r:
            external.left_click()
        elif not l and r:
            external.right_click()

    @pyqtSlot(float, float, float, float, float)
    def on_gaze(self, t, l0, l1, r0, r1):
        [x, y, blink, l_variance, r_variance] = gaze_filter.transform(t, l0, l1, r0, r1)

        # self.graph.addPoint(t, l0, l1, r0, r1, x, y)

        # self.on_blink(l_blink, r_blink)
        self.status_widget.on_gaze(l_variance, r_variance)

        self.currPos = QPointF(x, y)
        self.activation.update_gaze(x, y)
        if self.activation.state == GridActivationState.SELECTING:
            self.grid_widget.on_gaze(x, y)
        self.gaze_pointer.on_gaze(rel2abs(self.currPos))

    @pyqtSlot()
    def onHotkeyPressed(self):
        self.activation.hotkeyTriggered()
        self.grid_widget.on_gaze(
            self.currPos.x(), self.currPos.y(), after_activation=True
        )

    @pyqtSlot(str)
    def activation_changed(self, label):
        self.grid_widget.activate(label)

    @pyqtSlot(object, object, bool)
    def grid_action(self, item, params, hide):
        if isinstance(item, KeyAction):
            modifiers = params
            external.press_key("+".join(list(modifiers) + [item.pressKey]))
        elif isinstance(item, OtherAction) and item.id == "left_click":
            self.click_timer.setInterval(int(Times.click * 1000))
            self.click_timer.start()
            self.mouseMoveTime = time.time()
        elif isinstance(item, CmdAction):
            external.exec(item.cmd)

        if hide:
            self.activation.go_idle()

    @pyqtSlot()
    def processMouse(self):
        dist = rel2abs(self.currPos - self.lastPos).manhattanLength()

        if dist > 10:
            self.mouseMoveTime = time.time()
            log_debug("mouse moved: " + str(dist))

        elif time.time() - self.mouseMoveTime > Times.mouse_movement:
            log_debug("mouse click")
            pos = rel2abs(self.currPos)
            external.left_click(pos)
            self.click_timer.stop()

        self.lastPos = self.currPos


qapp = QApplication(sys.argv)
app = App()
# design flaw, see https://stackoverflow.com/q/4938723/6040478
signal.signal(signal.SIGINT, signal.SIG_DFL)


# print(keyboard.read_event())

hotkey_thread = HotḱeyThread()
hotkey_thread.hotkey_signal.connect(app.onHotkeyPressed, Qt.QueuedConnection)

gaze_thread = GazeThread()
gaze_thread.gaze_signal.connect(app.on_gaze, Qt.QueuedConnection)

hotkey_thread.start()
gaze_thread.start()
qapp.exec_()
