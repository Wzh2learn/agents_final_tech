import sys
import traceback
sys.path.insert(0, 'src')

from fastapi.testclient import TestClient
import main

client = TestClient(main.app, raise_server_exceptions=True)

try:
    response = client.get("/chat")
    print(f"Status: {response.status_code}")
    if response.status_code == 500:
        print("Response text:", response.text[:1000])
except Exception as e:
    print("=" * 80)
    print("EXCEPTION CAUGHT:")
    print("=" * 80)
    traceback.print_exc()
    print("=" * 80)
