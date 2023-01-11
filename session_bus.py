#
# References:
#
# https://github.com/cursorless-dev/cursorless/issues/541
#
# jsonrpc
# https://www.jsonrpc.org/specification
#
# asyncio sockets
# https://docs.python.org/3/library/asyncio-stream.html#asyncio.start_unix_server
# https://docs.python.org/3/library/socket.html?highlight=socket#module-socket
#


import asyncio
from concurrent.futures import Future
from inspect import getmembers
import logging
import time
import os
from pathlib import Path
from typing import Callable, Dict, List, Tuple
from random import random
import json


class ParseError(Exception):
    code = -32700


class InvalidRequest(Exception):
    code = -32600


class MethodNotFound(Exception):
    code = -32601


class ObjectNotAvailable(Exception):
    code = -32000


class ExecutionError(Exception):
    code = -32001


class NoServerError(Exception):
    pass


class AuthenticationError(Exception):
    pass


def rpc_error(cls: type, message: str):
    return {"code": cls.code, "message": message}


def _get_interface(local_object: object):
    return local_object.__class__.__name__


async def _call_func(local_object: object, func_name: str, *args):
    try:
        result = getattr(local_object, func_name)(*args)
        if asyncio.iscoroutine(result):
            result = await result
        return result
    except Exception as e:
        logging.error(e, exc_info=True)
        raise ExecutionError(e)


# Logging for debugging
debug_level: int = 0


def _debug_print(level, *args):
    if debug_level >= level:
        print(*args)


class _Connection:
    """Shared functionality between server and client."""

    pending_requests: Dict[str, asyncio.Future]
    local_objects: Dict[str, object]
    local_listeners: Dict[Tuple[str, str], Callable[..., None]]
    peers: Dict[object, Tuple[asyncio.StreamReader, asyncio.StreamWriter]]

    def __init__(self):
        self.pending_requests = {}
        self.local_objects = {}
        self.local_listeners = {}
        self.peers = {}

    async def _encode(self, message: object, writer: asyncio.StreamWriter):
        chunk = json.dumps(message).encode()
        writer.write(len(chunk).to_bytes(4, "big"))
        writer.write(chunk)
        await writer.drain()

    async def _decode(self, reader: asyncio.StreamReader):
        n = int.from_bytes(await reader.readexactly(4), "big")
        chunk = await reader.readexactly(n)
        return json.loads(chunk)

    async def _read_message(self, peer_id: object):
        try:
            message = await self._decode(self.peers[peer_id][0])
        except json.JSONDecodeError as e:
            await self.respond(None, peer_id, error=rpc_error(ParseError, e.msg))
            return
        if "id" in message and "method" in message:
            await self._handle_request(peer_id, message)
        elif "id" in message and ("result" in message or "error" in message):
            await self._handle_response(peer_id, message)
        elif "method" in message:
            await self._handle_notification(peer_id, message)

    async def start(self, socket_path: Path):
        raise NotImplementedError

    async def serve(self):
        raise NotImplementedError

    async def _handle_request(self, peer_id: object, message: object):
        raise NotImplementedError

    async def _handle_response(self, peer_id: object, message: object):
        id = message["id"]
        if id == None:
            # id is not assignable, take random
            request = self.pending_requests.popitem()[1]
        elif not id in self.pending_requests:
            print("Received response with unknown id.")
            return
        else:
            request = self.pending_requests.pop(id)

        if "result" in message:
            request.set_result(message["result"])
        else:
            error = message["error"]
            if error["code"] == ParseError.code:
                request.set_exception(ParseError(error["message"]))
            elif error["code"] == InvalidRequest.code:
                request.set_exception(InvalidRequest(error["message"]))
            elif error["code"] == MethodNotFound.code:
                request.set_exception(MethodNotFound(error["message"]))
            elif error["code"] == ObjectNotAvailable.code:
                request.set_exception(ObjectNotAvailable(error["message"]))
            elif error["code"] == ExecutionError.code:
                request.set_exception(ExecutionError(error["message"]))
            else:
                print("Unknown error code: ", error["code"])
                request.set_exception(RuntimeError(error["message"]))

    async def _handle_notification(self, peer_id: object, message: object):
        raise NotImplementedError

    async def request(self, method: str, params: object, peer_id: object):
        id = random()
        assert not id in self.pending_requests
        request = asyncio.get_running_loop().create_future()
        self.pending_requests[id] = request
        message = {"jsonrpc": "2.0", "method": method, "params": params, "id": id}
        await self._encode(message, self.peers[peer_id][1])
        result = await request
        return result

    async def respond(
        self,
        id: float,
        peer_id: object,
        result: object = None,
        error: object = None,
    ):
        assert (result is None) or (error is None)
        message = {"jsonrpc": "2.0", "id": id}
        if error != None:
            message["error"] = error
        else:
            message["result"] = result
        await self._encode(message, self.peers[peer_id][1])

    async def request_notification(self, method: str, params: object, peer_id: object):
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        await self._encode(message, self.peers[peer_id][1])

    def _local_register(self, bus_name: str, local_object: object):
        self.local_objects[bus_name] = local_object

    async def register(self, bus_name: str, local_object: object):
        raise NotImplementedError

    async def call(self, bus_name: str, func_name: str, *args):
        raise NotImplementedError

    async def subscribe_signal(
        self, bus_name: str, signal_name: str, callback: Callable[..., None]
    ):
        self.local_listeners[(bus_name, signal_name)] = callback

    def _local_notify(self, bus_name: str, signal_name: str, signal_data: List):
        callback = self.local_listeners.get((bus_name, signal_name), None)
        if callback != None:
            try:
                callback(*signal_data)
            except Exception as e:
                logging.error(e, exc_info=True)

    async def notify(self, bus_name: str, signal_name: str, signal_data: List):
        self._local_notify(bus_name, signal_name, signal_data)
        # relay notification
        for peer_id in self.peers.keys():
            await self.request_notification(
                "signal",
                {
                    "bus_name": bus_name,
                    "signal_name": signal_name,
                    "signal_data": signal_data,
                },
                peer_id,
            )

    async def inspect_interface(self, bus_name: str):
        raise NotImplementedError


class _Client(_Connection):
    async def start(self, socket_path: Path):
        try:
            # client has only one peer
            peer_id = 0
            self.peers[peer_id] = await asyncio.open_unix_connection(socket_path)
        except (ConnectionRefusedError, FileNotFoundError) as e:
            raise NoServerError()

    async def serve(self):
        peer_id = 0
        (reader, writer) = self.peers[peer_id]
        try:
            while True:
                await self._read_message(peer_id)
        finally:
            writer.close()
            del self.peers[peer_id]

    async def _handle_request(self, peer_id: object, message: object):
        result = None
        error = None
        try:
            if message["method"] == "call":
                if message["params"]["bus_name"] in self.local_objects:
                    result = await self.call(
                        message["params"]["bus_name"],
                        message["params"]["func_name"],
                        *message["params"]["args"],
                    )
                else:
                    error = rpc_error(ObjectNotAvailable, "Not found.")
            elif message["method"] == "inspect_interface":
                if message["params"]["bus_name"] in self.local_objects:
                    result = _get_interface(
                        self.local_objects[message["params"]["bus_name"]]
                    )
                else:
                    error = rpc_error(ObjectNotAvailable, "Not found.")
            else:
                error = rpc_error(MethodNotFound, "Not found.")
        except KeyError as e:
            error = rpc_error(InvalidRequest, repr(e))
        except ExecutionError as e:
            error = rpc_error(ExecutionError, repr(e))
        await self.respond(message["id"], peer_id, result=result, error=error)

    async def _handle_notification(self, peer_id: object, message: object):
        self._local_notify(
            message["params"]["bus_name"],
            message["params"]["signal_name"],
            message["params"]["signal_data"],
        )

    async def register(self, bus_name: str, local_object: object):
        self._local_register(bus_name, local_object)
        await self.request("register", {"bus_name": bus_name}, 0)

    async def call(self, bus_name: str, func_name: str, *args):
        if bus_name in self.local_objects:
            return await _call_func(self.local_objects[bus_name], func_name, *args)
        else:
            return await self.request(
                "call", {"bus_name": bus_name, "func_name": func_name, "args": args}, 0
            )

    async def inspect_interface(self, bus_name: str):
        if bus_name in self.local_objects:
            return _get_interface(self.local_objects[bus_name])
        else:
            return await self.request("inspect_interface", {"bus_name": bus_name}, 0)


class _Server(_Connection):
    remote_objects: Dict[str, object]
    server: asyncio.Server

    def __init__(self):
        super().__init__()
        self.remote_objects = {}

    def _unregister_client(self, peer_id: object):
        del self.peers[peer_id]
        self.remote_objects = {
            i: j for i, j in self.remote_objects.items() if j != peer_id
        }

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        peer_id = random()
        self.peers[peer_id] = (reader, writer)
        try:
            while True:
                await self._read_message(peer_id)
        except asyncio.IncompleteReadError:
            pass
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            self._unregister_client(peer_id)
            writer.close()

    async def start(self, socket_path: Path):
        mask = os.umask(~0o662)
        try:
            socket_path.unlink()
        except OSError:
            if socket_path.exists():
                raise
        os.umask(mask)
        # https://github.com/python/cpython/blob/1a6bacb31f7b49c244a6cc3ff0fa7f71a82412ef/Lib/asyncio/unix_events.py#L282
        self.server = await asyncio.start_unix_server(
            self._handle_client, socket_path, start_serving=False
        )

    async def serve(self):
        async with self.server:
            await self.server.serve_forever()

    async def wait_serving(self):
        while not self.server.is_serving():
            await asyncio.sleep(0.001)

    async def _handle_request(self, peer_id: object, message: object):
        result = None
        error = None
        try:
            if message["method"] == "register":
                self.remote_objects[message["params"]["bus_name"]] = peer_id
                result = "ok"
            elif message["method"] == "call":
                try:
                    result = await self.call(
                        message["params"]["bus_name"],
                        message["params"]["func_name"],
                        *message["params"]["args"],
                    )
                except ObjectNotAvailable:
                    error = rpc_error(ObjectNotAvailable, "Not found.")
            elif message["method"] == "inspect_interface":
                try:
                    result = await self.inspect_interface(message["params"]["bus_name"])
                except ObjectNotAvailable:
                    error = rpc_error(ObjectNotAvailable, "Not found.")
            else:
                error = rpc_error(MethodNotFound, "Not found.")
        except KeyError as e:
            error = rpc_error(InvalidRequest, repr(e))
        except ExecutionError as e:
            error = rpc_error(ExecutionError, repr(e))
        await self.respond(message["id"], peer_id, result=result, error=error)

    async def _handle_notification(self, peer_id: object, message: object):
        self._local_notify(
            message["params"]["bus_name"],
            message["params"]["signal_name"],
            message["params"]["signal_data"],
        )
        # relay notification
        for id in self.peers.keys():
            if id != peer_id:
                await self.request_notification(
                    message["method"],
                    message["params"],
                    peer_id,
                )

    async def register(self, bus_name: str, local_object: object):
        self._local_register(bus_name, local_object)

    async def call(self, bus_name: str, func_name: str, *args):
        if bus_name in self.local_objects:
            return await _call_func(self.local_objects[bus_name], func_name, *args)
        elif bus_name in self.remote_objects:
            return await self.request(
                "call",
                {"bus_name": bus_name, "func_name": func_name, "args": args},
                self.remote_objects[bus_name],
            )
        else:
            raise ObjectNotAvailable()

    async def inspect_interface(self, bus_name: str):
        if bus_name in self.local_objects:
            return _get_interface(self.local_objects[bus_name])
        elif bus_name in self.remote_objects:
            return await self.request(
                "inspect_interface",
                {"bus_name": bus_name},
                self.remote_objects[bus_name],
            )
        else:
            raise ObjectNotAvailable()


class SessionBus:
    # Don't try to start server if set to True and no server found
    client_only: bool
    # Don't try to connect as client
    server_only: bool
    # All applications with the same path connect to the same bus
    socket_path: Path
    # Set to true when the connection is successful
    is_connected: asyncio.Future[bool]
    # The listening task
    io_task: asyncio.Task = None
    # Either client or server
    connection: _Connection = None
    # Timeout for connecting to a server, only relevant if client_only=True
    timeout: float
    # Listeners for connection and register events
    bus_listeners: List[Callable[..., None]]
    # The event loop this bus is running in
    asyncio_loop: asyncio.AbstractEventLoop

    def __init__(
        self,
        socket_path: str,
        client_only: bool = False,
        server_only: bool = False,
        timeout: float = 1.0,
    ):
        self.socket_path = Path(socket_path)
        self.client_only = client_only
        self.server_only = server_only
        self.timeout = timeout
        self.bus_listeners = []
        try:
            self.asyncio_loop = asyncio.get_running_loop()
            self.is_connected = asyncio.get_running_loop().create_future()
            self._start()
        except RuntimeError:
            # no event loop running
            _debug_print(
                1,
                "Bus created without an event loop running. Remember to call async_init.",
            )

    def async_init(self):
        self.asyncio_loop = asyncio.get_running_loop()
        self.is_connected = asyncio.get_running_loop().create_future()
        self._start()

    def _exception(self, io_task: asyncio.Task):
        if self.is_connected.done():
            self.is_connected = asyncio.get_running_loop().create_future()
        # propagate exception to bus users
        try:
            self.is_connected.set_exception(io_task.exception())
        except asyncio.CancelledError:
            pass

    def _start(self):
        if self.io_task is None:
            self.io_task = asyncio.create_task(self._run())
            # add exception handler, actually no exception should occur here
            self.io_task.add_done_callback(self._exception)

    async def _run(self):
        def notify_connect():
            self.is_connected.set_result(True)
            for listener in self.bus_listeners:
                listener("connect")

        while True:
            if not self.server_only:
                # try to connect to existing server first
                try:
                    client = _Client()
                    await client.start(self.socket_path)
                    self.connection = client
                    notify_connect()
                    _debug_print(1, "client connection")
                    await self.connection.serve()
                except (NoServerError, asyncio.IncompleteReadError):
                    _debug_print(1, "client connection failed")

            if not self.client_only:
                # start server otherwise
                server = _Server()
                await server.start(self.socket_path)
                server_task = asyncio.create_task(server.serve())
                await server.wait_serving()

                # check for race condition on socket file
                unique_id = random()
                await server.register(unique_id, object())
                client = _Client()
                await client.start(self.socket_path)
                client_task = asyncio.create_task(client.serve())
                race = False
                try:
                    await client.inspect_interface(unique_id)
                except ObjectNotAvailable:
                    # race detected
                    race = True

                if race:
                    if not self.server_only:
                        # run as client
                        _debug_print(1, "client connection after race")
                        server_task.cancel()
                        self.connection = client
                        notify_connect()
                        try:
                            await client_task
                        except asyncio.IncompleteReadError:
                            pass
                    else:
                        raise RuntimeError("Another server is already running")
                else:
                    # run as server
                    _debug_print(1, "server connection")
                    client_task.cancel()
                    self.connection = server
                    notify_connect()
                    await server_task

            if not self.is_connected.done():
                self.is_connected.set_exception(
                    ConnectionError("Connection to server failed")
                )
                # get rid of "Future exception was never retrieved"
                def swallow(future):
                    try:
                        future.result()
                    except Exception:
                        pass

                self.is_connected.add_done_callback(swallow)

            self.is_connected = asyncio.get_running_loop().create_future()
            # wait some time before trying to reconnect
            await asyncio.sleep(0.1)

    async def wait_for_connection(self, timeout: float = 3.0):
        t0 = time.perf_counter()
        while True:
            try:
                t1 = time.perf_counter()
                done, pending = await asyncio.wait(
                    [self.is_connected], timeout=timeout - (t1 - t0)
                )
                if len(pending) == 1:
                    raise TimeoutError()
                # consume potential exception
                await self.is_connected
                break
            except ConnectionError:
                pass

    async def call(self, bus_name: str, func_name: str, *args):
        await self.wait_for_connection(timeout=self.timeout)
        return await self.connection.call(bus_name, func_name, *args)

    async def register(self, bus_name: str, local_object: object):
        await self.wait_for_connection(timeout=self.timeout)
        await self.connection.register(bus_name, local_object)
        # initialize signals
        for key, value in getmembers(local_object):
            if isinstance(value, BusSignal):
                value.bus = self
                value.bus_name = bus_name
                if value.signal_name == None:
                    value.signal_name = key

    async def get(self, bus_name: str) -> "BusProxy":
        await self.wait_for_connection(timeout=self.timeout)
        proxy = BusProxy(self, bus_name)
        # check connection
        await proxy.inspect_interface()
        return proxy

    async def subscribe_signal(
        self, bus_name: str, signal_name: str, callback: Callable[..., None]
    ):
        await self.wait_for_connection(timeout=self.timeout)
        return await self.connection.subscribe_signal(bus_name, signal_name, callback)

    async def notify(self, bus_name: str, signal_name: str, signal_data: List):
        await self.wait_for_connection(timeout=self.timeout)
        return await self.connection.notify(bus_name, signal_name, signal_data)

    def subscribe(self, callback: Callable[..., None]):
        self.bus_listeners.append(callback)

    async def list_objects(self) -> List:
        await self.wait_for_connection(timeout=self.timeout)
        return []

    async def inspect_interface(self, bus_name: str):
        await self.wait_for_connection(timeout=self.timeout)
        return await self.connection.inspect_interface(bus_name)

    def schedule(self, future: asyncio.Future) -> Future:
        """Utility function for bus users that need to separate bus thread from other threads."""
        _future = asyncio.run_coroutine_threadsafe(future, self.asyncio_loop)
        # placeholder that consumes exceptions
        _future.add_done_callback(lambda future: future.result())
        return _future


class BusProxy:
    def __init__(self, bus: SessionBus, name: str):
        self.bus = bus
        self.name = name

    async def call(self, func_name, *args):
        return await self.bus.call(self.name, func_name, *args)

    async def subscribe(self, signal_name: str, callback: Callable[..., None]):
        return await self.bus.subscribe_signal(self.name, signal_name, callback)

    async def inspect_interface(self):
        return await self.bus.inspect_interface(self.name)


class BusSignal:
    signal_name: str
    bus_name: str
    bus: SessionBus

    def __init__(self, signal_name: str = None):
        self.signal_name = signal_name

    async def notify(self, *args):
        await self.bus.notify(self.bus_name, self.signal_name, args)
