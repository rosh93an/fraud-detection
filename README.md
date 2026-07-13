# Real-Time Fraud Detection System
## Complete Project README — Stages 1–11
**Author:** Roshan Shetty | **Dataset:** Kaggle Credit Card Fraud | **2026**

---

## Project Status — All Stages Complete

| Stage | Component | Status |
|---|---|---|
| 1 | EDA & Data Analysis | ✅ Complete |
| 2 | Preprocessing + Feature Engineering | ✅ Complete |
| 3 | Model Training (LR, RF, XGBoost) + MLflow | ✅ Complete |
| 4 | FastAPI REST Serving | ✅ Complete |
| 5 | Docker Containerization | ✅ Complete |
| 6 | PostgreSQL Prediction Logging | ✅ Complete |
| 7 | GitHub Actions CI | ✅ Complete |
| 8 | AWS EC2 Deployment | ✅ Complete |
| 9 | Evidently AI Drift Monitoring | ✅ Complete |
| 10 | Kafka/Redpanda Streaming | ✅ Complete |
| 11 | Full CI/CD (Auto-Deploy) | ✅ Complete |

**Live API:** `http://13.235.71.227:8000` | **Docs:** `/docs` | **Health:** `/health`

---

## Architecture Overview

```
                    ┌─────────────────┐
                    │   GitHub Repo   │
                    │  (source code)  │
                    └────────┬────────┘
                             │ git push
                             ↓
                    ┌─────────────────┐
                    │ GitHub Actions  │
                    │  test_and_build │
                    │  → deploy (SSH) │
                    └────────┬────────┘
                             │ auto-deploy
                             ↓
┌──────────┐        ┌─────────────────┐        ┌──────────────┐
│ Redpanda │───────→│   AWS EC2       │───────→│  PostgreSQL  │
│ (stream, │        │   Docker        │        │ (predictions │
│  local)  │        │   FastAPI       │        │  + features) │
└──────────┘        │   XGBoost       │        └──────────────┘
                     └────────┬────────┘
                              │ feature data
                              ↓
                     ┌─────────────────┐
                     │   Evidently AI  │
                     │ (drift reports) │
                     └─────────────────┘
```

---

# Stage 1 — EDA (Exploratory Data Analysis)

### Dataset
- **Source:** Kaggle Credit Card Fraud Detection (European cardholders)
- **Rows:** 284,807 transactions | **Columns:** 31 (Time, V1–V28 PCA features, Amount, Class)
- **Fraud:** 492 cases (0.172%) | **Normal:** 284,315 (99.828%)
- **Missing values:** Zero

### Key Commands
```python
df = pd.read_csv('../data/creditcard.csv')
df['Class'].value_counts(normalize=True) * 100   # 99.83% / 0.17%
fraud_df  = df[df['Class']==1]
normal_df = df[df['Class']==0]
correlations = df.corr()['Class'].drop('Class').sort_values()
```

### Key Findings
| Finding | Explanation |
|---|---|
| Severe class imbalance | 99.83% normal vs 0.17% fraud — accuracy is a misleading metric |
| Fraud amount range | 75% of fraud is under €105 — fraudsters avoid large amounts |
| Time pattern | Normal transactions follow a day/night cycle; fraud is random 24/7 |
| Top fraud features | V11, V4, V2 positively correlated; V17, V14, V12 strongly negative |
| V17 fraud mean | -6.67 vs normal mean 0.01 — large separation despite PCA normalization |
| Amount correlation alone | Very weak — V features are required for real detection |

**Why PCA features still separate fraud:** PCA was fit on the FULL dataset. Normal transactions (99.83%) dominate the combined statistics (mean≈0, std≈1 overall). Isolating the 492 fraud rows reveals their own natural pattern, hidden inside the combined average.

---

# Stage 2 — Preprocessing + Feature Engineering

### Features Created
| Feature | Formula | Purpose |
|---|---|---|
| Hour | `(Time / 3600) % 24` | Human-readable time of day |
| Amount_log | `log1p(Amount)` | Reduces skew from outliers; handles zero amounts safely |
| Amount_bin | `pd.cut(Amount, bins=[0,10,50,200,500,inf])` | Captures transaction size category |

**Why `log1p` not `log`:** `log(0) = -infinity` (crashes). `log1p(0) = log(1) = 0.0` (safe). Zero-amount transactions are real — they represent card-testing fraud, so they cannot be dropped.

### Error: SMOTE Rejected Data (NaN values)
- **Cause:** `pd.cut(bins=[0,...])` uses `(left, right]` intervals by default — Amount=0 falls outside every bin and becomes NaN. 1,825 zero-amount rows were affected.
- **Fix:** Added `include_lowest=True` to `pd.cut()`, which changes the first bin to `[0, 10]`, including zero. NaN count dropped from 1,825 to 0.

### The Leakage Rule
Always split data **before** fitting any preprocessing. Fit `StandardScaler` on `X_train` only; transform `X_test` with that same fitted scaler. `stratify=y` in `train_test_split` ensures both splits keep the same 99.83%/0.17% fraud ratio.

### SMOTE — Class Imbalance (Initial Approach)
```python
smote = SMOTE(random_state=42)
X_train_bal, y_train_bal = smote.fit_resample(X_train, y_train)
# Before: Fraud=344, Normal=199020 → After: Fraud=199020, Normal=199020
```
SMOTE creates synthetic fraud samples between real ones (not duplication), so the model learns the *region* of fraud rather than memorizing 344 exact points. Applied to training data only — test data stays imbalanced to reflect the real world.

---

# Stage 3 — Model Training + MLflow

### Four Models Compared
| Model | Key Parameters | Imbalance Handling |
|---|---|---|
| Logistic Regression | `max_iter=1000, class_weight='balanced'` | SMOTE + class_weight (double-balancing — a mistake) |
| Random Forest | `n_estimators=100, max_depth=10` | SMOTE |
| XGBoost v1 | `n_estimators=100, max_depth=6, lr=0.1` | SMOTE |
| **XGBoost (winner)** | `n_estimators=300, max_depth=6, lr=0.05` | `scale_pos_weight=578` (no SMOTE) |

### Final Results
| Metric | LR | RF | XGB (Winner) |
|---|---|---|---|
| AUC-ROC | 0.9701 | 0.9783 | 0.9627 |
| F1 Score | 0.11 | 0.62 | **0.83** |
| Precision | 0.06 | 0.50 | **0.87** |
| Recall | 0.88 | 0.81 | 0.80 |
| False Alarms | 2,069 | 120 | **17** |
| Fraud Missed | 18 | 28 | 30 |

### Why XGBoost Without SMOTE Won
SMOTE generated 199,020 synthetic fraud rows from only 344 real ones (578× oversampling). XGBoost — being a sequential, error-correcting model — overfit to the synthetic patterns rather than real ones. Using `scale_pos_weight=578` instead tells XGBoost to weight each *real* fraud sample 578× more heavily during training, with zero synthetic data. Precision jumped from 0.46 (XGBoost+SMOTE) to 0.87, and false alarms dropped from 120+ to 17.

**Rule of thumb:** for tree-based models (Random Forest, XGBoost), `scale_pos_weight` often beats SMOTE. For linear models (Logistic Regression), SMOTE/class_weight still helps.

### MLflow Tracking
```python
mlflow.set_experiment('fraud_detection')
with mlflow.start_run(run_name='xgboost_no_smote'):
    mlflow.log_param('scale_pos_weight', ratio)
    model.fit(X_train, y_train)
    mlflow.log_metric('f1_score', f1)
    mlflow.sklearn.log_model(model, 'model')
# Dashboard: mlflow ui → http://localhost:5000
```
Every run records parameters, metrics, and the model artifact — allowing direct side-by-side comparison of all 4 models in one dashboard.

---

# Stage 4 — FastAPI Model Serving

### Structure
```
api/
├── __init__.py        # makes api/ a proper Python package
├── app.py              # FastAPI endpoints
└── model_utils.py      # preprocessing + risk-level logic
```

### Endpoints
| Endpoint | Purpose |
|---|---|
| `GET /` | Root — API info |
| `GET /health` | Health check (status, model, version) |
| `POST /predict` | Send transaction → get fraud prediction |
| `GET /stats` | Aggregate stats from PostgreSQL |

### Prediction Flow
1. Pydantic validates all 30 fields (types, `Amount > 0`)
2. `preprocess_input()` creates `Hour`, `Amount_log`, `Amount_bin`; drops `Time`/`Amount`; scales `Hour`/`Amount_log` using the saved `scaler.pkl`
3. `model.predict_proba()` returns fraud probability
4. `probability >= 0.5` → `"FRAUD"` else `"NORMAL"`; `get_risk_level()` maps to HIGH/MEDIUM/LOW/SAFE
5. Result logged and saved to PostgreSQL, then returned as JSON

### Errors & Fixes
| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: model_utils` | Running `uvicorn api.app:app` from `/app` looked for `/app/model_utils.py`, which didn't exist (only existed locally inside `api/`) | Added `api/__init__.py`; changed import to `from api.model_utils import ...`; added `ENV PYTHONPATH=/app` in Dockerfile |
| Logger `TypeError: not all arguments converted` | `logger.info(f"...", f"...", f"...")` passed multiple args — Python's logging tried `%`-style formatting | Combined into one single f-string |
| `404 Not Found` on `/health` | Missing `@` decorator (`app.get("/health")` instead of `@app.get("/health")`) is just a function call, not a route registration; also caught a `/Health` vs `/health` case-sensitivity bug | Added `@`; standardized to lowercase URLs; verified inside the running container with `docker exec -it <container> bash` → `grep -n health api/app.py` (Docker caches old code — rebuilds are required after every fix) |

---

# Stage 5 — Docker Containerization

### Dockerfile
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt
COPY models/ ./models/
COPY api/ ./api/
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Error: pywinpty Build Failure
- **Cause:** `pip freeze > requirements.txt` dumped all 190 packages from the conda environment, including `pywinpty` — a Windows-only terminal library that cannot compile on Linux.
- **Fix:** Created a minimal `requirements_api.txt` with only the 9–13 packages the API actually needs (fastapi, uvicorn, pydantic, scikit-learn, xgboost, pandas, numpy, joblib, psycopg2-binary, pytest). Always maintain a separate, minimal requirements file for deployment.

### Error: scikit-learn Version Mismatch
- **Cause:** `requirements_api.txt` pinned a different scikit-learn version than the one used to fit `scaler.pkl` locally, producing an `InconsistentVersionWarning`.
- **Fix:** Matched the exact version via `pip show scikit-learn` and pinned it identically in `requirements_api.txt`.

### Docker Commands Reference
| Command | Purpose |
|---|---|
| `docker build -t fraud-detection-api .` | Build image |
| `docker run -d --name fraud-api -p 8000:8000 fraud-detection-api` | Run container |
| `docker logs fraud-api` | View logs |
| `docker exec -it fraud-api bash` | Shell into running container |
| `docker compose up --build -d` | Build + start all services |
| `docker system prune -a -f` | Remove unused images/cache (critical on small disks) |

**Lesson:** Docker caches layers — code changes require a full `down → build → up` cycle, or the container silently keeps running old code.

---

# Stage 6 — PostgreSQL Prediction Logging

Initially logged: `prediction, probability, risk_level, amount, latency_ms, created_at`. Later (Stage 9) extended to store the full feature set.

```python
def save_prediction(prediction, probability, risk_level, amount, latency_ms, raw_data=None):
    cursor.execute("""
        INSERT INTO predictions (prediction, probability, risk_level, amount, latency_ms, ...)
        VALUES (%s, %s, %s, %s, %s, ...)
    """, (...))
```

`/stats` endpoint aggregates: total predictions, fraud count, normal count, average probability, average latency — proven end-to-end with real curl tests showing 99.85% fraud detection and correct DB persistence.

---

# Stage 7 — GitHub Actions CI

### Workflow (`ci.yml`)
```yaml
jobs:
  test_and_build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with: { python-version: '3.12' }
      - run: pip install -r requirements_api.txt
      - run: python -m pytest tests/ -v -s
      - run: docker build -t fraud-detection-api .
      - run: python -c "from api.model_utils import preprocess_input, get_risk_level; print('Imports OK')"
```

### Errors & Fixes
| Error | Fix |
|---|---|
| Missing `.` in `docker build` command | Added `.` (build context = current directory) |
| Typo `requiremnt` in workflow | Corrected to `requirements` |
| `No module named pytest` on fresh runner | Added `pytest` to `requirements_api.txt` — GitHub's runner is a brand-new machine with nothing pre-installed |
| Model `.pkl` files missing in CI | `models/` was in `.gitignore`; used `git add -f models/*.pkl` to force-track the model artifacts required for the Docker build |
| `AttributeError: 'tuple' object has no attribute 'ndim'` | `preprocess_input()` was changed (Stage 9) to return `(features, engineered)` as a tuple, but `tests/test_api.py` still expected a single array — updated tests to unpack the tuple |

---

# Stage 8 — AWS EC2 Deployment

- **Region:** ap-south-1 (Mumbai) | **Instance:** t3.micro (free tier) | **OS:** Ubuntu
- Security Group: port 22 (SSH, restricted to "My IP"), port 8000 (API, `0.0.0.0/0`), port 5432/5433 (Postgres, restricted)

### Errors & Fixes
| Error | Cause | Fix |
|---|---|---|
| `ssh: connect ... Connection refused` (port 22) | Home ISP IP changed overnight; security group's "My IP" rule still pointed at yesterday's IP | Re-selected "My IP" in the security group to refresh to the current IP |
| `docker-compose up --build` panicked (Go runtime slice-bounds error) | Bug in Docker Compose's BuildKit/bake integration | Worked around with `DOCKER_BUILDKIT=0 docker-compose up --build` |
| `fraud-api` healthcheck stuck "unhealthy" | Healthcheck used `curl`, which isn't installed in the slim Python image | Changed healthcheck to a Python one-liner using `urllib.request` (already available, no extra package needed) |
| Postgres port conflict (`password authentication failed`) | A **native PostgreSQL Windows service** (separate from Docker) was also listening on port 5432 on the laptop, intercepting connections meant for the Docker container | Diagnosed via `netstat -ano | findstr :5432` + `tasklist`; remapped Docker's Postgres to host port `5433` instead of touching the native service |
| `OSError: [Errno 28] No space left on device` during EC2 rebuild | t3.micro's 8GB disk filled up with accumulated Docker layers/images across many rebuilds (Kafka, Zookeeper, old image versions) | `docker system prune -a -f` + `docker volume prune -f`; ultimately reduced footprint by replacing Kafka+Zookeeper with the lighter Redpanda |

---

# Stage 9 — Evidently AI Drift Monitoring

### Extending the Database Schema
To support real input-feature drift detection (not just output monitoring), the `predictions` table was extended to also store every `V1`–`V28`, `Hour`, `Amount_log`, and `Amount_bin` value alongside each prediction. This required:
1. `database.py`: new columns in `create_table()`, updated `save_prediction()` signature with a `raw_data` dict
2. `model_utils.py`: `preprocess_input()` now returns **two** values — `(features_array, engineered_dict)` — since converting to a numpy array for the model strips column names, the `engineered` dict preserves the named Hour/Amount_log/Amount_bin values for storage
3. `app.py`: merges the original request data with `engineered` into one `full_data` dict before calling `save_prediction()`

### Error: `column "v1" does not exist`
- **Cause:** The `predictions` table already existed from Stage 6 with the old schema; `CREATE TABLE IF NOT EXISTS` silently does nothing if the table is already present, so the new V1–V28 columns never got added.
- **Fix:** `DROP TABLE predictions;` then restarted the API so `create_table()` ran fresh with the new schema.

### Error: `DATABASE_URL` Typo (Recurring Bug)
- **Cause:** `database.py` had `os.getenv("DATABASE URL", ...)` — a literal **space** instead of an underscore. Since that exact string never matches a real env var, the code silently always fell back to the hardcoded default (`...@db:5432/...`), which only resolves correctly *inside* Docker's network, not from the laptop or EC2 host directly.
- **Fix:** Corrected to `"DATABASE_URL"`. This bug had been masking itself for a while because the fallback value happened to also be "correct enough" when running fully inside Docker.

### Drift Report Workflow
```python
report = Report(metrics=[DataDriftPreset()])
report_output = report.run(reference_data=reference_df, current_data=production_df)
report_output.save_html('../notebooks/drift_report_production.html')
```
`reference_df` = original training data (199,364 rows). `production_df` = real rows pulled live from PostgreSQL via `psycopg2`/`pandas.read_sql`. With a tiny sample (~11–82 real predictions), Evidently correctly flagged differences (expected with such a small sample size vs. 199K reference rows) — proving the full pipeline (predict → store → retrieve → compare) works end-to-end on genuinely real data, not just simulation.

---

# Stage 10 — Kafka / Redpanda Streaming

### Why Streaming, Separately From FastAPI
FastAPI handles one-request-one-response (e.g., a customer paying at checkout). A streaming architecture handles high-throughput, asynchronous processing — useful for batch reprocessing or traffic spikes a request/response API isn't designed for.

### Kafka → Redpanda Migration
Initially set up with Kafka + Zookeeper (two containers, ~2.7GB combined images, ~1GB+ RAM). Switched to **Redpanda** — a single container that speaks the same Kafka wire protocol, eliminating Zookeeper entirely and cutting resource usage significantly. **Zero code changes** were needed in the producer/consumer Python scripts, since `kafka-python` only cares about the protocol, not which server implements it.

```yaml
redpanda:
  image: redpandadata/redpanda:latest
  command: [redpanda, start, --overprovisioned, --smp, "1", --memory, "512M", ...]
  ports: ["9092:9092"]
```

### Producer / Consumer
- `kafka_producer.py` — simulates transactions (mix of normal-looking and fraud-pattern-matching), publishes to the `transactions` topic
- `kafka_consumer.py` — loads the same `fraud_model_xgb.pkl`, listens continuously, runs every message through the model, saves results to PostgreSQL — proving the model can serve both synchronous (FastAPI) and asynchronous (streaming) workloads from one shared codebase

### Recurring Error: Wrong Database Host When Running Outside Docker
Scripts run on the laptop (outside Docker) need `DATABASE_URL=postgresql://frauduser:fraudpass@localhost:5433/frauddb` explicitly — the default `db:5432` hostname only resolves inside Docker's internal network. Forgetting this (e.g., after opening a *new* terminal session, since `export` doesn't persist across terminal windows) was the most common recurring issue throughout Stages 9–10.

---

# Stage 11 — Full CI/CD (Continuous Deployment)

### What CD Adds
CI (Stage 7) stopped at "tests pass, Docker builds." CD adds a second job that, only if CI passes, SSHs into EC2 and redeploys automatically.

```yaml
jobs:
  test_and_build: { ... }
  deploy:
    needs: test_and_build
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USER }}
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/fraud-detection
            git pull origin main
            docker compose down
            docker compose up --build -d
```

GitHub Secrets (`EC2_SSH_KEY`, `EC2_HOST`, `EC2_USER`) keep credentials out of the repository entirely.

### Errors & Fixes
| Error | Cause | Fix |
|---|---|---|
| `deploy` job never appeared in Actions UI | The job block was accidentally dropped while cleaning up duplicated workflow content during an earlier edit | Re-added the complete `deploy:` job under the same `jobs:` key, with `needs: test_and_build` matching the *exact* job name |
| EC2 repo diverged from GitHub (local edits never pushed) | Manual fixes (port 5433, DATABASE_URL typo, docker-compose changes) had been made directly on EC2 via SSH at various points, never committed back | Established the rule: **all changes happen on the laptop, get pushed to GitHub, then EC2 only ever runs `git pull`** — EC2's repo was reset with `git fetch && git reset --hard origin/main && git clean -fd` to eliminate drift permanently |
| Disk full mid-deploy (`No space left on device`) | Repeated rebuilds + Kafka/Zookeeper images accumulated on the 8GB EC2 volume | `docker system prune -a -f`; permanently reduced footprint by migrating to Redpanda |

**Verified:** pushing a trivial change to `api/app.py`'s root message and observing it appear live at `http://13.235.71.227:8000/` *without* manually SSHing in, confirmed the full pipeline works end-to-end.

---

# Key Engineering Lessons (Cross-Cutting)

1. **Docker caches aggressively** — a code fix isn't real until you rebuild *and* verify inside the running container (`docker exec ... grep ...`), not just on disk.
2. **Environment variables don't persist across terminal sessions** — `export` only lives for that one shell window; scripts run outside Docker need explicit `DATABASE_URL` overrides pointing at `localhost`, not the Docker-internal service name (`db`).
3. **`CREATE TABLE IF NOT EXISTS` won't migrate an existing table** — schema changes on a table that already exists require an explicit `ALTER TABLE` or a deliberate drop-and-recreate.
4. **A single typo in an env var name (`"DATABASE URL"` vs `"DATABASE_URL"`) fails silently** — `os.getenv()` just falls back to its default with no error, which can mask a bug for a long time if the fallback happens to mostly work.
5. **Free-tier infrastructure is genuinely resource-constrained** — choosing Redpanda over Kafka+Zookeeper, and `scale_pos_weight` over SMOTE for tree models, were both deliberate, explainable engineering trade-offs rather than compromises.
6. **CI ≠ CD** — passing tests on every push (CI) is necessary but not sufficient for automatic deployment (CD); CD requires its own job, its own credentials (via Secrets), and a clear separation between "tests passed" and "deployed."

---

# Pending / Future Work

| Item | Status | Notes |
|---|---|---|
| Nginx reverse proxy | Not implemented | Would drop the `:8000` from the public URL, add HTTPS termination and load-balancing readiness; deferred to preserve EC2 free-tier disk headroom for other projects |
| EBS volume resize | Deliberately deferred | 30GB free-tier allowance is shared across all AWS projects on the account; resizing this project's 8GB volume would reduce what's available elsewhere |
| Kubernetes | Not implemented | Would need a much larger instance than t3.micro to run meaningfully; documented as a known next step rather than attempted on insufficient hardware |
| Apache Airflow | Documented separately (see below) | Natural next step for scheduling periodic retraining / batch drift reports |
