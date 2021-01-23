import threading
import http.client
from collections import deque
from urllib.parse import urlparse

class Proxy:
    def __init__(self, proxy):
        self.raw_proxy = proxy
        self.proxy = urlparse("http://" + proxy)
        self.connection_map = {}

    def __exit__(self):
        for conn in list(self.connection_map.values()):
            conn.close()
    
    def get_connection(self, hostname, force=False):
        hostname = hostname.lower()
        if not force and hostname in self.connection_map:
            return self.connection_map[hostname]
        
        conn = http.client.HTTPSConnection(self.proxy.hostname, self.proxy.port)
        conn.set_tunnel(hostname, 443)
        self.connection_map[hostname] = conn
        return conn

class ProxyPool:
    def __init__(self, max_alive=50):
        self.raw_proxies = []
        self.alive_proxies = deque(maxlen=max_alive)
        self.lock = threading.Lock()

    def load(self, proxy_list):
        with self.lock:
            for proxy in proxy_list:
                self.raw_proxies.append(proxy)
    
    def get(self):
        with self.lock:
            if self.alive_proxies:
                return self.alive_proxies.pop(0)
            return Proxy(self.raw_proxies.pop(0))

    def put(self, proxy):
        with self.lock:
            self.alive_proxies.append(proxy)