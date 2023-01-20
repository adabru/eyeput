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
    pause_lock = QMutex()
    tags = Tags()
    # maps blink pattern to command
    blink_mapping = {}

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

        self.status_widget = Status(self.widget, "-")

        self.gaze_pointer = GazePointer(self.widget)

        self.gaze_calibration = Calibration(self.widget, get_screen_geometry())
        self.gaze_calibration.end_signal.connect(self.on_calibration_end)
        self.gaze_filter = GazeFilter(self.gaze_calibration)

        # initialize blink patterns
        self.on_tag_changed("init", True)

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

    def on_blink(self, blink, blink_position):
        if not blink:
            return
        assert blink in self.blink_mapping, blink
        command = self.blink_mapping[blink]
        self.on_action(command, blink_position, False)

    @Slot(object)
    def on_gaze(self, input_frame: InputFrame):
        callbacks = {
            "on_blink": [self.on_blink],
            "on_position": [self.grid_widget.on_gaze],
            # "on_position": [self.gaze_pointer.on_gaze],
            # "on_variance": [self.status_widget.on_variance],
        }
        if self.tags.has("calibration"):
            callbacks = {
                "on_frame": [self.gaze_calibration.on_frame],
                "on_blink": [self.on_blink],
            }
        position_callback = callbacks.get("on_position", [])
        blink_callback = callbacks.get("on_blink", [])
        variance_callback = callbacks.get("on_variance", [])
        frame_callback = callbacks.get("on_frame", [])
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
        self.tags.unset_tag("calibration")

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

        # shared actions
        elif type(item) is GridLayerAction:
            self.tags.set_tag("grid")
            self.grid_widget.activate(item.layer)
            hide_grid = False
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
                self.tags.set_tag("cursor")
            elif item.id == "mouse_stop_move":
                target_position = self.gaze_pointer.stop_move(
                    blink_position[0], blink_position[1]
                )
                self.tags.unset_tag("cursor")
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
                self.tags.unset_tag("calibration")
            elif item.id == "select_and_hold":
                hide_grid = False
                self.grid_widget.on_gaze(blink_position[0], blink_position[1])
                self.grid_widget.select_item(False)
            elif item.id == "select_and_hide":
                hide_grid = False
                self.grid_widget.on_gaze(blink_position[0], blink_position[1])
                self.grid_widget.select_item(True)

        if hide_grid:
            self.tags.unset_tag("grid")

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
        elif tag == "debug_gaze":
            self.debug_gaze.setVisible(value)
        elif tag == "scrolling" and not value:
            self.scroll_timer.stop()
        elif tag == "grid":
            self.scroll_timer.stop()
            if not value:
                self.grid_widget.hide_delayed()
        elif tag == "calibration":
            if value:
                self.gaze_calibration.start()
            else:
                self.gaze_calibration.cancel()

        self.blink_mapping = {}
        if self.tags.has("calibration"):
            # exclusive
            self.blink_mapping = blink_commands["tag_calibration"]
        elif self.tags.has("pause"):
            # exclusive
            self.blink_mapping = blink_commands["tag_pause"]
        else:
            for tag in blink_commands:
                if tag[4:] in self.tags:
                    if tag[4:] == "scrolling" and self.tags.has("grid"):
                        continue
                    # prevent overwrite
                    self.blink_mapping |= blink_commands[tag] | self.blink_mapping
            self.blink_mapping |= blink_commands["default"] | self.blink_mapping
        self.gaze_filter.set_blink_patterns(self.blink_mapping)

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
