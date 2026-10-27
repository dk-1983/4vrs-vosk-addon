"""Wyoming Describe must remain responsive while recognition runs."""
import json
import socket

try:
    with socket.create_connection(('127.0.0.1', 10301), timeout=3) as sock:
        sock.sendall(b'{"type":"describe"}\n')
        with sock.makefile('rb') as reader:
            data = json.loads(reader.readline(65536))
            if data.get('type') != 'info':
                raise SystemExit(1)
except (OSError, ValueError):
    raise SystemExit(1) from None
