import asyncio
from typing import Callable, List, Set


try:
    from .session_bus import BusSignal, SessionBus, ObjectNotAvailable
except ImportError:
    from session_bus import BusSignal, SessionBus, ObjectNotAvailable


class Event:
    listeners: List[Callable[..., None]]
    muted: Callable[..., None]

    def __init__(self):
        self.listeners = []
        self.muted = None

    def notify(self, *args):
        for callback in self.listeners:
            if callback == self.muted:
                self.muted = None
            else:
                callback(*args)

    def subscribe(self, callback: Callable):
        self.listeners.append(callback)

    def mute_once(self, callback: Callable):
        self.muted = callback


class Tags:
    tags: Set[str]
    tag_changed: Event

    def __init__(self):
        self.tags = set()
        self.tag_changed = Event()

    def __iter__(self):
        return iter(self.tags)

    def has(self, tag: str):
        return tag in self.tags

    def get_tags(self):
        return self.tags

    def set_tag_value(self, tag: str, value: bool):
        if value:
            self.set_tag(tag)
        else:
            self.unset_tag(tag)

    def set_tag(self, tag: str):
        self.tags.add(tag)
        self.tag_changed.notify(tag, True)

    def unset_tag(self, tag: str):
        self.tags.discard(tag)
        self.tag_changed.notify(tag, False)

    def toggle_tag(self, tag: str):
        if tag in self.tags:
            self.unset_tag(tag)
        else:
            self.set_tag(tag)


class TagSharing:
    tags: Tags
    tag_changed = BusSignal()
    bus: SessionBus
    register_name: str
    peer_name: str

    def __init__(self, tags, bus, register_name, peer_name):
        self.tags = tags
        self.bus = bus
        self.register_name = register_name
        self.peer_name = peer_name
        self.proxy = None
        self.populate_future = None
        self.bus.subscribe(self.bus_event)
        # maybe bus is already connected
        self.bus.schedule(self.populate_bus())
        self.tags.tag_changed.subscribe(self.local_tag_changed)

    async def populate_bus(self):
        # register own tags
        await self.bus.register(self.register_name, self)

        # subscribe
        while not self.proxy:
            try:
                self.proxy = await self.bus.get(self.peer_name)
                await self.proxy.subscribe("tag_changed", self.remote_tag_changed)
            except ObjectNotAvailable:
                await asyncio.sleep(2)

    def bus_event(self, event):
        if event == "connect":
            self.proxy = None
            if self.populate_future:
                self.populate_future.cancel()
            self.populate_future = self.bus.schedule(self.populate_bus())

    def remote_tag_changed(self, tag: str, value: bool):
        # avoid feedback loop
        self.tags.tag_changed.mute_once(self.local_tag_changed)

        self.tags.set_tag_value(tag, value)

    def local_tag_changed(self, tag: str, value: bool):
        self.bus.schedule(self.tag_changed.notify(tag, value))
