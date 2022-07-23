#!/usr/bin/env python

import sys, signal, time

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, QPoint, QPointF, QMutex

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
    pause_lock = QMutex()

    scroll_timer = None
    # click_timer = None
    # currPos = QPointF(0, 0)
    # lastPos = QPointF(0, 0)

    def __init__(self):
        super().__init__()

        global screen_geometry
        screen_geometry = QApplication.primaryScreen().geometry()

        # self.click_timer = QTimer(self)
        # self.click_timer.timeout.connect(self.processMouse)
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setInterval(int(Times.scroll_interval * 1000))
        self.scroll_timer.timeout.connect(self.scroll_step)

        # self.activation.activate_grid_signal.connect(self.activation_changed)

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

        self.gaze_pointer = GazePointer(self.widget, rel2abs)

        self.set_mode(Modes.enabled)

        self.widget.setWindowTitle("eyeput")
        self.widget.show()

        # self.graph = Graph()
        # self.graph.setup()

    def set_mode(self, mode):
        self.mode = mode
        self.status_widget.set_mode(self.mode)
        self.scroll_timer.stop()
        gaze_filter.set_blink_patterns(blink_commands[self.mode])

    def on_blink(self, blink, blink_position):
        if not blink:
            return
        assert blink in blink_commands[self.mode], self.mode + " " + blink
        id = blink_commands[self.mode][blink]
        if id == "mode_enabled":
            self.set_mode(Modes.enabled)
        elif id == "mode_paused":
            self.set_mode(Modes.paused)
        elif id == "mode_scrolling":
            self.set_mode(Modes.scrolling)
        # elif id == "mouse_move":
        #     position = rel2abs(QPointF(blink_position[0], blink_position[1]))
        #     external.mouse_move(position.x(), position.y())
        #     self.gaze_pointer.on_gaze(position)
        elif id == "mouse_start_move":
            self.gaze_pointer.start_move(blink_position[0], blink_position[1])
            self.set_mode(Modes.cursor)
        elif id == "mouse_stop_move":
            target_position = self.gaze_pointer.stop_move(
                blink_position[0], blink_position[1]
            )
            self.set_mode(Modes.enabled)
            external.mouse_move(target_position.x(), target_position.y())
        elif id == "left_click":
            external.left_click()
        elif id == "right_click":
            external.right_click()
        elif id == "scroll_up":
            self.scroll_direction = 1
            self.scroll_timer.start()
        elif id == "scroll_down":
            self.scroll_direction = -1
            self.scroll_timer.start()
        elif id == "scroll_stop":
            self.scroll_timer.stop()

    @pyqtSlot(float, float, float, float, float)
    def on_gaze(self, t, l0, l1, r0, r1):
        callbacks = {
            Modes.enabled: {
                "on_blink": self.on_blink,
                # "on_variance": self.status_widget.on_variance,
            },
            Modes.cursor: {
                "on_blink": self.on_blink,
                "on_position": self.gaze_pointer.on_gaze,
            },
            Modes.paused: {
                "on_blink": self.on_blink,
            },
            Modes.scrolling: {
                "on_blink": self.on_blink,
            },
        }
        position_callback = callbacks[self.mode].get("on_position", None)
        blink_callback = callbacks[self.mode].get("on_blink", None)
        variance_callback = callbacks[self.mode].get("on_variance", None)
        [x, y, flips, flip_position, l_variance, r_variance,] = gaze_filter.transform(
            t,
            l0,
            l1,
            r0,
            r1,
            position=position_callback,
            blink=blink_callback,
            variance=variance_callback,
        )
        if position_callback:
            position_callback(x, y)
        if blink_callback:
            blink_callback(flips, flip_position)
        if variance_callback:
            variance_callback(l_variance, r_variance)
        # self.graph.addPoint(t, l0, l1, r0, r1, x, y)
        # self.currPos = QPointF(x, y)
        # self.activation.update_gaze(x, y)
        # if self.activation.state == GridActivationState.SELECTING:
        #     self.grid_widget.on_gaze(x, y)

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
        elif isinstance(item, MouseAction) and item.id == "left_click_delayed":
            self.click_timer.setInterval(int(Times.click * 1000))
            self.click_timer.start()
            self.mouseMoveTime = time.time()
        elif isinstance(item, CmdAction):
            external.exec(item.cmd)

        if hide:
            self.activation.go_idle()

    @pyqtSlot()
    def scroll_step(self):
        external.scroll(self.scroll_direction)

    # @pyqtSlot()
    # def processMouse(self):
    #     dist = rel2abs(self.currPos - self.lastPos).manhattanLength()

    #     if dist > 10:
    #         self.mouseMoveTime = time.time()
    #         log_debug("mouse moved: " + str(dist))

    #     elif time.time() - self.mouseMoveTime > Times.mouse_movement:
    #         log_debug("mouse click")
    #         pos = rel2abs(self.currPos)
    #         external.left_click(pos)
    #         self.click_timer.stop()

    #     self.lastPos = self.currPos


qapp = QApplication(sys.argv)
app = App()
# design flaw, see https://stackoverflow.com/q/4938723/6040478
signal.signal(signal.SIGINT, signal.SIG_DFL)


# print(keyboard.read_event())

hotkey_thread = HotḱeyThread()
hotkey_thread.hotkey_signal.connect(app.onHotkeyPressed, Qt.QueuedConnection)

gaze_thread = GazeThread(app.pause_lock)
gaze_thread.gaze_signal.connect(app.on_gaze, Qt.QueuedConnection)

hotkey_thread.start()
gaze_thread.start()
qapp.exec_()
