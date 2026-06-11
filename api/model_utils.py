import joblib
import numpy as np
import pandas as pd
from pathlib import Path

#paths these works onnly in local we updated it into app.py 
#MODEL_PATH=Path('../models/fraud_model_xgb.pkl')
#SCALER_PATH=Path('../models/scaler.pkl')
#FEATURE_PATH=Path('../models/feature_names.pkl')

#def load_artifacts():
  #  'load model,scaler,features'
  #  model=joblib.load(MODEL_PATH)
  #  scaler=joblib.load(SCALER_PATH)
  #  Feature=joblib.load(FEATURE_PATH)
  #  return model,scaler,Feature


def preprocess_input(data:dict,scaler)-> np.ndarray:
    """
    Apply same preprocessing as training:
    1. Create Hour from Time
    2. Create Amount_log from Amount
    3. Create Amount_bin from Amount
    4. Scale Amount_log and Hour
    5. Drop Time and Amount
    """
    # create dataframe from input
    df = pd.DataFrame([data])
    #feature engineering same as training
    df['Hour'] = (df['Time'] / 3600) % 24
    df['Hour'] = df['Hour'].astype(int)
    df['Amount_log'] = np.log1p(df['Amount'])
    df['Amount_bin'] = pd.cut(
        df['Amount'],
        bins=[0, 10, 50, 200, 500, float('inf')],
        labels=[0, 1, 2, 3, 4],
        include_lowest=True
    ).astype(float)
    # Drop original Time and Amount
    df = df.drop(['Time', 'Amount'], axis=1)
    # Scale
    scale_cols = ['Amount_log', 'Hour']
    df[scale_cols] = scaler.transform(df[scale_cols])
    return df.values

def get_risk_level(probability:float):
    """Convert probability to risk level"""
    if probability>=0.8:
        return 'HIGH PROBABILITY'
    elif probability >= 0.5:
        return "MEDIUM"
    elif probability >= 0.3:
        return "LOW"
    else:
        return "SAFE"

