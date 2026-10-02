"""Small CONNECT-only proxy. Exact public OpenAI destinations; no TLS inspection."""
import ipaddress
import json
import select
import socket
import socketserver
import sys

HOSTS = frozenset({'api.openai.com', 'chatgpt.com', 'auth.openai.com'})

def permitted(authority):
    parts = authority.split(':')
    return (parts[0], 443) if len(parts) == 2 and parts[0] in HOSTS and parts[1] == '443' else None

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(10)
        data = b''
        try:
            while b'\r\n\r\n' not in data and len(data) <= 8192:
                chunk = self.request.recv(4096)
                if not chunk: return
                data += chunk
            line = data.split(b'\r\n', 1)[0].decode('ascii').split()
            dest = permitted(line[1]) if len(line) == 3 and line[0] == 'CONNECT' else None
            if dest is None or len(data) > 8192:
                print(json.dumps({'decision': 'deny'}), flush=True)
                self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n')
                return
            host, port = dest
            addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
                raise OSError('non-public upstream')
            address = next((a for a in addresses if a[0] == socket.AF_INET), addresses[0])
            with socket.create_connection((address[4][0], port), timeout=15) as upstream:
                print(json.dumps({'decision': 'allow', 'host': host, 'port': port}), flush=True)
                self.request.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                self.request.settimeout(None)
                upstream.settimeout(None)
                while True:
                    ready, _, _ = select.select([self.request, upstream], [], [], 900)
                    if not ready: return
                    for source in ready:
                        chunk = source.recv(65536)
                        if not chunk: return
                        (upstream if source is self.request else self.request).sendall(chunk)
        except (OSError, UnicodeError, ValueError):
            print(json.dumps({'decision': 'upstream_error'}), flush=True)

class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == '__main__':
    # Bound only to the internal interface, never to the egress interface.
    with Server((sys.argv[1], 3128), Handler) as server:
        print('{"ready":true}', flush=True)
        server.serve_forever()
