from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from contextlib import asynccontextmanager
import time
import logging
import numpy as np
from model_utils import load_artifacts,preprocess_input,get_risk_level

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
    latency_ms:float

#load model at startup

@asynccontextmanager
async def  lifespan(app:FastAPI):
    #runs when server starts
    logger.info('loading model')
    app.state.model,app.state.scaler,app.state.features=load_artifacts()
    logger.info('model loaded sucessfully')
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
app.get("/Health")
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
        features=preprocess_input(
            data,
            app.state.scaler
        )

        #probability predict
        probability=float(
            app.state.model.predict_proba(features)[0,1]
        )
        prediction="Fraud" if probability>=0.5 else "Normal"
        risk_level=get_risk_level(probability)

        #calculate latency
        latency_ms=(time.time()-start)*1000

        # log every prediction
        logger.info(
           f"prediction={prediction}",
           f" probability={round(probability,4)}",
           f" risk_level={risk_level}",
           f" latency_ms={round(latency_ms,2)}ms"
        )
        return PredictionResponse(
            prediction=prediction,
            probability=round(probability,4),
            risk_level=risk_level,
            latency_ms=round(latency_ms,2)
        )
    except Exception as e:
        logger.error(f"prediction error:{e}")
        raise HTTPException(
            status_code=500,
            detail=f"prediction failed :{str(e)}"
        )
    
#--root--
@app.get("/")
async def root():
    return {
        "message":"fraud Detection API",
        "docs":"/docs",
        "health": "/health"
    }
        





    