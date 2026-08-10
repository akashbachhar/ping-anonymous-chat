"""Peer connection management: inbound listener, outbound dialing, and I/O.

Ping supports a single live conversation at a time. A lock guards the active
socket so that a simultaneous inbound and outbound attempt cannot both win.
All notifications to the UI go through :class:`AppSignals`.
"""

import socket
import threading
import time

import socks

from . import config
from .protocol import StreamDecoder, encode_file, encode_text


class ConnectionManager:
    def __init__(self, signals):
        self.signals = signals
        self._lock = threading.Lock()
        self._sock = None
        self._active = False
        self._server = None
        self._running = True
        self._intentional = False  # was the most recent drop user-initiated?

    # ---------------- Inbound ----------------

    def start_listener(self):
        """Bind the local port Tor forwards to and accept peers serially."""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(("127.0.0.1", config.LOCAL_CHAT_PORT))
        self._server.listen(1)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self._running:
            try:
                conn, _ = self._server.accept()
            except OSError:
                break  # server socket closed during shutdown
            with self._lock:
                if self._active:
                    conn.close()  # already chatting; refuse the newcomer
                    continue
                self._sock = conn
                self._active = True
            self.signals.connected.emit("")  # inbound peer: address unknown
            self._start_recv(conn)

    # ---------------- Outbound ----------------

    def connect_to(self, address: str):
        threading.Thread(
            target=self._outbound_worker, args=(address,), daemon=True
        ).start()

    def _outbound_worker(self, address: str):
        self.signals.status_update.emit(f"Connecting to {address}...")
        sock = None
        for attempt in range(config.CONNECT_RETRIES):
            with self._lock:
                if self._active:
                    return  # a peer connected to us meanwhile
            try:
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, "127.0.0.1", config.SOCKS_PORT)
                sock.connect((address, config.ONION_PORT))
                break
            except (socks.GeneralProxyError, socks.ProxyConnectionError, OSError):
                self.signals.status_update.emit(
                    f"Retrying ({attempt + 1}/{config.CONNECT_RETRIES})..."
                )
                time.sleep(config.CONNECT_RETRY_DELAY)
        else:
            self.signals.connect_failed.emit("Failed to connect after retries.")
            return

        with self._lock:
            if self._active:
                sock.close()
                return
            self._sock = sock
            self._active = True
        self.signals.connected.emit(address)  # outbound: we know the peer address
        self._start_recv(sock)

    # ---------------- Shared I/O ----------------

    def _start_recv(self, sock):
        threading.Thread(target=self._recv_worker, args=(sock,), daemon=True).start()

    def _recv_worker(self, sock):
        decoder = StreamDecoder()
        while True:
            try:
                data = sock.recv(config.RECV_BUFFER)
            except OSError:
                break
            if not data:
                break
            try:
                for message in decoder.feed(data):
                    if message.kind == "file":
                        self.signals.file_received.emit(message.filename, message.data)
                    else:
                        self.signals.message_received.emit(message.text)
            except ValueError:
                break  # protocol violation; drop the peer
        self._handle_drop()

    def _handle_drop(self):
        with self._lock:
            intentional = self._intentional
            self._intentional = False
            self._active = False
            sock, self._sock = self._sock, None
        if sock:
            try:
                sock.close()
            except OSError:
                pass
        self.signals.disconnected.emit(intentional)

    def send(self, text: str) -> bool:
        """Frame and send a text message. Returns False if the link is gone."""
        return self._send_raw(encode_text(text))

    def send_file(self, filename: str, data: bytes) -> bool:
        """Frame and send a file. Returns False if the link is gone."""
        return self._send_raw(encode_file(filename, data))

    def _send_raw(self, framed: bytes) -> bool:
        with self._lock:
            sock = self._sock if self._active else None
        if not sock:
            return False
        try:
            sock.sendall(framed)
            return True
        except OSError:
            return False

    def disconnect(self):
        """End the current conversation on purpose (user pressed leave/close)."""
        with self._lock:
            if not self._active:
                return
            self._intentional = True
            sock = self._sock
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

    def shutdown(self):
        """Stop accepting and close everything. Called on app exit."""
        self._running = False
        self.disconnect()
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None
