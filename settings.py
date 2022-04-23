from PyQt5.QtGui import QColor

selectionTime = 300
delayBeforeClick = 0.6
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


class Colors:
    text = "#00ffffff"
    item = "#44f0f0ff"
    circle = "40ffffff"
    circle_hovered = ""
