import requests
import random
import sys
import time

"""
Sends 10 varied transactions to the fraud detection API.
Mix of normal-looking and fraud-looking transactions to populate
the predictions table with realistic data for drift monitoring.
 
Usage:
    python send_test_batch.py
    (or python send_test_batch.py http://13.235.71.227:8000 for AWS)
"""

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/predict"

def make_normal_transaction():
    return {
        "Time": random.uniform(1000, 170000),
        **{f"V{i}": round(random.gauss(0, 0.5), 4) for i in range(1, 29)},
        "Amount": round(random.uniform(1, 150), 2)
    }
 
# Base template for a "fraud-looking" transaction (extreme V values, matching
# the patterns we found in EDA: V11/V4/V2 high positive, V17/V14/V12 very negative)
def make_fraud_transaction():
    txn = {f"V{i}": round(random.gauss(0, 0.5), 4) for i in range(1, 29)}
    txn["V11"] = round(random.uniform(2, 5), 4)
    txn["V4"]  = round(random.uniform(2, 5), 4)
    txn["V2"]  = round(random.uniform(1, 3), 4)
    txn["V17"] = round(random.uniform(-8, -2), 4)
    txn["V14"] = round(random.uniform(-8, -3), 4)
    txn["V12"] = round(random.uniform(-6, -2), 4)
    txn["Time"] = random.uniform(1000, 170000)
    txn["Amount"] = round(random.uniform(1, 200), 2)
    return txn
 
def send(txn):
    try:
        resp = requests.post(ENDPOINT, json=txn, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
 
if __name__ == "__main__":
    print(f"Sending 10 test predictions to {ENDPOINT}\n")
 
    results = []
    for i in range(10):
        # Roughly half normal, half fraud-like
        txn = make_fraud_transaction() if i % 2 == 0 else make_normal_transaction()
        result = send(txn)
        results.append(result)
 
        label = "FRAUD-LIKE" if i % 2 == 0 else "NORMAL-LIKE"
        print(f"[{i+1:2d}] sent {label:12s} -> {result}")
        time.sleep(0.3)  # small delay, be nice to the server
 
    fraud_count = sum(1 for r in results if r.get("prediction") == "FRAUD")
    normal_count = sum(1 for r in results if r.get("prediction") == "NORMAL")
    errors = sum(1 for r in results if "error" in r)
 
    print(f"\nDone. FRAUD={fraud_count}  NORMAL={normal_count}  ERRORS={errors}")