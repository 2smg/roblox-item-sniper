import threading
import http.client
import random
import time
from collections import deque
from urllib.parse import urlparse

class AlwaysAliveConnection:
    def __init__(self, hostname, refresh_interval):
        self.hostname = hostname
        self.refresh_interval = refresh_interval
        self.connection = None
        self.event = threading.Event()
        self.thread = threading.Thread(target=self.updater)
        self.thread.start()

    def get(self):
        if not self.connection:
            self.event.wait()
            self.event.clear()
        return self.connection
    
    def updater(self):
        while 1:
            try:
                conn = http.client.HTTPSConnection(self.hostname, 443)
                # fun fact: it won't actually connect until you call .endheaders/.request or .connect
                conn.connect()
                self.connection = conn
                time.sleep(self.refresh_interval)
            except Exception as err:
                print("AlwaysAliveConnection thread error:", err, type(err))

class Proxy:
    def __init__(self, proxy):
        self.raw_proxy = proxy
        self.proxy = urlparse("http://" + proxy)
        self.connection_map = {}

    def __del__(self):
        for conn in list(self.connection_map.values()):
            conn.close()
    
    def get_connection(self, hostname, force=False) -> http.client.HTTPSConnection:
        hostname = hostname.lower()
        if not force and hostname in self.connection_map:
            return self.connection_map[hostname]
        
        conn = http.client.HTTPSConnection(self.proxy.hostname, self.proxy.port, timeout=5)
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
            if len(self.alive_proxies):
                return self.alive_proxies.pop()
            return Proxy(random.choice(self.raw_proxies))

    def put(self, proxy):
        with self.lock:
            self.alive_proxies.append(proxy)