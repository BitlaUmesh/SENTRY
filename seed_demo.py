import requests
import time
import json

# The API Endpoint
TARGET_URL = "http://127.0.0.1:8001/api/v1/alert"

# 10 Professional Security Attacks to trigger notifications
demo_attacks = [
    {"event_type": "WAF_ALERT", "source_ip": "185.15.56.22", "request_uri": "/api/login", "payload": "admin' OR 1=1 --", "user_agent": "sqlmap/1.5.8"},
    {"event_type": "WAF_ALERT", "source_ip": "45.83.19.110", "request_uri": "/api/system", "payload": "|| cat /etc/shadow", "user_agent": "curl/7.64.1"},
    {"event_type": "WAF_ALERT", "source_ip": "104.28.19.33", "request_uri": "/search", "payload": "<script>alert('XSS')</script>", "user_agent": "Mozilla/5.0"},
    {"event_type": "WAF_ALERT", "source_ip": "45.12.144.10", "request_uri": "/view", "payload": "../../../../etc/passwd", "user_agent": "curl/7.68.0"},
    {"event_type": "AUTH_FAILURE", "source_ip": "172.16.55.99", "request_uri": "/admin", "payload": "Brute force: 150 failed attempts", "user_agent": "Hydra/9.2"},
    {"event_type": "WAF_ALERT", "source_ip": "1.1.1.1", "request_uri": "/api/upload", "payload": "<?php phpinfo(); ?>", "user_agent": "Mozilla/5.0"},
    {"event_type": "WAF_ALERT", "source_ip": "2.2.2.2", "request_uri": "/api/v2/exec", "payload": "rm -rf /", "user_agent": "python-requests/2.25"},
    {"event_type": "WAF_ALERT", "source_ip": "3.3.3.3", "request_uri": "/login", "payload": "admin' UNION SELECT password FROM users", "user_agent": "sqlmap/1.6"},
    {"event_type": "WAF_ALERT", "source_ip": "4.4.4.4", "request_uri": "/api/debug", "payload": "debug=true; env", "user_agent": "Mozilla/5.0"},
    {"event_type": "WAF_ALERT", "source_ip": "5.5.5.5", "request_uri": "/config", "payload": "; cat .env", "user_agent": "curl/7.81"}
]

def fire_seed_demo():
    print("🚀 SENTRY: Starting Live Notification Seeding...")
    print("---------------------------------------------")
    
    for i, attack in enumerate(demo_attacks):
        print(f"[*] Sending Attack {i+1}/10 from {attack['source_ip']}...")
        try:
            # We POST to the API so both the DB and Telegram notifications are triggered
            response = requests.post(TARGET_URL, json=attack, timeout=10)
            if response.status_code == 200:
                print(f"  [SUCCESS] Notification triggered.")
            else:
                print(f"  [FAILED] Server responded with: {response.status_code}")
        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
        
        # Small delay to ensure Telegram doesn't rate-limit you and the UI reflects them one by one
        time.sleep(2)

    print("---------------------------------------------")
    print("✅ SEEDING COMPLETE. You should have 10 notifications on your phone!")

if __name__ == "__main__":
    fire_seed_demo()
