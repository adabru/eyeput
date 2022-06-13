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
    "shift": QColor(0xF5D491),
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
    circle_border = QColor(255, 255, 255, 0)
    circle = QColor(255, 255, 255, 50)
    circle_hovered = QColor(80, 255, 255, 150)
    circle_activated = QColor(255, 80, 80, 150)
    circle_toggled = QColor(80, 80, 255, 150)
    modifierBorder = QColor(168, 34, 3, 50)


class Times:
    # When looking outside the grid appears. But if the gaze stays outside, the grid disappears after this much seconds.
    out_of_screen = 0.5
    # The gaze has to stay this much seconds on one element to activate it.
    element_selection = 0.3
    # When activating the click element, you have this much seconds to move the mouse.
    mouse_movement = 0.6
    # You have to stay this much seconds on one spot for the click to trigger.
    click = 0.05
    # Blink time of a selected element
    selection_feedback = 0.1
