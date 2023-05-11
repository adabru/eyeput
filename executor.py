import time
from session_bus import BusSignal, SessionBus
import external


class Executor:
    command_received = BusSignal()
    bus: SessionBus
    register_name: str

    def __init__(self, bus, register_name):
        self.bus = bus
        self.register_name = register_name
        self.populate_future = None
        self.bus.subscribe(self.bus_event)

    async def populate_bus(self):
        # register on bus
        await self.bus.register(self.register_name, self)

    def bus_event(self, event):
        if event == "connect":
            if self.populate_future:
                self.populate_future.cancel()
            self.populate_future = self.bus.schedule(self.populate_bus())

    def execute(self, id: str, data: object = None):
        # report to anyone interested
        self.bus.schedule(self.command_received.notify(id, data))

        if id == "capitalize":
            external.press_key("ctrl+c")
            time.sleep(0.03)
            s: str = external.get_clipboard()
            s = s.capitalize()
            time.sleep(0.03)
            external.set_clipboard(s)
            time.sleep(0.03)
            external.press_key("ctrl+v")
        elif id == "point_space":
            external.press_key(".")
            external.press_key(" ")
        elif id == "point_newline":
            external.press_key(".")
            external.press_key("enter")
        elif id == "comma_space":
            external.press_key(",")
            external.press_key(" ")
        elif id == "comma_newline":
            external.press_key(",")
            external.press_key("enter")
        elif id == "git_diff":
            external.type("git diff --ws-error-highlight=all\n")
        elif id == "git_all":
            external.type("git add -A\n")
        # if id == "left_click":
        #     external.left_click()
