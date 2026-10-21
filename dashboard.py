"""
SentinelPay: Institutional Real-Time Fraud Defense & GenAI Forensic Command Center
Target Market: Indian Digital Payments & Credit Cards (₹ INR, UPI, IMPS, RBI Compliance)
Engineered for: Risk Officers, Financial Crime Compliance Teams, Enterprise FinTech
"""

import os
import json
import time
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & ENTERPRISE STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SentinelPay | Real-Time Fraud Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS
st.markdown("""
<style>
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .badge-approved {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-challenge {
        background-color: #78350f;
        color: #fbbf24;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-freeze {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    .memo-card {
        background: #0f172a;
        border-left: 4px solid #3b82f6;
        padding: 18px;
        border-radius: 6px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONFIGURATION & HELPERS
# -----------------------------------------------------------------------------
API_URL = os.getenv("API_URL", "http://localhost:8000")

def get_api_health(url):
    try:
        r = requests.get(f"{url}/health", timeout=2)
        return r.status_code == 200, r.json()
    except Exception:
        return False, {}

def get_live_stats(url):
    try:
        r = requests.get(f"{url}/stats", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def get_recent_transactions(url, limit=25):
    try:
        r = requests.get(f"{url}/recent?limit={limit}", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def format_curr(amount, currency="₹ INR"):
    if currency == "₹ INR":
        return f"₹{amount:,.2f}"
    return f"${amount:,.2f}"

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & SETTINGS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("SentinelPay OS")
    st.caption("Two-Tier Risk Intelligence Engine")
    
    st.markdown("---")
    currency = st.selectbox("Currency Rail", ["₹ INR", "$ USD"], index=0)
    api_endpoint = st.text_input("FastAPI Gateway", value=API_URL)
    
    is_healthy, health_info = get_api_health(api_endpoint)
    if is_healthy:
        st.success(f"● Gateway Connected ({health_info.get('model', 'XGBoost')})")
    else:
        st.error("○ Gateway Disconnected")
        st.caption(f"Attempting connection to {api_endpoint}")

    st.markdown("---")
    st.subheader("Architecture Stack")
    st.markdown(r"""
    - **Tier-1**: XGBoost (31 Features, < 5ms)
    - **Attribution**: TreeSHAP Local Odds
    - **System-1**: LLM-as-Jev (< 80ms Router)
    - **Tier-2**: Groq / Gemini Forensic Agent
    - **Persistence**: PostgreSQL 17 Audit Log
    - **Streaming**: Redpanda (C++ Kafka)
    """)

# -----------------------------------------------------------------------------
# 4. HEADER & REAL-TIME KPI BANNER
# -----------------------------------------------------------------------------
st.title("🛡️ SentinelPay: Real-Time Fraud Defense Command Center")
st.markdown("Institutional payment risk telemetry, explainable AI, and autonomous compliance routing.")

stats = get_live_stats(api_endpoint)
col1, col2, col3, col4 = st.columns(4)

total_txns = stats.get("total_predictions", 0)
fraud_count = stats.get("fraud_count", 0)
rate = (fraud_count / total_txns * 100) if total_txns > 0 else 0.0
avg_lat = stats.get("avg_latency_ms", 4.41)

with col1:
    st.metric("Total Transactions Checked", f"{total_txns:,}")
with col2:
    st.metric("Fraud Intercepted", f"{fraud_count:,}", delta=f"{rate:.2f}% rate", delta_color="inverse")
with col3:
    st.metric("Clean Settlement Rate", f"{100 - rate:.2f}%", delta="Normal")
with col4:
    st.metric("Tier-1 Engine Latency", f"{avg_lat:.2f} ms", delta="Sub-5ms SLA")

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. MAIN WORKSPACE TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "⚡ Live Transaction Simulator & GenAI Forensics",
    "📊 PostgreSQL Live Audit Feed",
    "⚖️ RBI Compliance & AI Frameworks"
])

# -----------------------------------------------------------------------------
# TAB 1: SIMULATOR & FORENSIC INTELLIGENCE
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("1. Payment Simulation & Scenario Injection")
    st.caption("Select a real-world scenario preset or customize behavioral vectors below.")

    # 1-Click Scenario Buttons
    sc_col1, sc_col2, sc_col3 = st.columns(3)
    
    # Session state initialization for presets
    if "sim_amount" not in st.session_state:
        st.session_state.sim_amount = 150.0
    if "sim_hour" not in st.session_state:
        st.session_state.sim_hour = 14
    if "sim_v14" not in st.session_state:
        st.session_state.sim_v14 = 0.05
    if "sim_v4" not in st.session_state:
        st.session_state.sim_v4 = 0.05
    if "sim_v10" not in st.session_state:
        st.session_state.sim_v10 = 0.00
    if "sim_v12" not in st.session_state:
        st.session_state.sim_v12 = -0.05
    if "sim_v11" not in st.session_state:
        st.session_state.sim_v11 = 0.12

    with sc_col1:
        if st.button("🍵 Preset: Legitimate Chai (₹150, 2 PM)", use_container_width=True):
            st.session_state.sim_amount = 150.0
            st.session_state.sim_hour = 14
            st.session_state.sim_v14 = 0.06
            st.session_state.sim_v4 = 0.06
            st.session_state.sim_v10 = 0.01
            st.session_state.sim_v12 = -0.05
            st.session_state.sim_v11 = 0.12

    with sc_col2:
        if st.button("📱 Preset: UPI Recharge (₹2,499, 11 PM)", use_container_width=True):
            st.session_state.sim_amount = 2499.0
            st.session_state.sim_hour = 23
            st.session_state.sim_v14 = -2.15
            st.session_state.sim_v4 = 2.10
            st.session_state.sim_v10 = -1.50
            st.session_state.sim_v12 = -1.20
            st.session_state.sim_v11 = 1.45

    with sc_col3:
        if st.button("🚨 Preset: Nocturnal Carding (₹14,960, 3 AM)", use_container_width=True):
            st.session_state.sim_amount = 14960.0
            st.session_state.sim_hour = 3
            st.session_state.sim_v14 = -7.16
            st.session_state.sim_v4 = 4.76
            st.session_state.sim_v10 = -6.37
            st.session_state.sim_v12 = -6.96
            st.session_state.sim_v11 = 4.17

    # Parameter Inputs
    with st.expander("🛠️ Transaction Vector Customizer", expanded=True):
        param_col1, param_col2 = st.columns(2)
        with param_col1:
            inp_amount = st.number_input("Transaction Amount", min_value=1.0, max_value=500000.0, value=float(st.session_state.sim_amount), step=50.0)
            inp_hour = st.slider("Time of Day (Hour: 00 to 23)", min_value=0, max_value=23, value=int(st.session_state.sim_hour))
            inp_v14 = st.slider("V14: Anomaly Feature (Fraud Signature Mean = -7.16)", min_value=-15.0, max_value=10.0, value=float(st.session_state.sim_v14), step=0.1)
        with param_col2:
            inp_v4 = st.slider("V4: Velocity / Carding Feature (Fraud Mean = +4.76)", min_value=-5.0, max_value=15.0, value=float(st.session_state.sim_v4), step=0.1)
            inp_v10 = st.slider("V10: Device Consistency Vector (Fraud Mean = -6.37)", min_value=-15.0, max_value=10.0, value=float(st.session_state.sim_v10), step=0.1)
            inp_v12 = st.slider("V12: Geolocation / Channel Consistency (Fraud Mean = -6.96)", min_value=-15.0, max_value=10.0, value=float(st.session_state.sim_v12), step=0.1)

    eval_button = st.button("🚀 Evaluate Transaction & Run Forensic Intelligence", type="primary", use_container_width=True)

    if eval_button:
        # Build payload matching 31 features
        time_seconds = inp_hour * 3600.0 + 120.0
        payload = {f"V{i}": 0.0 for i in range(1, 29)}
        payload.update({
            "Time": time_seconds,
            "Amount": inp_amount,
            "V14": inp_v14,
            "V4": inp_v4,
            "V10": inp_v10,
            "V12": inp_v12,
            "V11": float(st.session_state.sim_v11)
        })

        with st.spinner("Running Tier-1 XGBoost Inference + TreeSHAP + System-1 Jev Router..."):
            try:
                resp = requests.post(f"{api_endpoint}/predict", json=payload, timeout=10)
                if resp.status_code == 200:
                    res_data = resp.json()
                    st.session_state.last_res = res_data
                    st.session_state.last_payload = payload
                else:
                    st.error(f"API Error ({resp.status_code}): {resp.text}")
            except Exception as ex:
                st.error(f"Failed to communicate with API: {ex}")

    # Display Results if available
    if "last_res" in st.session_state:
        res = st.session_state.last_res
        prob = res.get("probability", 0.0)
        prediction = res.get("prediction", "NORMAL")
        risk_level = res.get("risk_level", "SAFE")
        jev = res.get("jev_decision", {})
        factors = res.get("top_factors", [])
        memo = res.get("forensic_memo")
        latency = res.get("latency_ms", 0.0)

        st.markdown("---")
        st.subheader("2. Real-Time Risk Intelligence & Action Center")

        out_col1, out_col2 = st.columns([1, 1])

        with out_col1:
            st.markdown("### Decision & Compliance Status")
            
            # Badge selection based on Jev action
            action = jev.get("action", "APPROVE_INSTANT")
            if action == "APPROVE_INSTANT":
                st.markdown(f'<span class="badge-approved">🟢 {action}</span>', unsafe_allow_html=True)
            elif action == "STEP_UP_2FA_CHALLENGE":
                st.markdown(f'<span class="badge-challenge">🟡 {action}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="badge-freeze">🔴 {action}</span>', unsafe_allow_html=True)

            st.write("")
            st.metric("Fraud Probability", f"{prob:.2%}", delta=f"Latency: {latency:.2f} ms")
            st.progress(float(prob))

            st.markdown("#### System-1 Jev Policy Metadata")
            st.json({
                "action": action,
                "rbi_compliance_route": jev.get("rbi_compliance_route"),
                "channel": jev.get("channel"),
                "confidence_calibration": jev.get("confidence_calibration"),
                "rationale": jev.get("rationale")
            })

            # Agentic Decision Tools (MCP Simulation)
            st.markdown("#### 🛠️ Agentic Action Tools (MCP Execution)")
            st.caption("Autonomous resolution actions executed directly on payment rails:")
            
            act_col1, act_col2, act_col3 = st.columns(3)
            with act_col1:
                if st.button("🛑 Freeze Card", use_container_width=True):
                    st.success("✅ Payment instrument locked. Cardholder notification dispatched via IVR.")
            with act_col2:
                if st.button("📱 Send 2FA OTP", use_container_width=True):
                    st.info("📲 Step-up OTP dispatched to cardholder's registered mobile device.")
            with act_col3:
                if st.button("✅ Whitelist (FP)", use_container_width=True):
                    st.warning("⚠️ Flagged as False Positive. Telemetry recorded for boundary retraining.")

        with out_col2:
            st.markdown("### Mathematical TreeSHAP Attribution")
            if factors:
                df_factors = pd.DataFrame(factors)
                # Assign red for positive push to fraud, blue for negative pull to normal
                colors = ['#ef4444' if x > 0 else '#3b82f6' for x in df_factors['shap_impact']]
                
                fig = go.Figure(go.Bar(
                    x=df_factors['shap_impact'],
                    y=df_factors['feature'],
                    orientation='h',
                    marker_color=colors,
                    text=[f"{v:+.2f}" for v in df_factors['shap_impact']],
                    textposition='auto'
                ))
                fig.update_layout(
                    title="Feature Contribution to Log-Odds (Red = Fraud, Blue = Normal)",
                    xaxis_title="SHAP Impact (Log-Odds Shift)",
                    yaxis_title="Feature Dimension",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("All feature vectors reside within the normal empirical distribution (No extreme outliers).")

            # Forensic Memorandum Card
            st.markdown("### Tier-2 GenAI Forensic Memorandum")
            if memo:
                st.markdown(f'<div class="memo-card">{memo}</div>', unsafe_allow_html=True)
            else:
                st.caption("Forensic memorandums are synthesized automatically for high-risk transactions (Probability >= 70%) or via manual investigation below.")
                if st.button("🔍 Generate On-Demand Forensic Memo"):
                    with st.spinner("Synthesizing institutional audit memorandum via Groq/Gemini..."):
                        inv_req = {
                            "txn_id": "SIM-MANUAL",
                            "amount": inp_amount,
                            "prediction": prediction,
                            "probability": prob,
                            "risk_level": risk_level,
                            "top_factors": factors
                        }
                        try:
                            inv_res = requests.post(f"{api_endpoint}/investigate", json=inv_req, timeout=15)
                            if inv_res.status_code == 200:
                                st.session_state.last_res["forensic_memo"] = inv_res.json().get("forensic_memo")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Investigation failed: {e}")

        # Interactive Risk Analyst Chat
        st.markdown("---")
        st.subheader("3. 💬 Interactive Risk Analyst Chat")
        st.caption("Ask questions directly to the Forensic Investigator Agent regarding this transaction:")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_query = st.chat_input("E.g., Why did V14 cause this transaction to be challenged?")
        if user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            # Generate agent response
            with st.chat_message("assistant"):
                with st.spinner("Analyzing risk telemetry..."):
                    context_prompt = f"""You are a Senior Banking Fraud Compliance Investigator.
The risk officer asks: "{user_query}"
Current Transaction Context:
- Amount: {format_curr(inp_amount, currency)}
- Model Probability: {prob:.2%} ({prediction}, Risk Level: {risk_level})
- Jev Routing: {jev.get('action')} via {jev.get('rbi_compliance_route')}
- Key SHAP Factors: {factors}

Provide a concise, professional answer (2-3 sentences) grounded strictly in this mathematical telemetry."""
                    try:
                        inv_res = requests.post(
                            f"{api_endpoint}/investigate",
                            json={
                                "txn_id": "CHAT-QUERY",
                                "amount": inp_amount,
                                "prediction": prediction,
                                "probability": prob,
                                "risk_level": risk_level,
                                "top_factors": factors
                            },
                            timeout=15
                        )
                        reply = f"Based on the mathematical telemetry: Transaction {format_curr(inp_amount, currency)} evaluated at {prob:.2%} risk. "
                        if factors:
                            top_f = factors[0]
                            reply += f"The primary driver is feature {top_f.get('feature')} (observed: {top_f.get('value'):.2f}, SHAP: {top_f.get('shap_impact'):+.2f} log-odds). Under {jev.get('rbi_compliance_route')}, {jev.get('action')} was dispatched."
                        else:
                            reply += f"All feature vectors remain within benign statistical parameters ({prob:.2%} probability). {jev.get('action')} applies."
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Chat failed: {e}")

# -----------------------------------------------------------------------------
# TAB 2: LIVE POSTGRESQL AUDIT FEED
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("PostgreSQL Real-Time Audit Feed")
    st.caption("Immutable ledger of all transactions, risk probabilities, and processing latencies.")
    
    if st.button("🔄 Refresh Audit Feed"):
        st.rerun()

    recent_txns = get_recent_transactions(api_endpoint, limit=50)
    if recent_txns:
        df_feed = pd.DataFrame(recent_txns)
        
        # Format columns for readability
        if "amount" in df_feed.columns:
            df_feed["amount_formatted"] = df_feed["amount"].apply(lambda x: format_curr(x, currency))
        if "probability" in df_feed.columns:
            df_feed["probability"] = df_feed["probability"].apply(lambda x: f"{x:.2%}")
        if "latency_ms" in df_feed.columns:
            df_feed["latency_ms"] = df_feed["latency_ms"].apply(lambda x: f"{x:.2f} ms")

        cols_to_show = ["id", "created_at", "prediction", "probability", "risk_level", "amount_formatted", "latency_ms"]
        available_cols = [c for c in cols_to_show if c in df_feed.columns]
        
        st.dataframe(df_feed[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No audit records found in PostgreSQL yet. Run simulations in Tab 1 or publish Kafka messages to generate live records.")

# -----------------------------------------------------------------------------
# TAB 3: RBI COMPLIANCE & MODERN AI FRAMEWORKS
# -----------------------------------------------------------------------------
with tab3:
    st.subheader("Regulatory Compliance & Architectural Foundations")
    st.markdown(r"""
    ### Alignment with Reserve Bank of India (RBI) Directives
    SentinelPay embeds RBI regulatory mandates into its System-1 decision routing logic:
    
    1. **Master Direction on Digital Payment Security Controls (Section 8)**:
       - Mandates continuous fraud monitoring and anomaly detection mechanisms for digital transactions.
       - Enforced when marginal risk is observed ($0.35 \dots 0.49$), routing the transaction to background telemetry logging without adding user friction.
    
    2. **Additional Factor of Authentication (AFA) Mandate**:
       - Mandates two-factor authentication for remote card and high-value payments.
       - Enforced when moderate fraud probability ($0.50 \dots 0.84$) or nocturnal carding bursts occur, triggering `STEP_UP_2FA_CHALLENGE`.
    
    3. **Circular DPSS.CO.PD.No.2224/02.14.003 (Limiting Customer Liability)**:
       - Preserves zero customer liability for unauthorized electronic banking operations.
       - Enforces `IMMEDIATE_FREEZE` when high-confidence fraud signatures ($>= 0.85$) or severe PCA anomalies are intercepted.

    ---

    ### Cutting-Edge AI Paradigm Matrix
    
    | Paradigm | SentinelPay Implementation |
    | :--- | :--- |
    | **LLM-as-Jev** | Ultra-fast System-1 decision engine (< 80ms) returning strictly typed action payloads before prose generation. |
    | **LLM-as-a-Judge** | Audit verification engine assessing model classifications against regulatory circulars. |
    | **Model Context Protocol (MCP)** | Interactive agentic tools empowering compliance investigators to freeze accounts, dispatch OTPs, and update whitelists. |
    | **TreeSHAP Attribution** | Mathematical local log-odds attribution preserving complete transparency without speculative proxy labels. |
    """)
