"""
Kafka Producer — simulates a stream of incoming transactions.

In real life, this role would be played by a payment gateway,
a bank's core transaction system, or a POS network — anything
generating live transactions that need fraud-checking.

Here, we simulate it: every couple of seconds, generate a random
transaction (mix of normal-looking and fraud-looking) and publish
it to the Kafka topic "transactions".

Usage:
    python kafka_producer.py
"""

import json
import random
import time
from kafka import KafkaProducer

BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "transactions"


def make_normal_transaction():
    return {
        "Time": random.uniform(1000, 170000),
        **{f"V{i}": round(random.gauss(0, 0.5), 4) for i in range(1, 29)},
        "Amount": round(random.uniform(1, 150), 2)
    }


def make_fraud_transaction():
    txn = {f"V{i}": round(random.gauss(0, 0.5), 4) for i in range(1, 29)}
    txn["V11"] = round(random.uniform(2, 5), 4)
    txn["V4"] = round(random.uniform(2, 5), 4)
    txn["V2"] = round(random.uniform(1, 3), 4)
    txn["V17"] = round(random.uniform(-8, -2), 4)
    txn["V14"] = round(random.uniform(-8, -3), 4)
    txn["V12"] = round(random.uniform(-6, -2), 4)
    txn["Time"] = random.uniform(1000, 170000)
    txn["Amount"] = round(random.uniform(1, 200), 2)
    return txn


def main():
    print(f"Connecting to Kafka at {BOOTSTRAP_SERVERS} ...")

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    print(f"Connected. Streaming transactions to topic '{TOPIC}' ...")
    print("Press Ctrl+C to stop.\n")

    count = 0
    try:
        while True:
            is_fraud_like = random.random() < 0.3  # ~30% fraud-like
            txn = make_fraud_transaction() if is_fraud_like else make_normal_transaction()

            # Attach a simple transaction id for tracking
            txn["txn_id"] = count

            producer.send(TOPIC, value=txn)
            producer.flush()

            label = "FRAUD-LIKE" if is_fraud_like else "NORMAL-LIKE"
            print(f"[{count:4d}] sent {label:12s} amount={txn['Amount']}")

            count += 1
            time.sleep(random.uniform(0.5, 2.0))  # simulate irregular arrival

    except KeyboardInterrupt:
        print(f"\nStopped. Sent {count} transactions total.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()