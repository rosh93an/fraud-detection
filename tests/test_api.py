import numpy as np
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api.model_utils import preprocess_input, get_risk_level

def test_get_risk_level_high():
    assert get_risk_level(0.9)=="HIGH PROBABILITY"
def test_get_risk_level_medium():
    assert get_risk_level(0.6)=="MEDIUM"
def test_get_risk_level_LOW():
    assert get_risk_level(0.35)=="LOW"
def test_get_risk_level_SAFE():
    assert get_risk_level(0.1)=="SAFE"


#TEST2
def test_preprocess_output_shape(tmp_path):
    import joblib
    from sklearn.preprocessing import StandardScaler

    #create dummy scaler
    scaler=StandardScaler()
    dummy=pd.DataFrame({
        'Amount_log': [1.0,2.0,3.0],
        'Hour' : [1.0,2.0,3.0]
    })
    scaler.fit(dummy)

    #sample transaction
    transaction = {
        'Time': 406.0,
        'V1': -2.31, 'V2': 1.95, 'V3': -1.60,
        'V4': 3.99,  'V5': -0.52,'V6': -1.42,
        'V7': -2.53, 'V8': 1.39, 'V9': -2.77,
        'V10': -2.77,'V11': 3.20,'V12': -2.89,
        'V13': -0.59,'V14': -4.28,'V15': 0.38,
        'V16': -1.14,'V17': -2.83,'V18': -0.01,
        'V19': 0.41, 'V20': 0.12,'V21': 0.51,
        'V22': 0.49, 'V23': -0.14,'V24': 0.63,
        'V25': 0.06, 'V26': -0.17,'V27': -0.12,
        'V28': -0.03,'Amount': 149.62
    }
    result = preprocess_input(transaction, scaler)
    

    # Should return 2D array
    assert result.ndim == 2
    # Should have 31 features
    assert result.shape[1] == 31
    print(f"Output shape: {result.shape} ✅")

    

def test_hour_feature():
    import joblib
    from sklearn.preprocessing import StandardScaler

    #create dummy scaler
    scaler=StandardScaler()
    dummy=pd.DataFrame({
        'Amount_log': [1.0],
        'Hour' : [1.0]
    })
    scaler.fit(dummy)

    # Sample transaction
    transaction = {
        'Time': 3600.0,  # exactly 1 hour
        'V1': 0.0, 'V2': 0.0, 'V3': 0.0,
        'V4': 0.0, 'V5': 0.0, 'V6': 0.0,
        'V7': 0.0, 'V8': 0.0, 'V9': 0.0,
        'V10': 0.0,'V11': 0.0,'V12': 0.0,
        'V13': 0.0,'V14': 0.0,'V15': 0.0,
        'V16': 0.0,'V17': 0.0,'V18': 0.0,
        'V19': 0.0,'V20': 0.0,'V21': 0.0,
        'V22': 0.0,'V23': 0.0,'V24': 0.0,
        'V25': 0.0,'V26': 0.0,'V27': 0.0,
        'V28': 0.0,'Amount': 10.0
    }

    result = preprocess_input(transaction, scaler)
    assert result is not None
    print("Hour feature test passed ✅")


