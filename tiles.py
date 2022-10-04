from dataclasses import dataclass
import os.path

from PySide2.QtCore import QRectF, QPointF

from settings import *


@dataclass
class Action:
    label: str
    img: str
    x: int
    y: int


@dataclass
class InternalAction(Action):
    pass


@dataclass
class SetModeAction(Action):
    mode: str


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
class CmdAction(Action):
    cmd: str = None


@dataclass
class GridLayerAction(Action):
    layer: str = None


tiles = {
    "keyboard1": {
        # row 0
        "a": KeyAction("a", None, 0, 0),
        "b": KeyAction("b", None, 1, 0),
        "c": KeyAction("c", None, 2, 0),
        "d": KeyAction("d", None, 3, 0),
        "e": KeyAction("e", None, 4, 0),
        "f": KeyAction("f", None, 5, 0),
        "g": KeyAction("g", None, 6, 0),
        "h": KeyAction("h", None, 7, 0),
        "i": KeyAction("i", None, 8, 0),
        "j": KeyAction("j", None, 9, 0),
        "k": KeyAction("k", None, 10, 0),
        "l": KeyAction("l", None, 11, 0),
        "m": KeyAction("m", None, 12, 0),
        "dot": KeyAction(".", None, 13, 0),
        # row 1
        "n": KeyAction("n", None, 0, 1),
        "o": KeyAction("o", None, 1, 1),
        "p": KeyAction("p", None, 2, 1),
        "q": KeyAction("q", None, 3, 1),
        "r": KeyAction("r", None, 4, 1),
        "s": KeyAction("s", None, 5, 1),
        "t": KeyAction("t", None, 6, 1),
        "u": KeyAction("u", None, 7, 1),
        "v": KeyAction("v", None, 8, 1),
        "w": KeyAction("w", None, 9, 1),
        "x": KeyAction("x", None, 10, 1),
        "y": KeyAction("y", None, 11, 1),
        "z": KeyAction("z", None, 12, 1),
        "comma": KeyAction(",", None, 13, 1),
        # row 2
        "A": KeyAction("A", None, 0, 2, "shift+a"),
        "B": KeyAction("B", None, 1, 2, "shift+b"),
        "C": KeyAction("C", None, 2, 2, "shift+c"),
        "D": KeyAction("D", None, 3, 2, "shift+d"),
        "E": KeyAction("E", None, 4, 2, "shift+e"),
        "F": KeyAction("F", None, 5, 2, "shift+f"),
        "G": KeyAction("G", None, 6, 2, "shift+g"),
        "H": KeyAction("H", None, 7, 2, "shift+h"),
        "I": KeyAction("I", None, 8, 2, "shift+i"),
        "J": KeyAction("J", None, 9, 2, "shift+j"),
        "K": KeyAction("K", None, 10, 2, "shift+k"),
        "L": KeyAction("L", None, 11, 2, "shift+l"),
        "M": KeyAction("M", None, 12, 2, "shift+m"),
        "space": KeyAction("⎵", None, 13, 2, "space"),
        # row 3
        "N": KeyAction("N", None, 0, 3, "shift+n"),
        "O": KeyAction("O", None, 1, 3, "shift+o"),
        "P": KeyAction("P", None, 2, 3, "shift+p"),
        "Q": KeyAction("Q", None, 3, 3, "shift+q"),
        "R": KeyAction("R", None, 4, 3, "shift+r"),
        "S": KeyAction("S", None, 5, 3, "shift+s"),
        "T": KeyAction("T", None, 6, 3, "shift+t"),
        "U": KeyAction("U", None, 7, 3, "shift+u"),
        "V": KeyAction("V", None, 8, 3, "shift+v"),
        "W": KeyAction("W", None, 9, 3, "shift+w"),
        "X": KeyAction("X", None, 10, 3, "shift+x"),
        "Y": KeyAction("Y", None, 11, 3, "shift+y"),
        "Z": KeyAction("Z", None, 12, 3, "shift+z"),
        "click": MouseAction("🖰", None, 13, 3, "left_click_delayed"),
        # row 4
        "left": KeyAction("⏴", None, 0, 4, "left"),
        "right": KeyAction("⏵", None, 1, 4, "right"),
        "digit0": KeyAction("0", None, 2, 4),
        "digit1": KeyAction("1", None, 3, 4),
        "digit2": KeyAction("2", None, 4, 4),
        "digit3": KeyAction("3", None, 5, 4),
        "digit4": KeyAction("4", None, 6, 4),
        "digit5": KeyAction("5", None, 7, 4),
        "digit6": KeyAction("6", None, 8, 4),
        "digit7": KeyAction("7", None, 9, 4),
        "digit8": KeyAction("8", None, 10, 4),
        "digit9": KeyAction("9", None, 11, 4),
        "plus": KeyAction("+", None, 12, 4),
        "minus": KeyAction("-", None, 13, 4),
        # row 5
        "up": KeyAction("⏶", None, 0, 5, "up"),
        "down": KeyAction("⏷", None, 1, 5, "down"),
        "backspace": KeyAction("⌫", None, 2, 5, "backspace"),
        "alt": KeyAction("ⓐ", None, 3, 5),
        "ctrl": KeyAction("ⓒ", None, 4, 5),
        "shift": KeyAction("ⓢ", None, 5, 5),
        "win": KeyAction("ⓦ", None, 6, 5),
        "escape": KeyAction("❌", None, 7, 5, "escape"),
        "tab": KeyAction("⇥", None, 8, 5, "tab"),
        "enter": KeyAction("↲", None, 9, 5, "enter"),
        "slash": KeyAction("/", None, 10, 5, "shift+7"),
        "hold": InternalAction("∞", None, 11, 5),
        "keyboard2": GridLayerAction("➁", None, 12, 5, "keyboard2"),
        "textCmds": GridLayerAction("➂", None, 13, 5, "textCmds"),
    },
    "keyboard2": {
        # row 0
        "home": KeyAction("⏮", None, 0, 0, "home"),
        "end": KeyAction("⏭", None, 1, 0, "end"),
        "pgup": KeyAction("⏫", None, 2, 0, "page up"),
        "pgdown": KeyAction("⏬", None, 3, 0, "page down"),
        "delete": KeyAction("⌧", None, 4, 0, "delete"),
        "insert": KeyAction("⎀", None, 5, 0, "insert"),
        # row 1
        "amp": KeyAction("&", None, 0, 1, "shift+6"),
        "perc": KeyAction("%", None, 1, 1, "shift+5"),
        "exclamation": KeyAction("!", None, 2, 1, "shift+1"),
        "doublequote": KeyAction('"', None, 3, 1, "shift+2"),
        "singlequote": KeyAction("'", None, 4, 1, "shift+numbersign"),
        "backtick": KeyAction("`", None, 5, 1),
        "dollar": KeyAction("$", None, 6, 1, "shift+4"),
        "euro": KeyAction("€", None, 7, 1, "alt gr+e"),
        "at": KeyAction("@", None, 8, 1, "alt gr+q"),
        "backslash": KeyAction("\\", None, 9, 1, "alt gr+\\"),
        "underscore": KeyAction("_", None, 10, 1, "shift+_"),
        "hash": KeyAction("#", None, 11, 1),
        "tilde": KeyAction("~", None, 12, 1, "alt gr+~"),
        "paragraph": KeyAction("§", None, 13, 1, "shift+3"),
        # row 2
        "roundbraceopen": KeyAction("(", None, 0, 2, "shift+("),
        "roundbraceclose": KeyAction(")", None, 1, 2, "shift+)"),
        "squarebraceopen": KeyAction("[", None, 2, 2, "alt gr+["),
        "squarebraceclose": KeyAction("]", None, 3, 2, "alt gr+]"),
        "curlybraceopen": KeyAction("{", None, 4, 2, "alt gr+{"),
        "curlybraceclose": KeyAction("}", None, 5, 2, "alt gr+}"),
        "smaller": KeyAction("<", None, 6, 2),
        "greater": KeyAction(">", None, 7, 2, "shift+>"),
        "pipe": KeyAction("|", None, 8, 2, "alt gr+|"),
        "questionmark": KeyAction("?", None, 9, 2, "shift+?"),
        # row 3
        "semicolon": KeyAction(";", None, 0, 3, "shift+;"),
        "colon": KeyAction(":", None, 1, 3, "shift+:"),
        "equal": KeyAction("=", None, 2, 3, "shift+="),
        "star": KeyAction("*", None, 3, 3, "shift+*"),
        "hat": KeyAction("^", None, 4, 3),
        "circle": KeyAction("°", None, 5, 3, "shift+°"),
        # row 4
        "F1": KeyAction("F1", None, 0, 4),
        "F2": KeyAction("F2", None, 1, 4),
        "F3": KeyAction("F3", None, 2, 4),
        "F4": KeyAction("F4", None, 3, 4),
        "F5": KeyAction("F5", None, 4, 4),
        "F6": KeyAction("F6", None, 5, 4),
        "F7": KeyAction("F7", None, 6, 4),
        "F8": KeyAction("F8", None, 7, 4),
        "F9": KeyAction("F9", None, 8, 4),
        "F10": KeyAction("F10", None, 9, 4),
        "F11": KeyAction("F11", None, 10, 4),
        "F12": KeyAction("F12", None, 11, 4),
        # row 5
        "hold": InternalAction("∞", None, 11, 5),
        "keyboard1": GridLayerAction("➀", None, 12, 5, "keyboard1"),
        "textCmds": GridLayerAction("➂", None, 13, 5, "textCmds"),
    },
    "textCmds": {
        # row 0
        "copy": KeyAction("copy", None, 0, 0, "ctrl+c"),
        "cut": KeyAction("cut", None, 1, 0, "ctrl+x"),
        "paste": KeyAction("paste", None, 2, 0, "ctrl+v"),
        # row 1
        # row 2
        # row 3
        # row 4
        # row 5
        "hold": InternalAction("∞", None, 11, 5),
        "keyboard1": GridLayerAction("➀", None, 12, 5, "keyboard1"),
        "keyboard2": GridLayerAction("➁", None, 13, 5, "keyboard2"),
    },
    "apps": {
        # row 0
        "vsc-eyeput": CmdAction(
            "/eyeput",
            f"{os.path.dirname(__file__)}/resources/vsc.png",
            1,
            0,
            f"code {os.path.dirname(__file__)}",
        ),
        # row 1
        "terminal": CmdAction(
            "",
            "/usr/share/app-info/icons/archlinux-arch-community/128x128/liri-terminal_utilities-terminal.png",
            0,
            1,
            "gnome-terminal",
        ),
        # row 2
        "google": CmdAction(
            "google",
            "/usr/share/app-info/icons/archlinux-arch-extra/64x64/kaccounts-providers_applications-internet.png",
            0,
            2,
            "xdg-open http://google.com &",
        ),
        "golem": CmdAction(
            "golem",
            f"{os.path.dirname(__file__)}/resources/jitsi.png",
            1,
            2,
            "xdg-open https://meet.golem.de/ &",
        ),
        "github": CmdAction(
            "github",
            f"{os.path.dirname(__file__)}/resources/web-github-icon.png",
            2,
            2,
            "xdg-open https://github.com/adabru &",
        ),
        "github": CmdAction(
            "github",
            "invalid path",
            2,
            3,
            "xdg-open https://github.com/adabru &",
        ),
    },
    "eye_modes": {
        # row 0
        "scroll_mode": SetModeAction("↕", None, 0, 0, Modes.scrolling),
        "click_mode": SetModeAction("🖰", None, 1, 0, Modes.enabled),
        "pause_mode": SetModeAction("pause", None, 2, 0, Modes.paused),
        # "calibration": SetModeAction("cal", None, 3, 0, Modes.calibration),
    },
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
Zone.tr = Zone((0.7, -0.1), (1.1, 0.3))
Zone.c = Zone((0.3, 0.3), (0.6, 0.6))
Zone.inside = Zone((-0.1, -0.1), (1.1, 1.1))
Zone.any = Zone((-100.0, -100.0), (100.0, 100.0))

blink_commands = {
    Modes.enabled: {
        (". . . .", Zone.any): SetModeAction("cal", None, 3, 0, Modes.calibration),
        (".r", Zone.c): GridLayerAction("", None, 0, 0, "keyboard1"),
        (".r", Zone.tr): GridLayerAction("", None, 0, 0, "keyboard2"),
        (".r", Zone.tl): GridLayerAction("", None, 0, 0, "eye_modes"),
        (".l", Zone.inside): BlinkAction("", None, 0, 0, "mouse_start_move"),
        # ". .": "mouse_move",
        # ".r.": "left_click",
    },
    Modes.cursor: {
        (".", Zone.any): BlinkAction("", None, 0, 0, "mouse_stop_move"),
    },
    Modes.grid: {
        (" ", Zone.any): SetModeAction("", None, 0, 0, Modes._previous),
        (".r", Zone.inside): BlinkAction("", None, 0, 0, "select_and_hold"),
        (".l", Zone.inside): BlinkAction("", None, 0, 0, "select_and_hide"),
    },
    Modes.calibration: {
        (". . .", Zone.any): BlinkAction("", None, 0, 0, "calibration_cancel"),
        (". .", Zone.any): BlinkAction("", None, 0, 0, "calibration_next"),
    },
    Modes.paused: {
        (".r", Zone.tl): GridLayerAction("", None, 0, 0, "eye_modes"),
        (". . . .", Zone.any): SetModeAction("cal", None, 3, 0, Modes.calibration),
    },
    Modes.scrolling: {
        (". . . .", Zone.any): SetModeAction("cal", None, 3, 0, Modes.calibration),
        (".r", Zone.c): GridLayerAction("", None, 0, 0, "keyboard1"),
        (".r", Zone.tr): GridLayerAction("", None, 0, 0, "keyboard2"),
        (".r", Zone.tl): GridLayerAction("", None, 0, 0, "eye_modes"),
        (". r", Zone.inside): BlinkAction("", None, 0, 0, "scroll_up"),
        (" r", Zone.inside): BlinkAction("", None, 0, 0, "scroll_up"),
        (".l", Zone.inside): BlinkAction("", None, 0, 0, "scroll_down"),
        (" ", Zone.any): BlinkAction("", None, 0, 0, "scroll_stop"),
        (".", Zone.any): BlinkAction("", None, 0, 0, "scroll_stop"),
    },
}
