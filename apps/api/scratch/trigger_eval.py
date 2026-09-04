import requests
import time

print("Triggering evaluation...")
res = requests.post("http://localhost:8000/api/v1/evaluation/run")
print(res.json())

for _ in range(30):
    time.sleep(2)
    try:
        latest = requests.get("http://localhost:8000/api/v1/evaluation/latest").json()
        print("Status:", latest.get("status"))
        if latest.get("status") != "RUNNING":
            print("Finished!")
            print("Metrics:", latest.get("metrics"))
            break
    except Exception as e:
        print("Error checking status:", e)
