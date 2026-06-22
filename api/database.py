import os
import psycopg2
from datetime import datetime
import logging

logger=logging.getLogger(__name__)

def get_db_connection():
    database_url=os.getenv(
        "DATABASE URL","postgresql://frauduser:fraudpass@db:5432/frauddb"
    )
    return psycopg2.connect(database_url)

def create_table():
    """Create predictions table with full feature columns"""
    #"""create production table if does not exist"""
    conn=None
    try:
        conn= get_db_connection()
        cursor=conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id          SERIAL PRIMARY KEY,
                prediction  VARCHAR(10) NOT NULL,
                probability FLOAT NOT NULL,
                risk_level  VARCHAR(20) NOT NULL,
                amount      FLOAT,
                latency_ms  FLOAT,
                v1 FLOAT, v2 FLOAT, v3 FLOAT, v4 FLOAT, v5 FLOAT,
                v6 FLOAT, v7 FLOAT, v8 FLOAT, v9 FLOAT, v10 FLOAT,
                v11 FLOAT, v12 FLOAT, v13 FLOAT, v14 FLOAT, v15 FLOAT,
                v16 FLOAT, v17 FLOAT, v18 FLOAT, v19 FLOAT, v20 FLOAT,
                v21 FLOAT, v22 FLOAT, v23 FLOAT, v24 FLOAT, v25 FLOAT,
                v26 FLOAT, v27 FLOAT, v28 FLOAT,
                hour FLOAT,
                amount_log FLOAT,
                amount_bin FLOAT,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        conn.commit()
        logger.info("prediction table ready")
    except Exception as e:
        logger.error(f"tablecreated error:{e}")
    finally:
        if conn:
            conn.close()


def save_prediction(prediction, probability, risk_level, amount, latency_ms, raw_data=None):
    """Save prediction + full feature set to database"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Default all V-features to None if raw_data not provided
        v = {f"v{i}": (raw_data.get(f"V{i}") if raw_data else None) for i in range(1, 29)}
        hour = raw_data.get("Hour") if raw_data else None
        amount_log = raw_data.get("Amount_log") if raw_data else None
        amount_bin = raw_data.get("Amount_bin") if raw_data else None

        cursor.execute("""
            INSERT INTO predictions
            (prediction, probability, risk_level, amount, latency_ms,
             v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,
             v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,
             v21,v22,v23,v24,v25,v26,v27,v28,
             hour, amount_log, amount_bin)
            VALUES (%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s)
        """, (
            prediction, probability, risk_level, amount, latency_ms,
            v['v1'],v['v2'],v['v3'],v['v4'],v['v5'],v['v6'],v['v7'],v['v8'],v['v9'],v['v10'],
            v['v11'],v['v12'],v['v13'],v['v14'],v['v15'],v['v16'],v['v17'],v['v18'],v['v19'],v['v20'],
            v['v21'],v['v22'],v['v23'],v['v24'],v['v25'],v['v26'],v['v27'],v['v28'],
            hour, amount_log, amount_bin
        ))
        conn.commit()
        logger.info("Prediction saved to DB ✅")
    except Exception as e:
        logger.error(f"DB save error: {e}")
    finally:
        if conn:
            conn.close()

def get_stats():
    """Get prediction statistics using modern PostgreSQL FILTER syntax"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Using the clean Postgres FILTER syntax
        cursor.execute("""
            SELECT 
                COUNT(*) as total, 
                COUNT(*) FILTER (WHERE prediction = 'FRAUD') as fraud_count, 
                COUNT(*) FILTER (WHERE prediction = 'NORMAL') as normal_count, 
                AVG(probability) as avg_probability, 
                AVG(latency_ms) as avg_latency 
            FROM predictions
        """)
        
        row = cursor.fetchone()
        
        return {
            "total_predictions": row[0],
            "fraud_count": row[1] if row[1] is not None else 0,
            "normal_count": row[2] if row[2] is not None else 0,
            "avg_probability": round(row[3], 4) if row[3] else 0,
            "avg_latency_ms": round(row[4], 2) if row[4] else 0
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {}
    finally:
        if conn:
            cursor.close()  # Memory safety fix
            conn.close()

                 

