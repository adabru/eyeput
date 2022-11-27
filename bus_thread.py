import asyncio
from PySide2.QtCore import (
    QThread,
)

from session_bus import SessionBus
from settings import *
from shared_tags import *


class BusThread(QThread):
    def __init__(self, tags):
        super().__init__()
        self.tags = tags

    async def event_loop(self):
        # async init
        self.bus = SessionBus("/tmp/adabru")
        self.tag_sharing = TagSharing(
            self.tags,
            self.bus,
            "eyeput.tags",
            "talon.tags",
            asyncio.get_running_loop(),
        )

        # keep event loop running
        while True:
            await asyncio.sleep(100)

    def run(self):
        asyncio.run(self.event_loop())
