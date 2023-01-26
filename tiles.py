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
            "a": KeyAction("a", None),
            "b": KeyAction("b", None),
            "c": KeyAction("c", None),
            "d": KeyAction("d", None),
            "e": KeyAction("e", None),
            "f": KeyAction("f", None),
            "g": KeyAction("g", None),
            "h": KeyAction("h", None),
            "i": KeyAction("i", None),
            "j": KeyAction("j", None),
            "k": KeyAction("k", None),
            "l": KeyAction("l", None),
            "m": KeyAction("m", None),
            "n": KeyAction("n", None),
            "o": KeyAction("o", None),
            "p": KeyAction("p", None),
            "q": KeyAction("q", None),
            "r": KeyAction("r", None),
            "s": KeyAction("s", None),
            "t": KeyAction("t", None),
            "u": KeyAction("u", None),
            "v": KeyAction("v", None),
            "w": KeyAction("w", None),
            "x": KeyAction("x", None),
            "y": KeyAction("y", None),
            "z": KeyAction("z", None),
        },
        "width": 13,
        "height": 2,
    },
    "digits": {
        "tiles": {
            "digit0": KeyAction("0", None),
            "digit1": KeyAction("1", None),
            "digit2": KeyAction("2", None),
            "digit3": KeyAction("3", None),
            "digit4": KeyAction("4", None),
            "digit5": KeyAction("5", None),
            "digit6": KeyAction("6", None),
            "digit7": KeyAction("7", None),
            "digit8": KeyAction("8", None),
            "digit9": KeyAction("9", None),
        },
        "width": 10,
        "height": 1,
    },
    "navigation": {
        "tiles": {
            "left": KeyAction("⏴", None, "left"),
            "right": KeyAction("⏵", None, "right"),
            "up": KeyAction("⏶", None, "up"),
            "down": KeyAction("⏷", None, "down"),
        },
        "width": 2,
        "height": 2,
    },
    "control": {
        "tiles": {
            "backspace": KeyAction("⌫", None, "backspace"),
            "alt": KeyAction("ⓐ", None),
            "ctrl": KeyAction("ⓒ", None),
            "shift": KeyAction("ⓢ", None),
            "win": KeyAction("ⓦ", None),
            "escape": KeyAction("❌", None, "escape"),
            "tab": KeyAction("⇥", None, "tab"),
            "enter": KeyAction("↲", None, "enter"),
        },
        "width": 8,
        "height": 1,
    },
    "symbols": {
        "tiles": {
            "home": KeyAction("⏮", None, "home"),
            "end": KeyAction("⏭", None, "end"),
            "pgup": KeyAction("⏫", None, "page up"),
            "pgdown": KeyAction("⏬", None, "page down"),
            "delete": KeyAction("⌧", None, "delete"),
            "insert": KeyAction("⎀", None, "insert"),
            "amp": KeyAction("&", None, "shift+6"),
            "perc": KeyAction("%", None, "shift+5"),
            "exclamation": KeyAction("!", None, "shift+1"),
            "doublequote": KeyAction('"', None, "shift+2"),
            "singlequote": KeyAction("'", None, "shift+numbersign"),
            "backtick": KeyAction("`", None),
            "dollar": KeyAction("$", None, "shift+4"),
            "euro": KeyAction("€", None, "alt gr+e"),
            "at": KeyAction("@", None, "alt gr+q"),
            "backslash": KeyAction("\\", None, "alt gr+\\"),
            "underscore": KeyAction("_", None, "shift+_"),
            "hash": KeyAction("#", None),
            "tilde": KeyAction("~", None, "alt gr+~"),
            "paragraph": KeyAction("§", None, "shift+3"),
            "roundbraceopen": KeyAction("(", None, "shift+("),
            "roundbraceclose": KeyAction(")", None, "shift+)"),
            "squarebraceopen": KeyAction("[", None, "alt gr+["),
            "squarebraceclose": KeyAction("]", None, "alt gr+]"),
            "curlybraceopen": KeyAction("{", None, "alt gr+{"),
            "curlybraceclose": KeyAction("}", None, "alt gr+}"),
            "smaller": KeyAction("<", None),
            "greater": KeyAction(">", None, "shift+>"),
            "pipe": KeyAction("|", None, "alt gr+|"),
            "questionmark": KeyAction("?", None, "shift+question"),
            "semicolon": KeyAction(";", None, "shift+;"),
            "colon": KeyAction(":", None, "shift+:"),
            "equal": KeyAction("=", None, "shift+="),
            "star": KeyAction("*", None, "shift+*"),
            "hat": KeyAction("^", None),
            "circle": KeyAction("°", None, "shift+°"),
            "F1": KeyAction("F1", None),
            "F2": KeyAction("F2", None),
            "F3": KeyAction("F3", None),
            "F4": KeyAction("F4", None),
            "F5": KeyAction("F5", None),
            "F6": KeyAction("F6", None),
            "F7": KeyAction("F7", None),
            "F8": KeyAction("F8", None),
            "F9": KeyAction("F9", None),
            "F10": KeyAction("F10", None),
            "F11": KeyAction("F11", None),
            "F12": KeyAction("F12", None),
            "dot": KeyAction(".", None),
            "comma": KeyAction(",", None),
            "space": KeyAction("⎵", None, "space"),
            "plus": KeyAction("+", None),
            "minus": KeyAction("-", None),
            "slash": KeyAction("/", None, "shift+7"),
        },
        "width": 13,
        "height": 5,
    },
    "context": {
        "tiles": {
            "copy": KeyAction("copy", None, "ctrl+c"),
            "cut": KeyAction("cut", None, "ctrl+x"),
            "paste": KeyAction("paste", None, "ctrl+v"),
            "save": KeyAction("save", None, "ctrl+s"),
            "undo": KeyAction("undo", None, "ctrl+z"),
            "redo": KeyAction("redo", None, "ctrl+y"),
            "clone": KeyAction("clone", None, "ctrl+d"),
            "del": KeyAction("del", None, "ctrl+shift+d"),
            "next": KeyAction("next", None, "ctrl+alt+f"),
            "find": KeyAction("find", None, "ctrl+f"),
        },
        "width": 8,
        "height": 4,
    },
    "eye_modes": {
        "tiles": {
            "pause_tag": TagAction("pause", None, "pause"),
            "debug_gaze": TagAction("👁", None, "debug_gaze"),
            "follow_tag": TagAction("follow", None, "follow"),
        },
        "width": 3,
        "height": 1,
    },
    "always": {
        "tiles": {
            "scrolling_tag": TagAction("↕", None, "scrolling"),
            "unpause_tag": TagAction("unpause", None, "pause"),
            "follow_until_click_tag": TagAction("🖰", None, "follow_until_click"),
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
    #     "vsc-eyeput": ShellAction(
    #         "/eyeput",
    #         f"{os.path.dirname(__file__)}/resources/vsc.png",
    #         1,
    #         0,
    #         f"code {os.path.dirname(__file__)}",
    #     ),
    #     # row 1
    #     "terminal": ShellAction(
    #         "",
    #         "/usr/share/app-info/icons/archlinux-arch-community/128x128/liri-terminal_utilities-terminal.png",
    #         0,
    #         1,
    #         "gnome-terminal",
    #     ),
    #     # row 2
    #     "google": ShellAction(
    #         "google",
    #         "/usr/share/app-info/icons/archlinux-arch-extra/64x64/kaccounts-providers_applications-internet.png",
    #         0,
    #         2,
    #         "xdg-open http://google.com &",
    #     ),
    #     "golem": ShellAction(
    #         "golem",
    #         f"{os.path.dirname(__file__)}/resources/jitsi.png",
    #         1,
    #         2,
    #         "xdg-open https://meet.golem.de/ &",
    #     ),
    #     "github": ShellAction(
    #         "github",
    #         f"{os.path.dirname(__file__)}/resources/web-github-icon.png",
    #         2,
    #         2,
    #         "xdg-open https://github.com/adabru &",
    #     ),
    #     "github": ShellAction(
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
        (".r", Zone.inside): BlinkAction("", None, "select_and_hold"),
        (".l", Zone.inside): BlinkAction("", None, "select_and_hide"),
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
        (".l", Zone.inside): BlinkAction("", None, "select_and_hold"),
        (".r", Zone.inside): BlinkAction("", None, "select_and_hold"),
    },
}
