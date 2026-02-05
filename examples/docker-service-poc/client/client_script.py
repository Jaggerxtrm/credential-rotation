import requests
import time

URL = "http://qwen-service:8000/generate"
time.sleep(5)

for p in ["Test 1", "Test 2"]:
    print(f"Sending: {p}")
    try:
        r = requests.post(URL, json={"prompt": p}, timeout=30)
        print(f"Status: {r.status_code}, Resp: {r.text[:50]}")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(1)
