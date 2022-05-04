import os.path

from PyQt5.QtCore import QRectF


class InternalAction:
    def __init__(self, label, x, y, img=None):
        self.label = label
        self.x = x
        self.y = y
        self.img = img


class KeyAction:
    def __init__(self, label, x, y, pressKey=None, img=None):
        self.label = label
        self.x = x
        self.y = y
        self.img = img
        self.pressKey = pressKey or label


class CmdAction:
    def __init__(self, label, x, y, cmd, img=None):
        self.label = label
        self.x = x
        self.y = y
        self.cmd = cmd
        self.img = img


Levels = {
    "keyboard1": {
        # row 0
        "a": KeyAction("a", 0, 0),
        "b": KeyAction("b", 1, 0),
        "c": KeyAction("c", 2, 0),
        "d": KeyAction("d", 3, 0),
        "e": KeyAction("e", 4, 0),
        "f": KeyAction("f", 5, 0),
        "g": KeyAction("g", 6, 0),
        "h": KeyAction("h", 7, 0),
        "i": KeyAction("i", 8, 0),
        "j": KeyAction("j", 9, 0),
        "k": KeyAction("k", 10, 0),
        "l": KeyAction("l", 11, 0),
        "m": KeyAction("m", 12, 0),
        "dot": KeyAction(".", 13, 0),
        # row 1
        "n": KeyAction("n", 0, 1),
        "o": KeyAction("o", 1, 1),
        "p": KeyAction("p", 2, 1),
        "q": KeyAction("q", 3, 1),
        "r": KeyAction("r", 4, 1),
        "s": KeyAction("s", 5, 1),
        "t": KeyAction("t", 6, 1),
        "u": KeyAction("u", 7, 1),
        "v": KeyAction("v", 8, 1),
        "w": KeyAction("w", 9, 1),
        "x": KeyAction("x", 10, 1),
        "y": KeyAction("y", 11, 1),
        "z": KeyAction("z", 12, 1),
        "comma": KeyAction(",", 13, 1),
        # row 2
        "A": KeyAction("A", 0, 2, "shiftl+a"),
        "B": KeyAction("B", 1, 2, "shiftl+b"),
        "C": KeyAction("C", 2, 2, "shiftl+c"),
        "D": KeyAction("D", 3, 2, "shiftl+d"),
        "E": KeyAction("E", 4, 2, "shiftl+e"),
        "F": KeyAction("F", 5, 2, "shiftl+f"),
        "G": KeyAction("G", 6, 2, "shiftl+g"),
        "H": KeyAction("H", 7, 2, "shiftl+h"),
        "I": KeyAction("I", 8, 2, "shiftl+i"),
        "J": KeyAction("J", 9, 2, "shiftl+j"),
        "K": KeyAction("K", 10, 2, "shiftl+k"),
        "L": KeyAction("L", 11, 2, "shiftl+l"),
        "M": KeyAction("M", 12, 2, "shiftl+m"),
        "space": KeyAction(" ", 13, 2, "shiftl+n"),
        # row 3
        "N": KeyAction("N", 0, 3, "shiftl+n"),
        "O": KeyAction("O", 1, 3, "shiftl+o"),
        "P": KeyAction("P", 2, 3, "shiftl+p"),
        "Q": KeyAction("Q", 3, 3, "shiftl+q"),
        "R": KeyAction("R", 4, 3, "shiftl+r"),
        "S": KeyAction("S", 5, 3, "shiftl+s"),
        "T": KeyAction("T", 6, 3, "shiftl+t"),
        "U": KeyAction("U", 7, 3, "shiftl+u"),
        "V": KeyAction("V", 8, 3, "shiftl+v"),
        "W": KeyAction("W", 9, 3, "shiftl+w"),
        "X": KeyAction("X", 10, 3, "shiftl+x"),
        "Y": KeyAction("Y", 11, 3, "shiftl+y"),
        "Z": KeyAction("Z", 12, 3, "shiftl+z"),
        "click": InternalAction("click", 13, 3),
        # row 4
        "left": KeyAction("←", 0, 4, "left"),
        "right": KeyAction("→", 1, 4, "right"),
        "digit0": KeyAction("0", 2, 4),
        "digit1": KeyAction("1", 3, 4),
        "digit2": KeyAction("2", 4, 4),
        "digit3": KeyAction("3", 5, 4),
        "digit4": KeyAction("4", 6, 4),
        "digit5": KeyAction("5", 7, 4),
        "digit6": KeyAction("6", 8, 4),
        "digit7": KeyAction("7", 9, 4),
        "digit8": KeyAction("8", 10, 4),
        "digit9": KeyAction("9", 11, 4),
        "plus": KeyAction("+", 12, 4),
        "minus": KeyAction("-", 13, 4),
        # row 5
        "up": KeyAction("↑", 0, 5, "up"),
        "down": KeyAction("↓", 1, 5, "down"),
        "backspace": KeyAction("␈", 2, 5, "backspace"),
        "alt": KeyAction("alt", 3, 5),
        "ctrl": KeyAction("ctrl", 4, 5),
        "shiftl": KeyAction("shiftl", 5, 5),
        "win": KeyAction("win", 6, 5),
        "escape": KeyAction("␛", 7, 5, "escape"),
        "tab": KeyAction("↹", 8, 5, "tab"),
        "enter": KeyAction("⏎", 9, 5, "enter"),
        "slash": KeyAction("/", 10, 5, "shiftl+/"),
        "hold": InternalAction("hold", 11, 5),
        "keyboard2": InternalAction("➁", 12, 5),
        "textCmds": InternalAction("➂", 13, 5),
    },
    "keyboard2": {
        # row 0
        "home": KeyAction("home", 0, 0),
        "end": KeyAction("end", 1, 0),
        "pgup": KeyAction("pg↑", 2, 0, "page up"),
        "pgdown": KeyAction("pg↓", 3, 0, "page down"),
        "delete": KeyAction("del", 4, 0, "delete"),
        "insert": KeyAction("ins", 5, 0, "insert"),
        # row 1
        "amp": KeyAction("&", 0, 1, "shiftl+&"),
        "perc": KeyAction("%", 1, 1, "shiftl+%"),
        "exclamation": KeyAction("!", 2, 1, "shiftl+!"),
        "doublequote": KeyAction('"', 3, 1, 'shiftl+"'),
        "singlequote": KeyAction("'", 4, 1, "shiftl+'"),
        "backtick": KeyAction("`", 5, 1),
        "dollar": KeyAction("$", 6, 1, "shiftl+$"),
        "euro": KeyAction("€", 7, 1, "alt gr+e"),
        "at": KeyAction("@", 8, 1, "alt gr+@"),
        "backslash": KeyAction("\\", 9, 1, "alt gr+\\"),
        "underscore": KeyAction("_", 10, 1, "shiftl+_"),
        "hash": KeyAction("#", 11, 1),
        "tilde": KeyAction("~", 12, 1, "alt gr+~"),
        "paragraph": KeyAction("§", 13, 1, "shiftl+3"),
        # row 2
        "roundbraceopen": KeyAction("(", 0, 2, "shiftl+("),
        "roundbraceclose": KeyAction(")", 1, 2, "shiftl+)"),
        "squarebraceopen": KeyAction("[", 2, 2, "alt gr+["),
        "squarebraceclose": KeyAction("]", 3, 2, "alt gr+]"),
        "curlybraceopen": KeyAction("{", 4, 2, "alt gr+{"),
        "curlybraceclose": KeyAction("}", 5, 2, "alt gr+}"),
        "smaller": KeyAction("<", 6, 2),
        "greater": KeyAction(">", 7, 2, "shiftl+>"),
        "pipe": KeyAction("|", 8, 2, "alt gr+|"),
        "questionmark": KeyAction("?", 9, 2, "shiftl+?"),
        # row 3
        "semicolon": KeyAction(";", 0, 3, "shiftl+;"),
        "colon": KeyAction(":", 1, 3, "shiftl+:"),
        "equal": KeyAction("=", 2, 3, "shiftl+="),
        "star": KeyAction("*", 3, 3, "shiftl+*"),
        "hat": KeyAction("^", 4, 3),
        "circle": KeyAction("°", 5, 3, "shiftl+°"),
        # row 4
        "F1": KeyAction("F1", 0, 4),
        "F2": KeyAction("F2", 1, 4),
        "F3": KeyAction("F3", 2, 4),
        "F4": KeyAction("F4", 3, 4),
        "F5": KeyAction("F5", 4, 4),
        "F6": KeyAction("F6", 5, 4),
        "F7": KeyAction("F7", 6, 4),
        "F8": KeyAction("F8", 7, 4),
        "F9": KeyAction("F9", 8, 4),
        "F10": KeyAction("F10", 9, 4),
        "F11": KeyAction("F11", 10, 4),
        "F12": KeyAction("F12", 11, 4),
        # row 5
        "hold": InternalAction("hold", 11, 5),
        "keyboard1": InternalAction("➀", 12, 5),
        "textCmds": InternalAction("➂", 13, 5),
    },
    "textCmds": {
        # row 0
        "copy": KeyAction("copy", 0, 0, "ctrl+c"),
        "cut": KeyAction("cut", 1, 0, "ctrl+x"),
        "paste": KeyAction("paste", 2, 0, "ctrl+v"),
        # row 1
        # row 2
        # row 3
        # row 4
        # row 5
        "hold": InternalAction("hold", 11, 5),
        "keyboard1": InternalAction("➀", 12, 5),
        "keyboard2": InternalAction("➁", 13, 5),
    },
    "apps": {
        # row 0
        "vsc-eyeput": CmdAction(
            "/eyeput",
            1,
            0,
            f"code {os.path.dirname(__file__)}",
            img=f"{os.path.dirname(__file__)}/resources/vsc.png",
        ),
        # row 1
        "terminal": CmdAction(
            "",
            0,
            1,
            "gnome-terminal",
            img="/usr/share/app-info/icons/archlinux-arch-community/128x128/liri-terminal_utilities-terminal.png",
        ),
        # row 2
        "google": CmdAction(
            "google",
            0,
            2,
            "xdg-open http://google.com &",
            img="/usr/share/app-info/icons/archlinux-arch-extra/64x64/kaccounts-providers_applications-internet.png",
        ),
        "golem": CmdAction(
            "golem",
            1,
            2,
            "xdg-open https://meet.golem.de/ &",
            img=f"{os.path.dirname(__file__)}/resources/jitsi.png",
        ),
        "github": CmdAction(
            "github",
            2,
            2,
            "xdg-open https://github.com/adabru &",
            img=f"{os.path.dirname(__file__)}/resources/web-github-icon.png",
        ),
        "github": CmdAction(
            "github",
            2,
            3,
            "xdg-open https://github.com/adabru &",
            img="invalid path",
        ),
    },
}


class Layout:
    def findLevel(x, y):
        for lvl in Layout.areas:
            if Layout.areas[lvl].contains(x, y):
                return lvl
        return None

    areas = {
        # diag top left
        "textCmds": QRectF(-1, -1, 1, 1),
        # top left
        "keyboard1": QRectF(0, -1, 0.5, 1),
        # top right
        "keyboard2": QRectF(0.5, -1, 0.5, 1),
        # left
        "apps": QRectF(-1, 0, 1, 1),
    }
    # areas = {
    #     # top
    #     "keyboard1": QRectF(0, -1, 1, 1),
    #     # bottom
    #     "keyboard2": QRectF(0, 1, 1, 1),
    #     # left
    #     "textCmds": QRectF(-1, 0, 1, 1),
    # }
