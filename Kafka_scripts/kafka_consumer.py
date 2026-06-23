"""
Kafka Consumer — the real-time fraud detection worker.

Continuously listens to the "transactions" topic, and for every
message that arrives, runs it through the SAME XGBoost model used
by the FastAPI service, then prints/logs the prediction.

This demonstrates a streaming architecture: instead of one
request -> one response (like FastAPI), this is a continuous
background worker that processes messages as they arrive,
at whatever pace it can handle.

Usage:
    python kafka_consumer.py
"""

import json
import sys
import os

# Allow importing from the api/ package (preprocess_input, get_risk_level)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import joblib
from kafka import KafkaConsumer
from api.model_utils import preprocess_input, get_risk_level
from api.database import create_table, save_prediction
import time


BOOTSTRAP_SERVERS = ["localhost:9092"]
TOPIC = "transactions"

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "fraud_model_xgb.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "scaler.pkl")


def main():
    print("Loading model and scaler ...")
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print("Model loaded.\n")

    print("Ensuring predictions table exists ...")
    create_table()

    print(f"Connecting to Kafka at {BOOTSTRAP_SERVERS} ...")
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",   # start from the beginning of the topic
        enable_auto_commit=True,
        group_id="fraud-consumer-group"
    )

    print(f"Connected. Listening to topic '{TOPIC}' ...")
    print("Press Ctrl+C to stop.\n")

    fraud_count = 0
    normal_count = 0

    try:
        for message in consumer:
            txn = message.value
            txn_id = txn.pop("txn_id", "?")
            
            start=time.time()
            features, engineered = preprocess_input(txn, scaler)
            probability = float(model.predict_proba(features)[0, 1])
            prediction = "FRAUD" if probability >= 0.5 else "NORMAL"
            risk_level = get_risk_level(probability)
            latency_ms= (time.time()- start)*1000

            # Merge raw V1-V28 with engineered features (Hour, Amount_log, Amount_bin)
            # for full storage, same pattern as the FastAPI /predict endpoint
            full_data = {**txn, **engineered}
 
            save_prediction(
                prediction=prediction,
                probability=probability,
                risk_level=risk_level,
                amount=txn.get("Amount", 0),
                latency_ms=latency_ms,
                raw_data=full_data
            )

            if prediction == "FRAUD":
                fraud_count += 1
                tag = "🚨 FRAUD "
            else:
                normal_count += 1
                tag = "   normal"

            print(f"[txn {txn_id:4}] {tag} prob={probability:.4f} "
                  f"risk={risk_level:6s} amount={txn.get('Amount')}")

    except KeyboardInterrupt:
        print(f"\nStopped. FRAUD={fraud_count}  NORMAL={normal_count}")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()