import time
from datetime import date, timedelta
import os
import random
import string
import threading
import sys
import asyncio
import requests
import html
import nftokengen

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import Select
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode

from browser import get_driver, Proxy_Test
import Emojies
import db 


# ==========================================
# 🚀 LAZY PROXY INITIALIZATION MODULE
# ==========================================
Proxies = []
proxy_locks = {}
proxies_initialized = False
proxy_lock_obj = asyncio.Lock()

async def ensure_proxies():
    """Tests and initializes proxies exclusively in the background only when required."""
    global Proxies, proxy_locks, proxies_initialized
    async with proxy_lock_obj:
        if proxies_initialized:
            return True
        
        # Offload proxy testing to a background thread to keep the bot completely responsive
        tested_proxies = await asyncio.to_thread(Proxy_Test)
        if not tested_proxies:
            print("\n [ FATAL ] No working proxies found!")
            return False
            
        Proxies = tested_proxies
        for i in Proxies:
            port = 1200 + i
            proxy_string = f"socks5://localhost:{port}"
            proxy_locks[proxy_string] = threading.Lock()
            print(f"  [ + ] Added Proxy Lock: {proxy_string}")
            
        proxies_initialized = True
        return True

async def get_any_available_proxy():
    """Tries to lock a random proxy safely."""
    await ensure_proxies()
    
    while True:
        all_proxies = list(proxy_locks.keys())
        if not all_proxies:
            await asyncio.sleep(1)
            continue
            
        random.shuffle(all_proxies)
        
        for proxy in all_proxies:
            lock = proxy_locks[proxy]
            if lock.acquire(blocking=False):
                return proxy
                
        await asyncio.sleep(1)


# ==========================================
# 🛠️ SYNCHRONOUS SELENIUM WRAPPERS
# ==========================================
def wait_for_page_source_text(driver, target_text, timeout=15):
    """Synchronous safe loop to check for dynamic DOM content changes."""
    target_text = target_text.lower()
    start_time = time.time()
    while time.time() - start_time < timeout:
        if target_text in driver.page_source.lower():
            return True
        time.sleep(0.5) 
    return False


def load_cities():
    if not os.path.exists("./Rnames/cities.txt"):
        print(" [-] ERROR: ./Rnames/cities.txt not found. Stopping script...")
        os._exit(1)
    try:
        with open("./Rnames/cities.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if ":" in l]
            return [l.split(":")[0] for l in lines], [l.split(":")[1] for l in lines]
    except Exception as e:
        print(f" [-] ERROR: Failed to read cities.txt - {str(e)}")
        os._exit(1)

def load_users():
    if not os.path.exists("./Rnames/users.txt"):
        print(" [-] ERROR: ./Rnames/users.txt not found. Stopping script...")
        os._exit(1)
    try:
        with open("./Rnames/users.txt", "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if ":" in l]
            return [l.split(":")[0] for l in lines], [l.split(":")[1] for l in lines]
    except Exception as e:
        print(f" [-] ERROR: Failed to read users.txt - {str(e)}")
        os._exit(1)


def CleanLink(text):
    import re
    # Searches for http:// or https:// followed by any non-whitespace characters
    match = re.search(r'(https?://[^\s]+)', text)
    if match:
        return match.group(1)
    return None
