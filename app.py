#!/usr/bin/env python

import sys, signal, time

from PySide2.QtWidgets import QApplication, QWidget
from PySide2.QtCore import QObject, Slot, Qt, QTimer, QPoint, QPointF, QMutex

from settings import *
from util import *
from hotkey_thread import HotḱeyThread
from gaze_thread import *
from gaze_filter import *
from gaze_calibration import *
from activation import *
from shared_tags import *
from gaze_pointer import GazePointer
from label_grid import *
from status import *
import external
from tiles import *

from debug_gaze import DebugGaze
from graph import *


class App(QObject):
    widget = None
    grid_widget = None
    status_widget = None
    gaze_pointer = None
    debug_gaze: DebugGaze

    activation = GridActivation()
    mode = Modes.enabled
    previous_mode = None
    pause_lock = QMutex()
    tags = Tags()

    scroll_timer = None
    # click_timer = None
    # currPos = QPointF(0, 0)
    # lastPos = QPointF(0, 0)

    executor_signal = Signal(str, object)
    tag_changed_signal = Signal(str, bool)

    def __init__(self, bus):
        super().__init__()
        self.bus = bus

        self.qapp = QApplication(sys.argv)
        # design flaw, see https://stackoverflow.com/q/4938723/6040478
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        set_screen_geometry(QApplication.primaryScreen().geometry())

        # self.click_timer = QTimer(self)
        # self.click_timer.timeout.connect(self.processMouse)
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setInterval(int(Times.scroll_interval * 1000))
        self.scroll_timer.timeout.connect(self.scroll_step)

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

        self.widget.setGeometry(get_screen_geometry())
        self.widget.setFocusPolicy(Qt.NoFocus)

        self.grid_widget = LabelGrid(self.widget, get_screen_geometry(), self.tags)
        # self.grid_widget.hide()
        self.grid_widget.action_signal.connect(self.on_action)

        self.status_widget = Status(self.widget, self.mode)

        self.gaze_pointer = GazePointer(self.widget)

        self.gaze_calibration = Calibration(self.widget, get_screen_geometry())
        self.gaze_calibration.end_signal.connect(self.on_calibration_end)
        self.gaze_filter = GazeFilter(self.gaze_calibration)

        self.set_mode(Modes.enabled)

        self.widget.setWindowTitle("eyeput")
        self.widget.show()

        self.debug_gaze = DebugGaze(self.widget)

        self.tag_sharing = TagSharing(self.tags, self.bus, "eyeput.tags", "talon.tags")
        self.tag_changed_signal.connect(self.on_tag_changed, Qt.QueuedConnection)
        self.tags.tag_changed.subscribe(self.tag_changed_signal.emit)

        self.executor_signal.connect(self.on_executor_command, Qt.QueuedConnection)
        self.bus.schedule(
            self.bus.subscribe_signal(
                "executor", "command_received", self.executor_signal.emit
            )
        )

        # self.graph = Graph()
        # self.graph.setup()

    def set_mode(self, mode):
        if mode == Modes._previous:
            mode = self.previous_mode
            self.previous_mode = Modes.paused
        elif self.previous_mode != self.mode:
            self.previous_mode = self.mode
        self.mode = mode
        self.status_widget.set_mode(self.mode)
        self.scroll_timer.stop()
        self.gaze_filter.set_blink_patterns(blink_commands[self.mode])
        if mode == Modes.calibration:
            self.gaze_calibration.start()

    def on_blink(self, blink, blink_position):
        if not blink:
            return
        assert blink in blink_commands[self.mode], self.mode + " " + blink
        command = blink_commands[self.mode][blink]
        self.on_action(command, blink_position, True)

    @Slot(object)
    def on_gaze(self, input_frame: InputFrame):
        callbacks = {
            Modes.enabled: {
                "on_blink": [self.on_blink],
                # "on_variance": [self.status_widget.on_variance],
            },
            Modes.cursor: {
                "on_blink": [self.on_blink],
                "on_position": [self.gaze_pointer.on_gaze],
            },
            Modes.grid: {
                "on_blink": [self.on_blink],
                "on_position": [self.grid_widget.on_gaze],
            },
            Modes.paused: {
                "on_blink": [self.on_blink],
            },
            Modes.scrolling: {
                "on_blink": [self.on_blink],
                "on_position": [self.grid_widget.on_gaze],
            },
            Modes.calibration: {
                "on_frame": [self.gaze_calibration.on_frame],
                "on_blink": [self.on_blink],
            },
        }
        position_callback = callbacks[self.mode].get("on_position", [])
        blink_callback = callbacks[self.mode].get("on_blink", [])
        variance_callback = callbacks[self.mode].get("on_variance", [])
        frame_callback = callbacks[self.mode].get("on_frame", [])
        if self.debug_gaze.isVisible():
            frame_callback.append(self.debug_gaze.on_frame)
        filtered_frame = self.gaze_filter.transform(
            input_frame,
            position=position_callback,
            blink=blink_callback,
            variance=variance_callback,
        )
        for callback in position_callback:
            callback(
                filtered_frame.screen_position[0], filtered_frame.screen_position[1]
            )
        for callback in blink_callback:
            callback(filtered_frame.flips, filtered_frame.flip_position)
        for callback in variance_callback:
            callback(filtered_frame.l_variance, filtered_frame.r_variance)
        for callback in frame_callback:
            callback(filtered_frame)
        # self.graph.addPoint(t, l0, l1, r0, r1, x, y)
        # self.currPos = QPointF(x, y)

    @Slot()
    def on_calibration_end(self):
        self.set_mode(Modes._previous)

    @Slot()
    def onHotkeyPressed(self):
        self.activation.hotkeyTriggered()
        self.grid_widget.on_gaze(
            self.currPos.x(), self.currPos.y(), after_activation=True
        )

    @Slot(str)
    def activation_changed(self, label):
        self.grid_widget.activate(label)

    @Slot(object, object, bool)
    def on_action(self, item: Action, params, hide_grid):
        # grid actions
        if type(item) is KeyAction:
            modifiers = params
            external.press_key("+".join(list(modifiers) + [item.key()]))
        elif type(item) is MouseAction and item.id == "left_click_delayed":
            self.click_timer.setInterval(int(Times.click * 1000))
            self.click_timer.start()
            self.mouseMoveTime = time.time()
        elif type(item) is ShellAction:
            external.exec(item.cmd)
        elif type(item) is InternalAction:
            if item.id == "debug_gaze":
                self.debug_gaze.setVisible(not self.debug_gaze.isVisible())

        # shared actions
        elif type(item) is GridLayerAction:
            self.set_mode(Modes.grid)
            self.grid_widget.activate(item.layer)
            hide_grid = False
        elif type(item) is SetModeAction:
            self.set_mode(item.mode)
        elif type(item) is TagAction:
            match item.action:
                case "set":
                    self.tags.set_tag(item.tag)
                case "unset":
                    self.tags.unset_tag(item.tag)
                case "toggle":
                    self.tags.toggle_tag(item.tag)

        # blink actions
        elif type(item) is BlinkAction:
            blink_position = params
            # elif id == "mouse_move":
            #     position = rel2abs(blink_position)
            #     external.mouse_move(position.x(), position.y())
            #     self.gaze_pointer.on_gaze(position)
            if item.id == "mouse_start_move":
                self.gaze_pointer.start_move(blink_position[0], blink_position[1])
                self.set_mode(Modes.cursor)
            elif item.id == "mouse_stop_move":
                target_position = self.gaze_pointer.stop_move(
                    blink_position[0], blink_position[1]
                )
                self.set_mode(Modes.enabled)
                external.mouse_move(target_position.x(), target_position.y())
            elif item.id == "left_click":
                external.left_click()
            elif item.id == "right_click":
                external.right_click()
            elif item.id == "scroll_up":
                self.scroll_direction = 1
                self.scroll_timer.start()
            elif item.id == "scroll_down":
                self.scroll_direction = -1
                self.scroll_timer.start()
            elif item.id == "scroll_stop":
                self.scroll_timer.stop()
            elif item.id == "calibration_next":
                self.gaze_calibration.next_point()
            elif item.id == "calibration_cancel":
                self.gaze_calibration.cancel()
                self.set_mode(Modes._previous)
            elif item.id == "select_and_hold":
                hide_grid = False
                self.grid_widget.on_gaze(blink_position[0], blink_position[1])
                self.grid_widget.select_item(False)
            elif item.id == "select_and_hide":
                hide_grid = False
                self.grid_widget.on_gaze(blink_position[0], blink_position[1])
                self.set_mode(Modes._previous)
                self.grid_widget.select_item(True)

        if hide_grid:
            self.grid_widget.hide_delayed()

    @Slot()
    def scroll_step(self):
        external.scroll(self.scroll_direction)

    # @Slot()
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

    @Slot(str, object)
    def on_executor_command(self, command_id, data):
        if command_id == "left_click" and self.tags.has("follow_until_click"):
            self.tags.unset_tag("follow_until_click")
            self.tags.unset_tag("follow")

    @Slot(str, bool)
    def on_tag_changed(self, tag, value):
        if tag == "follow" and value == False:
            self.tags.unset_tag("follow_until_click")
        elif tag == "follow_until_click" and value == True:
            self.tags.set_tag("follow")

        if self.grid_widget.isVisible():
            self.grid_widget.update_grid()

    def run(self):
        hotkey_thread = HotḱeyThread()
        hotkey_thread.hotkey_signal.connect(self.onHotkeyPressed, Qt.QueuedConnection)

        gaze_thread = GazeThread(self.pause_lock)
        gaze_thread.gaze_signal.connect(self.on_gaze, Qt.QueuedConnection)

        hotkey_thread.start()
        gaze_thread.start()
        self.qapp.exec_()
