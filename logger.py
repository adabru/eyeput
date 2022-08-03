from enum import Enum


class LogLvl(Enum):
    NONE = 0
    INFO = 1
    VERBOSE = 2
    DEBUG = 3


logLevel = LogLvl.INFO
# logLevel = LogLvl.DEBUG
last_message = ""


def log_info(s):
    if logLevel.value > LogLvl.NONE.value:
        print(s)


def log_verbose(s):
    if logLevel.value > LogLvl.INFO.value:
        print(s)


def log_debug(s):
    global last_message
    if logLevel.value > LogLvl.VERBOSE.value:
        if s == last_message:
            print(".", end="", flush=True)
        else:
            print("\n" + s, end="")
        last_message = s
