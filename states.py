from enum import Enum
from PyQt5.QtCore import (
    pyqtSignal,
    QTimer,
    QObject,
    QRectF,
)

from levels import Layout, Levels
from logger import *
from settings import *


class GridActivationState(Enum):
    IDLE = 0
    GRID_ACIVATE = 1
    SELECTING = 2
    GRID_DEACTIVATE = 3


class GridState(QObject):
    state = GridActivationState.IDLE
    lvl = next(iter(Levels))
    hold = False
    modifiers = set()

    deactivateTimer = None

    activate_grid_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.deactivateTimer = QTimer(self)
        self.deactivateTimer.timeout.connect(self._deactivateGrid)

    def _deactivateGrid(self):
        self.deactivateTimer.stop()

        # TRANS 1-3
        if self.state == GridActivationState.GRID_ACIVATE:
            log_debug("TRANS 1-3")
            self.state = GridActivationState.GRID_DEACTIVATE
            self.activate_grid_signal.emit("")
        else:
            log_debug(
                "invalid state when deactivateTimer triggered: " + self.state.name
            )

    def selectionCompleted(self):
        if not self.hold:
            # TRANS 2-0
            log_debug("TRANS 2-0")
            self.state = GridActivationState.IDLE
            self.activate_grid_signal.emit("")

    def hotkeyTriggered(self):
        # TRANS 0-2
        if self.state == GridActivationState.IDLE:
            log_debug("TRANS 0-2 hotkey")
            self.state = GridActivationState.SELECTING
            self.activate_grid_signal.emit(self.lvl)

        # TRANS 2-0
        elif self.state == GridActivationState.SELECTING:
            log_debug("TRANS 2-0 hotkey")
            self.state = GridActivationState.IDLE
            self.activate_grid_signal.emit("")

        # TRANS 1-3
        elif self.state == GridActivationState.GRID_ACIVATE:
            log_debug("TRANS 1-3 hotkey")
            self.state = GridActivationState.GRID_DEACTIVATE
            self.activate_grid_signal.emit("")

        # TRANS 3-1
        elif self.state == GridActivationState.GRID_DEACTIVATE:
            log_debug("TRANS 3-1 hotkey")
            self.state = GridActivationState.GRID_ACIVATE
            self.activate_grid_signal.emit(self.lvl)

    def setMousePos(self, x, y):
        gazeIsInside = QRectF(0, 0, 1, 1).contains(x, y)

        # TRANS 0-0
        if self.state == GridActivationState.IDLE and gazeIsInside:
            pass

        # TRANS 0-1
        elif self.state == GridActivationState.IDLE and not gazeIsInside:
            self.state = GridActivationState.GRID_ACIVATE

            self.lvl = Layout.findLevel(x, y)
            if self.lvl:
                log_debug("TRANS 0-1 : " + self.lvl)
            else:
                log_debug("TRANS 0-1 : none")
            self.activate_grid_signal.emit(self.lvl)
            self.deactivateTimer.start(Times.deactivateAfter)

        # TRANS 1-1
        elif self.state == GridActivationState.GRID_ACIVATE and not gazeIsInside:
            newLvl = Layout.findLevel(x, y)
            if self.lvl != newLvl:
                if newLvl:
                    log_debug("TRANS 1-1 : " + newLvl)
                else:
                    log_debug("TRANS 1-1 : none")

                self.lvl = newLvl
                self.activate_grid_signal.emit(self.lvl)
                self.deactivateTimer.start(Times.deactivateAfter)

        # TRANS 1-2
        elif self.state == GridActivationState.GRID_ACIVATE and gazeIsInside:
            log_debug("TRANS 1-2")
            self.state = GridActivationState.SELECTING

            self.deactivateTimer.stop()

        # TRANS 2-3
        elif self.state == GridActivationState.SELECTING and not gazeIsInside:
            log_debug("TRANS 2-3")
            self.state = GridActivationState.GRID_DEACTIVATE

            self.activate_grid_signal.emit("")

        # TRANS 3-0
        elif self.state == GridActivationState.GRID_DEACTIVATE and gazeIsInside:
            log_debug("TRANS 3-0")
            self.state = GridActivationState.IDLE
