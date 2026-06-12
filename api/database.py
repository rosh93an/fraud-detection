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
    """create production table if does not exist"""
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


def save_prediction(
    prediction:str,
    probability: float,
    risk_level: str,
    amount: float,
    latency_ms: float
    ):

        """ save one prediction to database """
        conn= None
        try:
            conn = get_db_connection()
            cursor= conn.cursor()
            cursor.execute("""
                           insert into predictions
                           (prediction, probability,risk_level,amount,latency_ms)
                           Values(%s,%s,%s,%s,%s)""",
                           (prediction, probability,risk_level,amount,latency_ms))
            conn.commit()
            logger.info(f"prediction saved to db")
        except Exception as e:
             logger.error("database error :{e}")
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

                 

