import urllib.request
import urllib.error
import json
import time

unique = str(int(time.time()))

data = json.dumps({
    "name": "Debug Test2",
    "email": f"debug2_{unique}@test.com",
    "password": "pass123",
    "phone": f"0877{unique[-6:]}",
    "role": "petani",
    "location": "P"
}).encode('utf-8')

print(f"Testing with email: debug2_{unique}@test.com")

req = urllib.request.Request(
    "https://xai-rag-production.up.railway.app/api/v1/auth/register",
    data=data,
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        result = response.read().decode()
        print(f"SUCCESS: {result}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP ERROR {e.code}")
    print(f"FULL BODY: {body}")
    print(f"FULL BODY LENGTH: {len(body)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
