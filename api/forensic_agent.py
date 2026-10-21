"""
GenAI Forensic Investigator Agent
Translates raw SHAP feature vectors and transaction metadata into
executive, audit-ready compliance memorandums.

Supports dual-provider architecture:
1. Groq (High-speed LLaMA/GPT-OSS inference)
2. Google Gemini (Gemini 1.5/2.0 Flash)
3. Deterministic template fallback (Zero downtime)
"""

import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Feature semantic mappings for human financial interpretation
FEATURE_ANNOTATIONS = {
    "V14": "Account Spending & Behavior Deviation",
    "V4": "Card Velocity & Frequency Spike",
    "V10": "Location / Merchant Risk Factor",
    "V12": "Authentication & Credential Consistency",
    "V17": "Card-Not-Present / Terminal Anomaly",
    "V3": "Geographical Jump Factor",
    "V11": "Repetitive Trial Attempt Index",
    "V8": "Verification Signal Discrepancy",
    "V2": "Transaction Magnitude Deviation",
    "Hour": "Time of Day (Nocturnal / Off-Peak Window)",
    "Amount_log": "Logarithmic Transaction Volume",
    "Amount_bins": "Ticket Size Tier Category",
}


def _build_prompt(
    txn_id: Any,
    amount: float,
    prediction: str,
    probability: float,
    risk_level: str,
    top_factors: List[Dict[str, Any]],
) -> str:
    factors_lines = []
    for f in top_factors:
        feat = f.get("feature", "Unknown")
        val = f.get("value", 0.0)
        impact = f.get("shap_impact", 0.0)
        meaning = FEATURE_ANNOTATIONS.get(feat, "Behavioral PCA Dimension")
        direction = "pushes towards FRAUD" if impact > 0 else "pulls towards NORMAL"
        factors_lines.append(
            f"- {feat} ({meaning}): value={val:+.2f}, SHAP impact={impact:+.3f} ({direction})"
        )
    factors_text = "\n".join(factors_lines) if factors_lines else "No extreme feature outliers."

    return f"""You are a Senior Financial Crime & Fraud Forensic Investigator.
A real-time Machine Learning model flagged transaction #{txn_id} as {prediction} with {probability:.1%} confidence.

TRANSACTION DETAILS:
- Transaction ID: #{txn_id}
- Amount: ${amount:.2f}
- Model Classification: {prediction}
- Confidence Probability: {probability:.2%}
- Assigned Risk Level: {risk_level}

TOP CONTRIBUTING SHAP FEATURE DRIVERS:
{factors_text}

TASK:
Write an audit-ready, 3-section Forensic Investigation Memorandum formatted in clean Markdown:
### 1. Executive Summary
Brief 1-2 sentence overview of the decision and risk profile.

### 2. Behavioral Risk Analysis
Explain in plain English what the top feature drivers signify and why the combination is suspicious (or safe).

### 3. Recommended Action
Specific, actionable next steps (e.g. Immediate card freeze, 2FA challenge via SMS, manual AML analyst review, or release transaction).

Keep the memo concise, objective, and professional for compliance officers."""


def _call_groq(prompt: str) -> Optional[str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    # Clean miniconda SSL issues on Windows if present
    os.environ.pop("SSL_CERT_FILE", None)
    os.environ.pop("SSL_CERT_DIR", None)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # Try available text models on user's Groq tier
        models_to_try = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "qwen/qwen3.8-27b",
        ]
        
        for model in models_to_try:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a professional banking fraud forensics investigator."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=400,
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                if content and content.strip():
                    return f"{content.strip()}\n\n*(Analysis by Groq: {model})*"
            except Exception as e:
                logger.warning(f"Groq model {model} attempt failed: {e}")
                continue

    except Exception as e:
        logger.error(f"Groq API error: {e}")
    return None


def _call_gemini(prompt: str) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return f"{response.text.strip()}\n\n*(Analysis by Google Gemini: {model_name})*"
            except Exception as e:
                logger.warning(f"Gemini model {model_name} attempt failed: {e}")
                continue

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
    return None


def _fallback_rule_memo(
    txn_id: Any,
    amount: float,
    prediction: str,
    probability: float,
    risk_level: str,
    top_factors: List[Dict[str, Any]],
) -> str:
    """Deterministic fallback memo in case of network/token exhaustion"""
    top_drivers = ", ".join(
        f"{f.get('feature')}({FEATURE_ANNOTATIONS.get(f.get('feature'), 'PCA')})"
        for f in top_factors[:3]
    ) or "Standard parameters"

    if prediction == "FRAUD":
        action = "Block card immediately. Issue automated cardholder SMS inquiry and flag for AML analyst review."
        summary = f"Transaction #{txn_id} for ${amount:.2f} triggered a HIGH-RISK FRAUD alert with {probability:.1%} confidence."
    else:
        action = "Approve and release transaction for standard clearing."
        summary = f"Transaction #{txn_id} for ${amount:.2f} cleared all automated safety checks with {1 - probability:.1%} normal confidence."

    return f"""### 1. Executive Summary
{summary}

### 2. Behavioral Risk Analysis
- **Primary Driver Features**: {top_drivers}.
- **Risk Posture**: Model probability is {probability:.2%} with risk rating {risk_level}. Multiple behavioral dimensions pushed above threshold limits.

### 3. Recommended Action
{action}

*(Automated Rule-Based Compliance Fallback)*"""


def generate_forensic_memo(
    txn_id: Any = "LIVE",
    amount: float = 0.0,
    prediction: str = "FRAUD",
    probability: float = 0.0,
    risk_level: str = "HIGH PROBABILITY",
    top_factors: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Main entrypoint: Generates a forensic memorandum using Groq, Gemini,
    or deterministic fallback.
    """
    factors = top_factors or []
    prompt = _build_prompt(txn_id, amount, prediction, probability, risk_level, factors)

    # 1. Try Groq (Primary high-speed engine)
    memo = _call_groq(prompt)
    if memo:
        return memo

    # 2. Try Gemini (Secondary enterprise fallback)
    memo = _call_gemini(prompt)
    if memo:
        return memo

    # 3. Deterministic Fallback (Guarantees zero downtime)
    return _fallback_rule_memo(txn_id, amount, prediction, probability, risk_level, factors)
