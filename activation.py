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
            return self.rect.contains(x, y)
        else:
            return (self.rect - border_threshold).contains(x, y)


areas = [
    Area("center", QRectF(0, 0, 1, 1), None),
    Area("diag top left", QRectF(-1, -1, 1, 1), "textCmds"),
    Area("top left", QRectF(0, -1, 0.5, 1), "keyboard1"),
    Area("top right", QRectF(0.5, -1, 0.5, 1), "keyboard2"),
    Area("left", QRectF(-1, 0, 1, 1), "apps"),
]


class GridActivationState(Enum):
    IDLE = 0
    GRID_ACTIVATE = 1
    SELECTING = 2
    GRID_DEACTIVATE = 3


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

        # TRANS 1-3
        if self.state == GridActivationState.GRID_ACTIVATE:
            log_debug("TRANS 1-3")
            self.state = GridActivationState.GRID_DEACTIVATE
            self._trigger()
        else:
            log_debug(
                "invalid state when deactivateTimer triggered: " + self.state.name
            )

    def _trigger(self, area=None):
        """..."""
        self.activate_grid_signal.emit(area and area.target)

    def go_idle(self):
        # TRANS 2-0
        log_debug("TRANS 2-0")
        self.state = GridActivationState.IDLE
        self._trigger()

    def hotkeyTriggered(self):
        # TRANS 0-2
        if self.state == GridActivationState.IDLE:
            log_debug("TRANS 0-2 hotkey")
            self.state = GridActivationState.SELECTING
            self._trigger(areas[0])

        # TRANS 2-0
        elif self.state == GridActivationState.SELECTING:
            log_debug("TRANS 2-0 hotkey")
            self.state = GridActivationState.IDLE
            self._trigger()

        # TRANS 1-3
        elif self.state == GridActivationState.GRID_ACTIVATE:
            log_debug("TRANS 1-3 hotkey")
            self.state = GridActivationState.GRID_DEACTIVATE
            self._trigger()

        # TRANS 3-1
        elif self.state == GridActivationState.GRID_DEACTIVATE:
            log_debug("TRANS 3-1 hotkey")
            self.state = GridActivationState.GRID_ACTIVATE
            self._trigger(areas[0])

    def update_gaze(self, x, y):
        area = self._find_area(x, y)
        gazeIsInside = area and area.label == "center"

        # TRANS 0-0
        if self.state == GridActivationState.IDLE and gazeIsInside:
            pass

        # TRANS 0-1
        elif self.state == GridActivationState.IDLE and not gazeIsInside:
            log_debug("TRANS 0-1 : " + str(area and area.label))
            self.state = GridActivationState.GRID_ACTIVATE
            self._trigger(area)
            self.deactivateTimer.start(int(Times.deactivateAfter * 1000))

        # TRANS 1-1
        elif self.state == GridActivationState.GRID_ACTIVATE and not gazeIsInside:
            if area != self.last_area:
                log_debug("TRANS 1-1 : " + str(area and area.label))
                self._trigger(area)
                self.deactivateTimer.start(int(Times.deactivateAfter * 1000))

        # TRANS 1-2
        elif self.state == GridActivationState.GRID_ACTIVATE and gazeIsInside:
            log_debug("TRANS 1-2")
            self.state = GridActivationState.SELECTING
            self.deactivateTimer.stop()

        # TRANS 2-3
        elif self.state == GridActivationState.SELECTING and not gazeIsInside:
            log_debug("TRANS 2-3")
            self.state = GridActivationState.GRID_DEACTIVATE
            self._trigger()

        # TRANS 3-0
        elif self.state == GridActivationState.GRID_DEACTIVATE and gazeIsInside:
            log_debug("TRANS 3-0")
            self.state = GridActivationState.IDLE

        self.last_area = area
