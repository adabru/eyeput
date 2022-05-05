from enum import Enum
from PyQt5.QtCore import (
    pyqtSignal,
    QTimer,
    QObject,
    QRectF,
)

from logger import *
from settings import *


class Area:
    def __init__(self, label, rect, target):
        """..."""
        self.label = label
        self.rect = rect
        self.target = target

    def contains(self, x, y, last_area):
        """..."""
        if last_area == self:
            return (self.rect + border_threshold).contains(x, y)
        else:
            return (self.rect - border_threshold).contains(x, y)


areas = [
    Area("center", QRectF(0, 0, 1, 1), None),
    Area("diag top left", QRectF(-1, -1, 1, 1), "textCmds"),
    Area("top left", QRectF(0, -1, 0.5, 1), "keyboard1"),
    Area("top right", QRectF(0.5, -1, 0.5, 1), "keyboard2"),
    # Area("left", QRectF(-1, 0, 1, 1), "apps"),
]


class GridActivationState(Enum):
    # waiting for activation
    IDLE = 0
    # grid is visible, gaze is outside
    PRE_SELECTING = 1
    # grid is visible, gaze is selecting
    SELECTING = 2
    # grid is invisible, gaze is outside
    PRE_IDLE = 3


class GridActivation(QObject):
    state = GridActivationState.IDLE
    last_area = None

    deactivateTimer = None

    activate_grid_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.deactivateTimer = QTimer(self)
        self.deactivateTimer.timeout.connect(self._deactivateGrid)

    def _find_area(self, x, y):
        for area in areas:
            if area.contains(x, y, self.last_area):
                return area
        return None

    def _deactivateGrid(self):
        self.deactivateTimer.stop()

        if self.state == GridActivationState.PRE_SELECTING:
            log_debug("PRE_SELECTING → PRE_IDLE")
            self.state = GridActivationState.PRE_IDLE
            self._trigger()
        else:
            log_debug(
                "invalid state when deactivateTimer triggered: " + self.state.name
            )

    def _trigger(self, area=None):
        """..."""
        self.activate_grid_signal.emit(area and area.target)

    def go_idle(self):
        log_debug("SELECTING → IDLE")
        self.state = GridActivationState.IDLE
        self._trigger()

    def hotkeyTriggered(self):
        if self.state == GridActivationState.IDLE:
            log_debug("IDLE → SELECTING hotkey")
            self.state = GridActivationState.SELECTING
            self._trigger(areas[0])

        elif self.state == GridActivationState.SELECTING:
            log_debug("SELECTING → IDLE hotkey")
            self.state = GridActivationState.IDLE
            self._trigger()

        elif self.state == GridActivationState.PRE_SELECTING:
            log_debug("PRE_SELECTING → PRE_IDLE hotkey")
            self.state = GridActivationState.PRE_IDLE
            self._trigger()

        elif self.state == GridActivationState.PRE_IDLE:
            log_debug("PRE_IDLE → PRE_SELECTING hotkey")
            self.state = GridActivationState.PRE_SELECTING
            self._trigger(areas[0])

    def update_gaze(self, x, y):
        out_of_bounds_or_blinking = x == 0 and y == 0
        if not out_of_bounds_or_blinking:
            area = self._find_area(x, y)
            gaze_is_inside = area and area.label == "center"
            gaze_is_outside = not gaze_is_inside

        if self.state == GridActivationState.IDLE:
            if not out_of_bounds_or_blinking and gaze_is_outside:
                log_debug("IDLE → PRE_SELECTING : " + str(area and area.label))
                self.state = GridActivationState.PRE_SELECTING
                self._trigger(area)
                self.deactivateTimer.start(int(Times.deactivateAfter * 1000))

        elif self.state == GridActivationState.PRE_SELECTING:
            if out_of_bounds_or_blinking:
                log_debug("PRE_SELECTING → PRE_IDLE")
                self.state = GridActivationState.PRE_IDLE
                self._trigger()
            elif gaze_is_outside and area != self.last_area:
                log_debug("PRE_SELECTING → PRE_SELECTING : " + str(area and area.label))
                self._trigger(area)
                self.deactivateTimer.start(int(Times.deactivateAfter * 1000))
            elif gaze_is_inside:
                log_debug("PRE_SELECTING → SELECTING")
                self.state = GridActivationState.SELECTING
                self.deactivateTimer.stop()

        elif self.state == GridActivationState.SELECTING:
            if out_of_bounds_or_blinking or gaze_is_outside:
                log_debug("SELECTING → PRE_IDLE")
                self.state = GridActivationState.PRE_IDLE
                self._trigger()

        elif self.state == GridActivationState.PRE_IDLE:
            if not out_of_bounds_or_blinking and gaze_is_inside:
                log_debug("PRE_IDLE → IDLE")
                self.state = GridActivationState.IDLE

        if not out_of_bounds_or_blinking:
            self.last_area = area
