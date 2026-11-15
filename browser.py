import random
import threading
import undetected_chromedriver as uc
import requests
import os 

def test_wireguard_config(config_path, i):
    # 1. Extract port directly from the file
    proxy_port = 1200 + i
    
    if not proxy_port:
        print(f"[-] {config_path}: Could not find file or BindAddress port. Skipping.")
        return False, None
            
    proxy_url = f"socks5h://127.0.0.1:{proxy_port}"
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    is_working = False
    proxy_ip = None
    
    try:
        # 3. Test the connection with a 10-second timeout
        response = requests.get("https://api.ipify.org", proxies=proxies, timeout=10)
        
        if response.status_code == 200:
            is_working = True
            proxy_ip = response.text.strip()
            print(f"[+] {config_path} is WORKING. ✅ {proxy_ip}")
        else:
            print(f"[-] {config_path} failed with HTTP status: ⛔ {response.status_code}")
            
    except requests.exceptions.RequestException:
        print(f"[-] {config_path} is DEAD ⛔.")
    
        
    return is_working, proxy_ip

def Proxy_Test():
    
    print("\n > Checking Proxies...\n")

    Proxies = []
    for i in range(8):
        config_file = f"/Path_To_wireguard_config/{i}.conf"
        working, ip = test_wireguard_config(config_file, i)

        if working : 
            Proxies.append(i)
        print("-" * 24)
    return Proxies


import platform
import random
import threading
import undetected_chromedriver as uc
import requests

# Global lock and virtual display reference for Linux SSH servers
driver_creation_lock = threading.Lock()
virtual_display = None

def ensure_virtual_display():
    """Starts an in-memory 1920x1080 monitor on headless Linux SSH servers."""
    global virtual_display
    if platform.system() == "Linux" and virtual_display is None:
        from pyvirtualdisplay import Display
        virtual_display = Display(visible=0, size=(1920, 1080), color_depth=24)
        virtual_display.start()
        print("  [ + ] Started Xvfb virtual display (1920x1080x24) for headed Chrome on Linux.")

def get_driver(proxy=None, hide_on_windows=True, block_images=False):
    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'

    # Minimal stock flags + prevent background throttling
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--lang=en-US')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')

    # Required flags when running inside Linux SSH / root environments
    if platform.system() == "Linux":
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--enable-webgl')
        options.add_argument('--ignore-gpu-blocklist')
    elif hide_on_windows:
        # Hides the headed window off-screen on Windows without using headless mode
        options.add_argument('--window-position=-2400,-2400')

    if proxy:
        proxy_url = proxy if isinstance(proxy, str) else "socks5://127.0.0.1:1200"
        options.add_argument(f"--proxy-server={proxy_url}")

    viewports = [
        (1920, 1080),
        (1536, 864),
        (1440, 900),
        (1366, 768),
        (1600, 900),
    ]
    width, height = random.choice(viewports)
    options.add_argument(f"--window-size={width},{height}")

    with driver_creation_lock:
        # Automatically starts Xvfb if on Linux
        ensure_virtual_display()

        driver = uc.Chrome(
            options=options,
            # version_main=156,
            headless=False,  # ALWAYS False: runs headed inside Xvfb on Linux and natively on Windows
            use_subprocess=True,
        )

    driver.set_window_size(width, height)

    # Only block heavy raster images if requested; never block .woff/.woff2/.svg on SheerID
    if block_images:
        driver.execute_cdp_cmd('Network.enable', {})
        driver.execute_cdp_cmd('Network.setBlockedURLs', {
            "urls": ["*.jpg", "*.jpeg", "*.webp"]
        })

    return driver
