import time
import requests

for i in range(100):
    response = requests.get("http://localhost:8000/documents", headers={"x-tenant-id": "1"})
    print(response.json())