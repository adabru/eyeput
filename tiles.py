from dataclasses import dataclass, field
import os.path

from PySide2.QtCore import QRectF, QPointF

from settings import *


@dataclass
class Action:
    label: str
    img: str


@dataclass
class InternalAction(Action):
    id: str


@dataclass
class TagAction(Action):
    tag: str
    action: str = "toggle"


@dataclass
class MouseAction(Action):
    id: str


@dataclass
class BlinkAction(Action):
    id: str


@dataclass
class KeyAction(Action):
    pressKey: str = None

    def key(self):
        return self.pressKey or self.label


@dataclass
class ShellAction(Action):
    cmd: str = None


@dataclass
class GridLayerAction(Action):
    layer: str = None
    modifiers: set = field(default_factory=set)


tile_groups = {
    "letters": {
        "tiles": {
            "a": (KeyAction("a", None), KeyAction("shift+a", None)),
            "b": (KeyAction("b", None), KeyAction("shift+b", None)),
            "c": (KeyAction("c", None), KeyAction("shift+c", None)),
            "d": (KeyAction("d", None), KeyAction("shift+d", None)),
            "e": (KeyAction("e", None), KeyAction("shift+e", None)),
            "f": (KeyAction("f", None), KeyAction("shift+f", None)),
            "g": (KeyAction("g", None), KeyAction("shift+g", None)),
            "h": (KeyAction("h", None), KeyAction("shift+h", None)),
            "i": (KeyAction("i", None), KeyAction("shift+i", None)),
            "j": (KeyAction("j", None), KeyAction("shift+j", None)),
            "k": (KeyAction("k", None), KeyAction("shift+k", None)),
            "l": (KeyAction("l", None), KeyAction("shift+l", None)),
            "m": (KeyAction("m", None), KeyAction("shift+m", None)),
            "n": (KeyAction("n", None), KeyAction("shift+n", None)),
            "o": (KeyAction("o", None), KeyAction("shift+o", None)),
            "p": (KeyAction("p", None), KeyAction("shift+p", None)),
            "q": (KeyAction("q", None), KeyAction("shift+q", None)),
            "r": (KeyAction("r", None), KeyAction("shift+r", None)),
            "s": (KeyAction("s", None), KeyAction("shift+s", None)),
            "t": (KeyAction("t", None), KeyAction("shift+t", None)),
            "u": (KeyAction("u", None), KeyAction("shift+u", None)),
            "v": (KeyAction("v", None), KeyAction("shift+v", None)),
            "w": (KeyAction("w", None), KeyAction("shift+w", None)),
            "x": (KeyAction("x", None), KeyAction("shift+x", None)),
            "y": (KeyAction("y", None), KeyAction("shift+y", None)),
            "z": (KeyAction("z", None), KeyAction("shift+z", None)),
        },
        "width": 13,
        "height": 2,
    },
    "digits": {
        "tiles": {
            "digit0": (KeyAction("0", None), None),
            "digit1": (KeyAction("1", None), None),
            "digit2": (KeyAction("2", None), None),
            "digit3": (KeyAction("3", None), None),
            "digit4": (KeyAction("4", None), None),
            "digit5": (KeyAction("5", None), None),
            "digit6": (KeyAction("6", None), None),
            "digit7": (KeyAction("7", None), None),
            "digit8": (KeyAction("8", None), None),
            "digit9": (KeyAction("9", None), None),
        },
        "width": 10,
        "height": 1,
    },
    "navigation": {
        "tiles": {
            "left": (KeyAction("⏴", None, "left"), None),
            "right": (KeyAction("⏵", None, "right"), None),
            "up": (KeyAction("⏶", None, "up"), None),
            "down": (KeyAction("⏷", None, "down"), None),
        },
        "width": 2,
        "height": 2,
    },
    "control": {
        "tiles": {
            "backspace": (KeyAction("⌫", None, "backspace"), None),
            "alt": (KeyAction("ⓐ", None), None),
            "ctrl": (KeyAction("ⓒ", None), None),
            "shift": (KeyAction("ⓢ", None), None),
            "win": (KeyAction("ⓦ", None), None),
            "escape": (KeyAction("❌", None, "escape"), None),
            "tab": (KeyAction("⇥", None, "tab"), None),
            "enter": (KeyAction("↲", None, "enter"), None),
        },
        "width": 8,
        "height": 1,
    },
    "symbols": {
        "tiles": {
            "home": (KeyAction("⏮", None, "home"), None),
            "end": (KeyAction("⏭", None, "end"), None),
            "pgup": (KeyAction("⏫", None, "page up"), None),
            "pgdown": (KeyAction("⏬", None, "page down"), None),
            "delete": (KeyAction("⌧", None, "delete"), None),
            "insert": (KeyAction("⎀", None, "insert"), None),
            "amp": (KeyAction("&", None, "shift+6"), None),
            "perc": (KeyAction("%", None, "shift+5"), None),
            "exclamation": (KeyAction("!", None, "shift+1"), None),
            "doublequote": (KeyAction('"', None, "shift+2"), None),
            "singlequote": (KeyAction("'", None, "shift+numbersign"), None),
            "backtick": (KeyAction("`", None), None),
            "dollar": (KeyAction("$", None, "shift+4"), None),
            "euro": (KeyAction("€", None, "alt gr+e"), None),
            "at": (KeyAction("@", None, "alt gr+q"), None),
            "backslash": (KeyAction("\\", None, "alt gr+\\"), None),
            "underscore": (KeyAction("_", None, "shift+_"), None),
            "hash": (KeyAction("#", None), None),
            "tilde": (KeyAction("~", None, "alt gr+~"), None),
            "paragraph": (KeyAction("§", None, "shift+3"), None),
            "roundbraceopen": (KeyAction("(", None, "shift+("), None),
            "roundbraceclose": (KeyAction(")", None, "shift+)"), None),
            "squarebraceopen": (KeyAction("[", None, "alt gr+["), None),
            "squarebraceclose": (KeyAction("]", None, "alt gr+]"), None),
            "curlybraceopen": (KeyAction("{", None, "alt gr+{"), None),
            "curlybraceclose": (KeyAction("}", None, "alt gr+}"), None),
            "smaller": (KeyAction("<", None), None),
            "greater": (KeyAction(">", None, "shift+>"), None),
            "pipe": (KeyAction("|", None, "alt gr+|"), None),
            "questionmark": (KeyAction("?", None, "shift+question"), None),
            "semicolon": (KeyAction(";", None, "shift+;"), None),
            "colon": (KeyAction(":", None, "shift+:"), None),
            "equal": (KeyAction("=", None, "shift+="), None),
            "star": (KeyAction("*", None, "shift+*"), None),
            "hat": (KeyAction("^", None), None),
            "circle": (KeyAction("°", None, "shift+°"), None),
            "F1": (KeyAction("F1", None), None),
            "F2": (KeyAction("F2", None), None),
            "F3": (KeyAction("F3", None), None),
            "F4": (KeyAction("F4", None), None),
            "F5": (KeyAction("F5", None), None),
            "F6": (KeyAction("F6", None), None),
            "F7": (KeyAction("F7", None), None),
            "F8": (KeyAction("F8", None), None),
            "F9": (KeyAction("F9", None), None),
            "F10": (KeyAction("F10", None), None),
            "F11": (KeyAction("F11", None), None),
            "F12": (KeyAction("F12", None), None),
            "dot": (KeyAction(".", None), None),
            "comma": (KeyAction(",", None), None),
            "space": (KeyAction("⎵", None, "space"), None),
            "plus": (KeyAction("+", None), None),
            "minus": (KeyAction("-", None), None),
            "slash": (KeyAction("/", None, "shift+7"), None),
        },
        "width": 13,
        "height": 5,
    },
    "context": {
        "tiles": {
            "copy": (KeyAction("copy", None, "ctrl+c"), None),
            "cut": (KeyAction("cut", None, "ctrl+x"), None),
            "paste": (KeyAction("paste", None, "ctrl+v"), None),
            "save": (KeyAction("save", None, "ctrl+s"), None),
            "undo": (KeyAction("undo", None, "ctrl+z"), None),
            "redo": (KeyAction("redo", None, "ctrl+y"), None),
            "clone": (KeyAction("clone", None, "ctrl+d"), None),
            "del": (KeyAction("del", None, "ctrl+shift+d"), None),
            "next": (KeyAction("next", None, "ctrl+alt+f"), None),
            "find": (KeyAction("find", None, "ctrl+f"), None),
        },
        "width": 8,
        "height": 4,
    },
    "eye_modes": {
        "tiles": {
            "pause_tag": (TagAction("pause", None, "pause"), None),
            "debug_gaze": (TagAction("👁", None, "debug_gaze"), None),
            "follow_tag": (TagAction("follow", None, "follow"), None),
            "hide_labels": (TagAction("labels", None, "hide_labels"), None),
        },
        "width": 4,
        "height": 1,
    },
    "always": {
        "tiles": {
            "scrolling_tag": (TagAction("↕", None, "scrolling"), None),
            "unpause_tag": (TagAction("unpause", None, "pause"), None),
            "follow_until_click_tag": (
                TagAction("🖰", None, "follow_until_click"),
                None,
            ),
        },
        "width": 3,
        "height": 1,
    },
}
tiles = {
    "keyboard1": {
        "letters": (0, 0),
        "digits": (0, 2),
        "navigation": (0, 3),
        "control": (2, 3),
    },
    "keyboard2": {"symbols": (0, 0)},
    "textCmds": {"context": (0, 0)},
    # "apps": {
    #     # row 0
    #     "vsc-eyeput": (ShellAction(None),
    #         "/eyeput",
    #         f"{os.path.dirname(__file__)}/resources/vsc.png",
    #         1,
    #         0,
    #         f"code {os.path.dirname(__file__)}",
    #     ),
    #     # row 1
    #     "terminal": (ShellAction(None),
    #         "",
    #         "/usr/share/app-info/icons/archlinux-arch-community/128x128/liri-terminal_utilities-terminal.png",
    #         0,
    #         1,
    #         "gnome-terminal",
    #     ),
    #     # row 2
    #     "google": (ShellAction(None),
    #         "google",
    #         "/usr/share/app-info/icons/archlinux-arch-extra/64x64/kaccounts-providers_applications-internet.png",
    #         0,
    #         2,
    #         "xdg-open http://google.com &",
    #     ),
    #     "golem": (ShellAction(None),
    #         "golem",
    #         f"{os.path.dirname(__file__)}/resources/jitsi.png",
    #         1,
    #         2,
    #         "xdg-open https://meet.golem.de/ &",
    #     ),
    #     "github": (ShellAction(None),
    #         "github",
    #         f"{os.path.dirname(__file__)}/resources/web-github-icon.png",
    #         2,
    #         2,
    #         "xdg-open https://github.com/adabru &",
    #     ),
    #     "github": (ShellAction(None),
    #         "github",
    #         "invalid path",
    #         2,
    #         3,
    #         "xdg-open https://github.com/adabru &",
    #     ),
    # },
    "eye_modes": {"eye_modes": (0, 0)},
    "empty": {},
    "always": {"always": (0, 5)},
}


@dataclass(frozen=True)
class Zone:
    top_left: tuple[float, float]
    bottom_right: tuple[float, float]

    def __contains__(self, point):
        return (
            self.top_left[0] <= point[0] <= self.bottom_right[0]
            and self.top_left[1] <= point[1] <= self.bottom_right[1]
        )


Zone.tl = Zone((-0.1, -0.1), (0.3, 0.3))
Zone.l = Zone((-0.1, 0.3), (0.3, 0.6))
Zone.tr = Zone((0.7, -0.1), (1.1, 0.3))
Zone.br = Zone((0.7, 0.7), (1.1, 1.1))
Zone.c = Zone((0.3, 0.3), (0.6, 0.6))
Zone.inside = Zone((-0.1, -0.1), (1.1, 1.1))
Zone.any = Zone((-100.0, -100.0), (100.0, 100.0))

# commands further up have precedence
blink_commands = {
    "tag_cursor": {
        (".", Zone.any): BlinkAction("", None, "mouse_stop_move"),
    },
    "tag_calibration": {
        (". . .", Zone.any): BlinkAction("", None, "calibration_cancel"),
        (". .", Zone.any): BlinkAction("", None, "calibration_next"),
    },
    "tag_pause": {
        (".r", Zone.inside): BlinkAction("", None, "select_and_hold"),
        (".l", Zone.inside): BlinkAction("", None, "select_and_hold"),
    },
    "tag_grid": {
        (" ", Zone.any): TagAction("↕", None, "grid", "unset"),
        (".r", Zone.inside): BlinkAction("", None, "select_0"),
        (".l", Zone.inside): BlinkAction("", None, "select_1"),
    },
    "tag_scrolling": {
        (". r", Zone.inside): BlinkAction("", None, "scroll_up"),
        (" r", Zone.inside): BlinkAction("", None, "scroll_up"),
        (". l", Zone.inside): BlinkAction("", None, "scroll_down"),
        (" l", Zone.inside): BlinkAction("", None, "scroll_down"),
        (" ", Zone.any): BlinkAction("", None, "scroll_stop"),
        (".", Zone.any): BlinkAction("", None, "scroll_stop"),
    },
    "default": {
        (".r", Zone.c): GridLayerAction("", None, "keyboard1"),
        (".r", Zone.l): GridLayerAction("", None, "keyboard1", ("ctrl",)),
        (".r", Zone.tr): GridLayerAction("", None, "keyboard2"),
        (".r", Zone.br): GridLayerAction("", None, "textCmds"),
        (".r", Zone.tl): GridLayerAction("", None, "eye_modes"),
        (".r", Zone.inside): BlinkAction("", None, "select_0"),
        (".l", Zone.inside): BlinkAction("", None, "select_1"),
    },
}
