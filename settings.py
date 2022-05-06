from PyQt5.QtGui import QColor
from PyQt5.QtCore import QMarginsF


# DEFAULT: True - can be deactivated when debugging
activate_keypress = True

# The gaze may flicker. This is the threshold to acknowledge a border crossing between two areas.
border_threshold = QMarginsF(0.015, 0.015, 0.015, 0.015)

modifierColors = {
    "win": QColor(0x61A0AF),
    "alt": QColor(0x96C9DC),
    "ctrl": QColor(0xF9B9B7),
    "shiftl": QColor(0xF5D491),
}


class Sockets:
    gaze = "/tmp/gaze_input.sock"
    keypress = "/tmp/evdev_keypress.sock"
    eyeput = "/tmp/eyeput.fifo"


class Tiles:
    x = 14
    y = 6
    maxSide = 64


class Colors:
    text = QColor(0, 0, 0)
    item = "#44f0f0ff"
    circleBorder = QColor(255, 255, 255, 0)
    circle = QColor(255, 255, 255, 0)
    circle_hovered = QColor(80, 255, 255, 150)
    modifierBorder = QColor(168, 34, 3, 50)


class Times:
    # When looking outside the grid appears. But if the gaze stays outside, the grid disappears after deactivateAfter time.
    deactivateAfter = 0.5
    # The gaze has to stay selectAfter seconds on one element to activate it.
    selectAfter = 0.4
    # When activating the click element, you have delayBeforeClick seconds to move the mouse.
    delayBeforeClick = 0.6
    # You have to stay clickAfter seconds on one spot for the click to trigger.
    clickAfter = 0.05
