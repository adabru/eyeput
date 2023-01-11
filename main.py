import asyncio
from threading import Thread
from app import App
from executor import Executor
from session_bus import SessionBus


class BusThread(Thread):
    def __init__(self, bus):
        super().__init__()
        self.bus = bus

    async def event_loop(self):
        # async init
        self.bus.async_init()

        # keep event loop running
        while True:
            await asyncio.sleep(100)

    def run(self):
        asyncio.run(self.event_loop())


bus = SessionBus("/tmp/adabru")
bus_thread = BusThread(bus)
bus_thread.start()

# decouple from main app for potential community compatibility
executor = Executor(bus, "executor")


app = App(bus)
app.run()
