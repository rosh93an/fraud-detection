from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from contextlib import asynccontextmanager
import time
import logging
import numpy as np
import joblib
from pathlib import Path
from api.database import create_table, save_prediction, get_stats
from api.forensic_agent import generate_forensic_memo, evaluate_jev_decision
from typing import Optional, Any, Dict
from api.model_utils import preprocess_input, get_risk_level, create_explainer, get_top_shap_factors

#setup logging
logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

#request schema
class TransactionRequest(BaseModel):
    Time: float=Field(...,description="seconds elapsed")
    V1: float
    V2:     float
    V3:     float
    V4:     float
    V5:     float
    V6:     float
    V7:     float
    V8:     float
    V9:     float
    V10:    float
    V11:    float
    V12:    float
    V13:    float
    V14:    float
    V15:    float
    V16:    float
    V17:    float
    V18:    float
    V19:    float
    V20:    float
    V21:    float
    V22:    float
    V23:    float
    V24:    float
    V25:    float
    V26:    float
    V27:    float
    V28:    float
    Amount: float = Field(..., gt=0, description="Transaction amount")

#---RESPONSE SCHEMA----
class PredictionResponse(BaseModel):
    prediction: str
    probability: float
    risk_level:str
    top_factors: list[dict] = []
    jev_decision: Optional[Dict[str, Any]] = None
    forensic_memo: Optional[str] = None
    latency_ms:float

#load model at startup

@asynccontextmanager
async def  lifespan(app:FastAPI):
    #runs when server starts
    logger.info('loading model')
    #works both locally and  in docker 
    base_path = Path(__file__).parent.parent

    model_path   = base_path / "models" / "fraud_model_xgb.pkl"
    scaler_path  = base_path / "models" / "scaler.pkl"
    features_path = base_path / "models" / "feature_names.pkl"

    app.state.model    = joblib.load(model_path)
    app.state.scaler   = joblib.load(scaler_path)
    app.state.features = joblib.load(features_path)
    app.state.explainer = create_explainer(app.state.model)
    
    logger.info('model loaded sucessfully')

    #db
    create_table()
    yield
    #runs when server stops
    logger.info('server shutting down')

#--create app--
app=FastAPI(
    title="Fraud detection API",
    description="Real-time credit card fraud detection",
    version="1.0.0",
    lifespan=lifespan
)

#health check
@app.get("/health")
async def health():
    return {
        "status":"healthy",
        "model":"XGBOOST",
        "version":"1.0.0"
    }

#predict Endpoint
@app.post("/predict",response_model=PredictionResponse)
async def predict (request:TransactionRequest):
    start=time.time()
    
    try:
        #convert  request to dict
        data=request.model_dump()
        #preprocess
        features,engineered=preprocess_input(
            data,
            app.state.scaler
        )

        #probability predict
        probability=float(
            app.state.model.predict_proba(features)[0,1]
        )
        prediction="FRAUD" if probability>=0.5 else "NORMAL"
        risk_level=get_risk_level(probability)

        #calculate latency
        latency_ms=(time.time()-start)*1000

        # Merge original V1-V28 with engineered features for storage

        full_data = {**data, **engineered}


        # log every prediction
        logger.info(
           f"prediction={prediction}"
           f" probability={round(probability,4)}"
           f" risk_level={risk_level}"
           f" latency_ms={round(latency_ms,2)}ms"
        )

        #save to post gre sql 
        save_prediction(
            prediction=prediction,
            probability=probability,
            risk_level=risk_level,
            amount=data.get('Amount', 0),
            latency_ms=latency_ms,
            raw_data=full_data
        )
        # Only compute SHAP if high probability or medium risk (to keep latency < 10ms for safe traffic)
        top_factors = []
        forensic_memo = None
        if probability >= 0.5:
            top_factors = get_top_shap_factors(
                features, 
                app.state.explainer, 
                app.state.features, 
                top_n=5
            )
            # Generate AI Forensic Memo for high-risk alerts
            if probability >= 0.70:
                forensic_memo = generate_forensic_memo(
                    txn_id="LIVE",
                    amount=data.get('Amount', 0.0),
                    prediction=prediction,
                    probability=probability,
                    risk_level=risk_level,
                    top_factors=top_factors
                )

        jev_decision = evaluate_jev_decision(
            probability=probability,
            amount=data.get('Amount', 0.0),
            hour=engineered.get('Hour'),
            top_factors=top_factors
        )

        return PredictionResponse(
            prediction=prediction,
            probability=round(probability,4),
            risk_level=risk_level,
            top_factors=top_factors,
            jev_decision=jev_decision,
            forensic_memo=forensic_memo,
            latency_ms=round(latency_ms,2)
        )
    except Exception as e:
        logger.error(f"prediction error:{e}")
        raise HTTPException(
            status_code=500,
            detail=f"prediction failed :{str(e)}"
        )
    
    
#--root--

class InvestigateRequest(BaseModel):
    txn_id: Any = "LIVE"
    amount: float = 0.0
    prediction: str = "FRAUD"
    probability: float = 0.95
    risk_level: str = "HIGH PROBABILITY"
    top_factors: list[dict] = []
    jev_decision: Optional[Dict[str, Any]] = None

class InvestigateResponse(BaseModel):
    txn_id: Any
    jev_decision: Optional[Dict[str, Any]] = None
    forensic_memo: str

@app.post("/investigate", response_model=InvestigateResponse)
async def investigate(req: InvestigateRequest):
    """GenAI Forensic Investigator Agent: Generate an audit-ready compliance memo."""
    memo = generate_forensic_memo(
        txn_id=req.txn_id,
        amount=req.amount,
        prediction=req.prediction,
        probability=req.probability,
        risk_level=req.risk_level,
        top_factors=req.top_factors,
    )
    jev_decision = evaluate_jev_decision(
        probability=req.probability,
        amount=req.amount,
        top_factors=req.top_factors,
    )
    return InvestigateResponse(txn_id=req.txn_id, jev_decision=jev_decision, forensic_memo=memo)

@app.get("/")
async def root():
    return {
        "message":"fraud Detection API - Auto-Deployed via CI/CD ",
        "docs":"/docs",
        "health": "/health"
    }

@app.get("/stats")
async def stats():
    """Get prediction statistics from database"""
    return get_stats()
        





    