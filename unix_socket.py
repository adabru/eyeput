import os, socket


class UnixSocket:
    reconnect = False

    def __init__(self, path, msg_length):
        self.path = path
        self.msg_length = msg_length
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(False)

    def try_send(self, msg):
        try:
            if self.reconnect:
                self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                self.sock.setblocking(False)
                self.sock.connect(self.path)
                self.reconnect = False
            self.send(msg)

        except (BrokenPipeError, ConnectionRefusedError) as e:
            self.sock.close()
            self.reconnect = True

        except OSError as e:
            if e.errno == 107:  # Transport endpoint is not connected
                try:
                    self.sock.connect(self.path)
                    self.send(msg)
                except FileNotFoundError:
                    pass  # server is not running
                except ConnectionRefusedError:
                    pass  # socket exists, but server is not running
            else:
                raise e

    def close_connection(self):
        self.connection.close()

    def listen(self):
        mask = os.umask(~0o662)
        try:
            os.unlink(self.path)
        except OSError:
            if os.path.exists(self.path):
                raise

        self.sock.bind(self.path)
        self.sock.listen(1)
        os.umask(mask)

    def accept(self):
        self.sock.setblocking(True)
        self.connection, client_address = self.sock.accept()

    def send(self, msg):
        if isinstance(msg, str):
            msg = msg.encode()
        packet = msg.ljust(self.msg_length, b"\0")
        totalsent = 0
        while totalsent < self.msg_length:
            sent = self.sock.send(packet[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < self.msg_length:
            chunk = self.connection.recv(min(self.msg_length - bytes_recd, 2048))
            if chunk == b"":
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)

        return b"".join(chunks)

    def receive_string(self):
        return self.receive().strip(b"\0").decode()
