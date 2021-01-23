import os.path
import json
import threading
import requests
from httpstuff import ProxyPool, AlwaysAliveConnection
from itertools import cycle

# load cookie
try:
    with open("cookie.txt") as fp:
        COOKIE = fp.read().strip()
except FileNotFoundError:
    exit("The cookie.txt file doesn't exist, or is empty.")

# load config
try:
    with open("config.json") as fp:
        config_data = json.load(fp)
        PRICE_CHECK_THREADS = int(config_data["price_check_threads"])
        ASSET_IDS = list(map(int, config_data["asset_ids"]))
        del config_data
except FileNotFoundError:
    exit("The config.json file doesn't exist, or is corrupted.")

# load proxies
proxy_pool = ProxyPool(PRICE_CHECK_THREADS)
try:
    with open("proxies.txt") as f:
        proxy_pool.load(f.read().splitlines())
except FileNotFoundError:
    exit("The proxies.txt file was not found")

asset_url_iter = cycle([
    requests.get(f"https://www.roblox.com/library/{asset_id}/--", allow_redirects=False).url
    for asset_id in ASSET_IDS
])
target = None
target_lock = threading.Lock()

class BuyThread(threading.Thread):
    def __init__(self):
        super().__int__()
        self.conn = AlwaysAliveConnection("economy.roblox.com", refresh_interval=5)
        self.event = threading.Event()
    
    def run(self):
        while True:
            self.event.wait()
            self.event.clear()
            conn = self.conn.get()

class PriceCheckThread(threading.Thread):
    def __init__(self, buy_threads):
        super().__init__()
        self.buy_threads = buy_threads
    
    def run(self):
        while True:
            asset_url = next(asset_url_iter)
            proxy = proxy_pool.get()
            
            try:
                conn = proxy.get_connection("www.roblox.com")
                conn.putrequest("GET", asset_url, True, True)
                conn.putheader("User-Agent", "Roblox/WinInet")
                conn.endheaders()
                resp = conn.getresponse()
                data = resp.read()
                print(data)
                proxy_pool.put(proxy)
            except:
                pass

buy_threads = [BuyThread() for _ in range(1)]
for t in buy_threads: t.start()
pc_threads = [PriceCheckThread(buy_threads) for _ in range(PRICE_CHECK_THREADS)]
for t in pc_threads: t.start()