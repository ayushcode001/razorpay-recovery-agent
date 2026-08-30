# Payment Recovery Agent
**Razorpay AI Buildathon — Track 03: AI Revenue Recovery**

> **Autonomous AI revenue recovery agent that intercepts failed payments, causal-filters self-recoveries, optimizes retry timings, monitors systemic outages, and executes bounded recovery workflows with an immutable audit trail.**

An explainable, multi-component revenue recovery system for Razorpay merchants that pairs deterministic domain safety gates with 4 specialized ML models to maximize recovered net revenue while minimizing wasted costs and customer friction.

**Repository**: [https://github.com/ayushcode001/razorpay-recovery-agent](https://github.com/ayushcode001/razorpay-recovery-agent)

---

## 1. Executive Summary & Pitch Cheat Sheet (One Sentence Per Component)

| Component | Role / Technology | One-Sentence Pitch |
|---|---|---|
| **1. Deterministic Taxonomy** | `agent/taxonomy.py` | Governs legal and compliance safety boundaries, ensuring high-risk and fraud-blocked payments are never autonomously retried. |
| **2. Success Predictor** | `agent/success_predictor.py` (Gradient Boosting) | Predicts $P(\text{intervention succeeds} \mid \text{context})$ to evaluate whether an attempt is statistically viable before burning budget. |
| **3. Causal Uplift Modeler** | `agent/uplift_model.py` (T-Learner Causal ML) | Isolates genuine treatment lift from organic self-recovery ($\mu_1(x) - \mu_0(x)$) so merchants never waste notifications on transactions that would self-resolve. |
| **4. Degradation Monitor** | `agent/degradation_agent.py` (Seasonal Z-Score) | Forecasts and detects systemic bank/gateway outages in real-time ($z \ge 3.0\sigma$) with estimated INR revenue impact before outages drain merchant revenue. |
| **5. Contextual Retry Bandit** | `agent/retry_bandit.py` (Thompson Sampling) | Discovers the optimal cooldown delay per error category through reinforcement learning, outperforming fixed static cooldowns by up to +400% in simulated recoveries. |
| **6. Cohort Strategic Analyst** | `agent/cohort_analyst.py` (GMM / PCA Clustering) | Uncovers latent transaction archetypes and ranks untapped merchant segments by recoverable INR to guide strategic revenue recovery ROI. |

---

## 2. Problem Taste & AI Judgment: Where We Used ML (And Where We Didn't)

A common pitfall in revenue recovery is "fake ML" — training NLP or classifiers to predict *why* a payment failed. Razorpay's `payment.failed` webhook already hands you `error_code` and `error_reason` for free (e.g. `insufficient_funds`, `card_expired`, `payment_risk_check_failed`). Re-classifying that with an LLM or classifier is re-deriving a lookup table.

### The Clear Separation of Concerns:
1. **Deterministic Taxonomy**: Domain policy governs what interventions are legally and operationally *allowed*. Sensitive violations like risk check failures and compliance violations are **never** auto-actioned.
2. **Learned Success ML Model**: Predicts the probability that an intervention will actually succeed given transaction features (Amount, Prior Retries, Hour of Day, Method, Source, Category).
3. **Causal Uplift Refinement Layer**: Filters out false-positive successes that would have organically self-recovered without intervention.
4. **Data-Driven Policy Engine**: Combines taxonomy + success probability threshold + causal uplift threshold + retry budgets into an explainable, bounded decision per transaction.

---

## 3. The 4 Advanced ML Components

### Component A: Causal Uplift Modeling (T-Learner)
- **Question Answered**: *"Did OUR intervention cause the recovery, or would it have happened anyway?"*
- **Architecture**: A two-model T-Learner estimator ($\mu_1$ on treatment arm, $\mu_0$ on control arm).
  $$\text{Estimated Uplift}(x) = \mu_1(x) - \mu_0(x)$$
- **Validation**: Pearson correlation of **0.5266** ($p = 8.35 \times 10^{-23}$) against synthetic ground-truth treatment effects on held-out test data.
- **Honest Caveat**: Real-world per-transaction uplift is fundamentally unobservable (the fundamental problem of causal inference). Synthetic validation confirms estimation integrity and pipeline soundness before live A/B rollout.

### Component B: Time-Series Systemic Degradation Forecasting
- **Question Answered**: *"Is a specific bank or payment gateway experiencing an outage right now?"*
- **Architecture**: Computes rolling seasonal mean and standard deviation per `(bank, method, hour_of_day, is_weekend)` bucket, scoring deviations via Z-Score.
- **Validation**: Evaluated across 30 days (10,800 channel-hours) with injected outages:
  - **Outage Recall**: **100.0%** (all multi-hour outage incidents detected).
  - **False Positive Rate on Normal Windows**: **0.06%**.
  - **Financial Impact Attribution**: Top caught incident: *HDFC Card Outage (Day 8)* -> ₹2,487,659 at risk over 7 hours.

### Component C: Contextual Bandit for Dynamic Retry Timing (Offline Demo)
- **Question Answered**: *"What delay timing maximizes recovery probability for this failure mode?"*
- **Architecture**: Thompson Sampling Multi-Armed Bandit with $\text{Beta}(\alpha, \beta)$ conjugate posteriors over 5 discrete delay arms (1m, 15m, 1h, 6h, 24h).
- **Simulation**: 5,000 episodes per error category evaluated against a static 1-minute cooldown baseline:
  - `retry_later` (insufficient funds): Converged to **24h Cooldown** (99.9% pull rate, **+412.1% recovery lift**).
  - `smart_retry` (gateway latency): Converged to **15m Backoff** (99.8% pull rate, **+82.7% recovery lift**).
  - `change_method` (expired card): Converged to **6h Window** (98.9% pull rate, **+641.1% recovery lift**).
  - `user_error` (wrong CVV/OTP): Converged to **1h Nudge** (99.9% pull rate, **+202.0% recovery lift**).
- **Deliverable**: Generated convergence comparison plot `bandit_convergence.png`.

### Component D: Strategic Cohort Analyst (Unsupervised Clustering)
- **Question Answered**: *"Which latent customer segments represent the largest recoverable revenue opportunity?"*
- **Architecture**: GMM clustering on standardized continuous signals + one-hot features projected onto 2D PCA space.
- **Key Insight**: Discovered 5 archetypes where the top 2 Enterprise cohorts account for **>79% of total recoverable INR** (₹9,925,273 recoverable opportunity).
- **Non-Triviality Verification**: 5 of 5 discovered clusters cross taxonomy boundaries (discovering true multi-dimensional interaction patterns rather than single-field rehashes).
- **Deliverables**: Generated scatter projection `cohort_scatter.png` and report `cohort_report.txt`.

---

## 4. Batch Results & Before/After Metrics (n=1200 records, ₹3.76 Crore At Risk)

| Metric | Baseline Policy (Naive 0.40) | Tuned Policy (0.47) | Tuned + Uplift Refinement | Business Impact |
|---|---|---|---|---|
| **Total Amount at Risk** | ₹37,569,620 | ₹37,569,620 | ₹37,569,620 | Real-schema synthetic batch |
| **Total Transactions Handled** | 1,200 | 1,200 | 1,200 | End-to-end evaluation |
| **Autonomous Interventions Attempted** | 783 (65.3%) | 736 (61.3%) | **736 (61.3%)** | Bounded & gated actions |
| **Skipped (Low Causal Uplift / Self-Recovery)** | 0 | 0 | **47 (3.9%)** | Eliminates wasted notifications |
| **Escalated to Human Review** | 417 (34.7%) | 464 (38.7%) | **417 (34.7%)** | Risk & compliance protected |
| **Total Amount Recovered** | ₹14,891,400 | ₹14,195,147 | **₹14,195,147** | High-confidence conversion |
| **Amount Wasted on Failed Attempts** | ₹7,210,500 | ₹6,099,284 | **₹6,099,284** | **-15.4% reduction in wasted spend** |
| **Recovery Rate *of Attempted Cases*** | 67.3% | 69.95% | **69.95%** | Precision on customer touchpoints |

---

## 5. System Architecture

```
                                  +-----------------------------+
                                  |   Razorpay Webhook Event    |
                                  |       payment.failed        |
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |     Webhook Adapter Layer   |
                                  | (error_reason / error_code) |
                                  +--------------+--------------+
                                                 |
                         +-----------------------+-----------------------+
                         v                                               v
          +-----------------------------+                 +-----------------------------+
          |      agent/taxonomy.py      |                 |  agent/success_predictor.py |
          |   (Deterministic Policy)    |                 |   (Gradient Boosting ML)    |
          |  - Risk/Compliance gates    |                 |  - Predicts P(Success)      |
          |  - Category cooldown rules  |                 |  - Contextual feature prep  |
          +--------------+--------------+                 +--------------+--------------+
                         |                                               |
                         +-----------------------+-----------------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |    agent/uplift_model.py    |
                                  |   (Causal T-Learner Gate)   |
                                  |  - P_treated - P_control    |
                                  |  - Filters self-recoveries  |
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |    agent/policy_engine.py   |
                                  |    (Bounded Stopping Rule)  |
                                  |  - P(Success) >= 0.47?      |
                                  |  - Uplift >= 0.05?          |
                                  |  - Max retries exceeded?    |
                                  +--------------+--------------+
                                                 |
                  +------------------------------+------------------------------+
                  v                              v                              v
   +-----------------------------+ +-----------------------------+ +-----------------------------+
   |      Autonomous Retry       | |    Customer Notification    | |     Escalate to Human       |
   | (retry_after_cooldown /     | | (prompt_new_payment_method/ | | (Risk check / Low-uplift /  │
   |  retry_with_backoff)        | |  reprompt_customer)         | |  Max retries exhausted)     │
   | -> Razorpay Payment Link    | | -> Payment Link + Email/SMS | | -> Graceful bounded stop    │
   +--------------+--------------+ +--------------+--------------+ +--------------+--------------+
                  |                              |                              |
                  +------------------------------+------------------------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |       agent/audit.py        |
                                  | -> audit_logs/audit_trail   |
                                  +-----------------------------+
```

---

## 6. Live Webhook Demo & Quickstart

### 1. Setup Environment
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 2. Launch the Autonomous Server
```bash
python webhook/server.py
```
- **Live Dashboard**: `http://localhost:5000/` (Live audit trail + Systemic Degradation Outage panel)
- **Interactive Checkout Demo**: `http://localhost:5000/checkout`
- **Live Webhook Listener**: `http://localhost:5000/webhook/razorpay`

### 3. Run Pipeline Test Suite & ML Verification
```bash
# 1. Run full webhook & agent flow integration tests
python tests/test_webhook_flow.py

# 2. Run T-Learner Uplift Model training & validation
python agent/uplift_model.py

# 3. Run Time-Series Degradation Outage Detector
python agent/degradation_agent.py

# 4. Run Contextual Bandit Retry Timing Simulation (generates bandit_convergence.png)
python agent/retry_bandit.py 5000

# 5. Run Cohort Strategic Analyst (generates cohort_scatter.png & cohort_report.txt)
python agent/cohort_analyst.py
```

---

## 7. Audit Trail & Failure Recovery Philosophy

Every decision — autonomous retry, customer re-prompt, low-uplift skip, or human escalation — is timestamped and recorded in `audit_logs/audit_trail.json` with an explicit reason string. No silent drops, no black-box money actions.
