import os
import subprocess
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs

# Configuration
START_PORT = 13000
POOL_SIZE = 30

def parse_proxy_line(line):
    line = line.strip()
    if not line or line.startswith("#"): return None
    parts = line.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        return f"http://{user}:{password}@{host}:{port}"
    if line.startswith(("http://", "https://", "socks5://")):
        return line
    return None

PROXIES = []
with open("PROXY", "r", encoding="utf-8") as f:
    for line in f:
        p = parse_proxy_line(line)
        if p: PROXIES.append(p)

# Dictionary to hold {port: {"process": subprocess, "proxy_index": int}}
active_processes = {}
lock = threading.Lock()
master_index = 0

def start_port(port):
    global master_index
    
    # Kill existing process on this port if it exists
    if port in active_processes and active_processes[port]["process"]:
        active_processes[port]["process"].terminate()
        active_processes[port]["process"].wait()

    # Get the next proxy from the master list
    proxy_url = PROXIES[master_index % len(PROXIES)]
    master_index += 1

    print(f"[*] Port {port} -> Upstream: {proxy_url}")
    
    # Launch GOST on this specific port, silencing its massive JSON logs!
    proc = subprocess.Popen(
        ["./gost", f"-L=socks5://127.0.0.1:{port}", f"-F={proxy_url}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    active_processes[port] = {"process": proc, "proxy_index": master_index - 1}

class ControlHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/swap":
            query = parse_qs(parsed_path.query)
            if 'port' in query:
                port = int(query['port'][0])
                with lock:
                    if port in active_processes:
                        start_port(port)
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(f'{{"status": "swapped", "port": {port}}}'.encode())
                        return
            self.send_error(400, "Invalid port")
        else:
            self.send_error(404)
            
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print(f"[+] Loaded {len(PROXIES)} proxies. Starting pool of {POOL_SIZE}...")
    
    # Boot up the 30 proxies
    for i in range(POOL_SIZE):
        start_port(START_PORT + i)

    socketserver.TCPServer.allow_reuse_address = True
    # Upgraded to ThreadingTCPServer to prevent bottlenecks on simultaneous swaps
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 5000), ControlHandler)
    print(f"\n[*] Proxy Pool Active on ports {START_PORT} to {START_PORT + POOL_SIZE - 1}")
    print("[*] Control API listening on 127.0.0.1:5000/swap?port=XXXX")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down all proxies...")
        for port, data in active_processes.items():
            data["process"].terminate()