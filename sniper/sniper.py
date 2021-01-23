import os.path
import json
import threading
from httpstuff import ProxyPool
from itertools import cycle

try:
    with open("cookie.txt") as fp:
        COOKIE = fp.read().strip()
except FileNotFoundError:
    exit("The cookie.txt file doesn't exist, or is empty.")

try:
    with open("config.json") as fp:
        config_data = json.load(fp)
        PRICE_CHECK_THREADS = int(config_data["price_check_threads"])
        ASSET_IDS = list(map(int, config_data["asset_ids"]))
        del config_data
except FileNotFoundError:
    exit("The config.json file doesn't exist, or is corrupted.")

proxy_pool = ProxyPool(PRICE_CHECK_THREADS)
try:
    proxy_pool.load("proxies.txt")
except FileNotFoundError:
    exit("The proxies.txt file was not found")

asset_id_iter = cycle(ASSET_IDS)

class PriceCheckThread(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        while True:
            asset_id = next(ASSET_IDS)
            proxy = proxy_pool.get()
            print(proxy)

pc_threads = [PriceCheckThread() for _ in range(PRICE_CHECK_THREADS)]
for t in pc_threads: t.start()