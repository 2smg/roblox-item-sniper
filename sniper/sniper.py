import os.path
import json
import threading
import requests
import http.client
import re
import time
import ctypes
from httpstuff import ProxyPool, AlwaysAliveConnection
from itertools import cycle

xsrf_token = None
target = None
target_updated = 0
target_lock = threading.Lock()
refresh_count = 0

PRODUCT_ID_RE = re.compile(r'data\-product\-id="(\d+)"')
PRICE_RE = re.compile(r'data\-expected\-price="(\d+)"')
SELLER_ID_RE = re.compile(r'data\-expected\-seller-id="(\d+)"')
USERASSET_ID_RE = re.compile(r'data\-lowest\-private\-sale\-userasset\-id="(\d+)"')

def parse_item_page(data):
    product_id = int(PRODUCT_ID_RE.search(data).group(1))
    price = int(PRICE_RE.search(data).group(1))
    seller_id = int(SELLER_ID_RE.search(data).group(1))
    userasset_id = int(USERASSET_ID_RE.search(data).group(1))
    return product_id, price, seller_id, userasset_id

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
        XSRF_REFRESH_INTERVAL = float(config_data["xsrf_refresh_interval"])
        TARGET_ASSETS = config_data["targets"]
        del config_data
except FileNotFoundError:
    exit("The config.json file doesn't exist, or is corrupted.")

# load proxies
proxy_pool = ProxyPool(PRICE_CHECK_THREADS + 1)
try:
    with open("proxies.txt") as f:
        proxy_pool.load(f.read().splitlines())
except FileNotFoundError:
    exit("The proxies.txt file was not found")

target_iter = cycle([
    (
        requests.get(f"https://www.roblox.com/catalog/{asset_id}/--").url \
            .replace("https://www.roblox.com", ""),
        price
    )
    for asset_id, price in TARGET_ASSETS
])

class StatUpdater(threading.Thread):
    def __init__(self, refresh_interval):
        super().__init__()
        self.refresh_interval = refresh_interval
    
    def run(self):
        while 1:
            time.sleep(self.refresh_interval)
            ctypes.windll.kernel32.SetConsoleTitleW(f"refresh count: {refresh_count}")

class XsrfUpdateThread(threading.Thread):
    def __init__(self, refresh_interval):
        super().__init__()
        self.refresh_interval = refresh_interval
    
    def run(self):
        global xsrf_token

        while 1:
            try:
                conn = http.client.HTTPSConnection("www.roblox.com")
                conn.request("GET", "/home", headers={"Cookie": f".ROBLOSECURITY={COOKIE}"})
                resp = conn.getresponse()
                data = resp.read()
                new_xsrf = data.decode("UTF-8").split("setToken('")[1].split("'")[0]

                if new_xsrf != xsrf_token:
                    xsrf_token = new_xsrf
                    print("updated xsrf:", new_xsrf)

                time.sleep(self.refresh_interval)
            except Exception as err:
                print("xsrf update error:", err, type(err))

class BuyThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.conn = AlwaysAliveConnection("economy.roblox.com", refresh_interval=5)
        self.event = threading.Event()
    
    def run(self):
        while True:
            self.event.wait()
            self.event.clear()

            try:
                conn = self.conn.get()
                conn.request(
                    method="POST",
                    url=f"/v1/purchases/products/{target[0]}",
                    body='{"expectedCurrency":1,"expectedPrice":%d,"expectedSellerId":%d,"userAssetId":%d}' % (target[1], target[2], target[3]),
                    headers={"Content-Type": "application/json", "Cookie": ".ROBLOSECURITY=%s" % COOKIE, "X-CSRF-TOKEN": xsrf_token}
                )
                resp = conn.getresponse()
                data = json.loads(resp.read())
                print(f"buy result for {target}: {data} (in {round(time.time()-target_updated, 4)}s)")
            except Exception as err:
                print(f"failed to buy {target} due to error: {err} {type(err)}")

class PriceCheckThread(threading.Thread):
    def __init__(self, buy_threads):
        super().__init__()
        self.buy_threads = buy_threads
    
    def run(self):
        global target, target_updated, refresh_count

        while True:
            asset_url, price_threshold = next(target_iter)
            proxy = proxy_pool.get()
            
            try:
                start_time = time.time()
                conn = proxy.get_connection("www.roblox.com")
                conn.putrequest("GET", asset_url, True, True)
                conn.putheader("Host", "www.roblox.com")
                conn.putheader("User-Agent", "Roblox/WinInet")
                conn.endheaders()
                resp = conn.getresponse()
                data = resp.read()
                
                if len(data) < 1000:
                    raise Exception("Weird response")

                reseller = parse_item_page(data.decode("UTF-8"))
                if reseller[1] > 0 and reseller[1] <= price_threshold:
                    with target_lock:
                        if target != reseller and start_time > target_updated:
                            target = reseller
                            target_updated = time.time()
                            for t in buy_threads: t.event.set()
                            print("target set:", target)
                
                refresh_count += 1
                proxy_pool.put(proxy)
            except:
                pass

# start threads
stat_thread = StatUpdater(1)
stat_thread.start()
xsrf_thread = XsrfUpdateThread(XSRF_REFRESH_INTERVAL)
xsrf_thread.start()

buy_threads = [BuyThread() for _ in range(1)]
for t in buy_threads: t.start()

pc_threads = [PriceCheckThread(buy_threads) for _ in range(PRICE_CHECK_THREADS)]
for t in pc_threads: t.start()

print("running 100%!")