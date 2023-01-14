# https://coverage.readthedocs.io/en/6.5.0/#quick-start
# https://docs.python.org/3/library/unittest.html
# https://docs.python.org/3/library/multiprocessing.html
#
# pip install coverage
# python -m unittest session_bus_test.py
# coverage run -m unittest session_bus_test.py
# coverage report
# coverage html
# python -m unittest session_bus_test.TestClientTcp.test_call

import asyncio
import sys
from typing import Callable, List
import unittest
from multiprocessing import Pipe, Process, set_start_method
from multiprocessing.connection import Connection
from subprocess import Popen

from session_bus import BusSignal, ObjectNotAvailable, SessionBus


class RemoteTask:
    def run(self, conn: Connection, get_bus: Callable[[], SessionBus]):
        asyncio.run(self._run(conn, get_bus))

    async def _run(self, conn: Connection, get_bus: Callable[[], SessionBus]):
        conn.send("started")
        bus = get_bus()
        await bus.wait_for_connection(1.0)
        conn.send("connected")
        command = None
        while True:
            result = await asyncio.to_thread(conn.recv)
            if result == True:
                break
            elif result == "register":
                await bus.register("remote_object", DemoClass())
                conn.send("done")
        conn.close()


class DemoClass:
    test_signal = BusSignal()
    o: object

    def get(self):
        return self.o

    def set(self, o: object):
        self.o = o


class Hidden:
    class TestCommon(unittest.IsolatedAsyncioTestCase):
        bus: SessionBus
        event_log: List

        async def asyncSetUp(self):
            # https://docs.python.org/3/library/multiprocessing.html#exchanging-objects-between-processes
            self.conn, child_conn = Pipe()
            self.p_remote = Process(
                target=RemoteTask().run, args=(child_conn, self._get_remote_bus)
            )
            self.p_remote.start()
            self.bus = self._get_bus()
            self.event_log = []
            self.bus.subscribe(lambda *args: self.event_log.append(args))
            assert await self._rcv() == "started"
            assert await self._rcv() == "connected"
            await self.bus.wait_for_connection(1.0)

        def tearDown(self):
            self.conn.send(True)
            self.p_remote.join()
            self.bus = None

        def _get_bus(self) -> SessionBus:
            raise NotImplementedError

        @staticmethod
        def _get_remote_bus() -> SessionBus:
            raise NotImplementedError

        async def _rcv(self):
            return await asyncio.wait_for(
                asyncio.to_thread(self.conn.recv), timeout=1.0
            )

        async def _command(self, c: str):
            self.conn.send(c)
            assert await self._rcv() == "done"

        async def test_register(self):
            # local object
            with self.assertRaises(ObjectNotAvailable):
                proxy = await self.bus.get("local_object")
            o = DemoClass()
            await self.bus.register("local_object", o)
            proxy = await self.bus.get("local_object")

            # remote object
            with self.assertRaises(ObjectNotAvailable):
                proxy = await self.bus.get("remote_object")
            await self._command("register")
            proxy = await self.bus.get("remote_object")

        async def test_call(self):
            # local object
            o = DemoClass()
            await self.bus.register("local_object", o)
            proxy = await self.bus.get("local_object")
            await proxy.call("set", 1)
            self.assertEqual(1, await proxy.call("get"))

            # remote object
            await self._command("register")
            proxy = await self.bus.get("remote_object")
            await proxy.call("set", 1)
            self.assertEqual(1, await proxy.call("get"))

        async def test_notify(self):
            store = DemoClass()

            # local object
            o = DemoClass()
            await self.bus.register("local_object", o)
            proxy = await self.bus.get("local_object")
            await proxy.subscribe("test_signal", store.set)
            await o.test_signal.notify(1)
            self.assertEqual(1, store.get())

            # remote object
            await self._command("register")
            proxy = await self.bus.get("remote_object")
            await proxy.subscribe("test_signal", store.set)
            await o.test_signal.notify(2)
            self.assertEqual(2, store.get())

        async def test_bus_callbacks(self):
            self.assertEqual(("connect",), self.event_log.pop())


class TestClientTcp(Hidden.TestCommon):
    def _get_bus(self):
        return SessionBus(36475, client_only=True)

    @staticmethod
    def _get_remote_bus():
        return SessionBus(36475, server_only=True)


class TestServerTcp(Hidden.TestCommon):
    def _get_bus(self):
        return SessionBus(36475, server_only=True)

    @staticmethod
    def _get_remote_bus():
        return SessionBus(36475, client_only=True)


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class TestClientUnix(Hidden.TestCommon):
    def _get_bus(self):
        return SessionBus("/tmp/test", client_only=True)

    @staticmethod
    def _get_remote_bus():
        return SessionBus("/tmp/test", server_only=True)


@unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
class TestServerUnix(Hidden.TestCommon):
    def _get_bus(self):
        return SessionBus("/tmp/test", server_only=True)

    @staticmethod
    def _get_remote_bus():
        return SessionBus("/tmp/test", client_only=True)


if __name__ == "__main__":
    # don't inherit file handles
    set_start_method("forkserver")
    unittest.main()
