import asyncio
import sys
from pathlib import Path
from typing import Callable, List


class SessionBus:
    socket_path: str

    def __init__(self, socket_path: str):
        self.socket_path = socket_path

    def register(self, bus_name: str, local_object: object):
        pass

    def get(self, bus_name: str) -> "BusProxy":
        return BusProxy()

    async def list_objects(self) -> List:
        return []

    def subscribe(self, callback: Callable[[str, object], None]):
        pass


class BusProxyRequest:
    async def result(self):
        pass


class BusProxy:
    def call(self, func_name, *args) -> "BusProxyRequest":
        return BusProxyRequest()

    def subscribe(self, signal_name: str, callback: Callable[..., None]):
        pass

    async def inspect_interface(self):
        pass


class BusSignal:
    def notify(*args):
        pass


class TimeoutException(Exception):
    pass


class MalformedException(Exception):
    pass


class NotAvailableException(Exception):
    pass


class NoServerException(Exception):
    pass


class AuthenticationException(Exception):
    pass


# test
if Path(sys.argv[0]).name == Path(__file__).name:
    from subprocess import Popen

    # https://github.com/cursorless-dev/cursorless/issues/541

    bus = SessionBus("/tmp/test")

    if len(sys.argv) == 1:
        print("start A")
        pA = Popen(["python", __file__, "A"])
        print("start B")
        pB = Popen(["python", __file__, "B"])
        pA.wait()
        pB.wait()

    elif sys.argv[1] == "A":
        print("[A]", "testing api")

        # expose local object to bus
        class C:
            some_signal = BusSignal()

            def do_something(p1: str):
                print(p1)

        o = C()
        bus.register("test.o", o)

        # publish and subscribe
        o.some_signal.notify("sleep", True)

    elif sys.argv[1] == "B":

        async def run():
            print("[B]", "testing api")
            try:
                # consume remote object
                proxy = bus.get("vscode.command_server")

                # request and response
                rpc_request = proxy.call("do_something", "apple")
                await rpc_request.result()

                # publish and subscribe
                def callback(p1: str, p2: bool):
                    print(p1, p2)

                proxy.subscribe("some_signal", callback)

            except TimeoutException as e:
                pass
            except MalformedException as e:
                pass
            except NotAvailableException as e:
                pass
            except NoServerException as e:
                pass
            except AuthenticationException as e:
                pass

            # bus functions
            print(await bus.list_objects())

            def callback(event_type: str, event_data: object):
                print(event_type)

            bus.subscribe(callback)
            print(await proxy.inspect_interface())

        asyncio.run(run())
