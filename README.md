# Autonomous Payment Recovery Agent

**Razorpay AI Buildathon — Track 03: AI Revenue Recovery**

> **An autonomous, explainable AI revenue recovery agent that detects failed Razorpay payments, isolates causal intervention uplift from organic self-recovery, optimizes retry cooldowns via reinforcement learning, monitors systemic outages in real-time, and executes bounded recovery workflows with a full audit trail.**

Built for Razorpay merchants, this system pairs strict deterministic compliance gates with **4 specialized machine learning models** to maximize net recovered revenue while eliminating wasted retry spend, spamming, and customer friction.

**Repository**: [https://github.com/ayushcode001/razorpay-recovery-agent](https://github.com/ayushcode001/razorpay-recovery-agent)

---

## 1. Executive Summary & Pitch Cheat Sheet

| Component                       | Role / Module                | Technology                                       | One-Sentence Pitch                                                                                                                                                            |
| ------------------------------- | ---------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Deterministic Taxonomy**   | Safety Gates & Rules         | `agent/taxonomy.py`                              | Governs legal and compliance safety boundaries, ensuring high-risk, international blocks, and fraud-flagged payments are strictly escalated—never retried.                    |
| **2. Success Predictor**        | Intervention Feasibility     | `agent/success_predictor.py` (Gradient Boosting) | Predicts $P(\text{intervention succeeds} \mid \text{context})$ using transaction features to evaluate whether an attempt is statistically viable before burning retry budget. |
| **3. Causal Uplift Modeler**    | Organic Self-Recovery Filter | `agent/uplift_model.py` (T-Learner Causal ML)    | Isolates genuine intervention lift from organic self-recovery ($\mu_1(x) - \mu_0(x)$) so merchants never waste notifications or retries on payments that would self-resolve.  |
| **4. Degradation Forecaster**   | Systemic Outage Monitor      | `agent/degradation_agent.py` (Seasonal Z-Score)  | Detects bank and gateway outages in real-time ($z \ge 3.0\sigma$) with estimated INR revenue impact before widespread issuer latency drains merchant revenue.                 |
| **5. Contextual Retry Bandit**  | Dynamic Timing Optimizer     | `agent/retry_bandit.py` (Thompson Sampling)      | Learns the optimal retry cooldown per error category through multi-armed bandit exploration, validating hand-set heuristics and discovering non-obvious delay gains.          |
| **6. Strategic Cohort Analyst** | Latent Segment Discovery     | `agent/cohort_analyst.py` (GMM + PCA Clustering) | Uncovers latent transaction archetypes and ranks untapped merchant segments by recoverable INR to guide strategic revenue recovery ROI.                                       |

---

## 2. Problem Taste & AI Judgment: Where We Used ML (And Where We Didn't)

A standard pitfall in AI payment hackathons is **"Fake ML"** — training an NLP classifier or LLM to predict why a transaction failed based on webhook error strings. In production, Razorpay's `payment.failed` webhook already gives you `error_code` and `error_reason` for free (e.g. `insufficient_funds`, `card_expired`, `payment_risk_check_failed`). Re-predicting that is re-deriving a lookup table.

### Clear Separation of Concerns:

```
                      PAYMENT FAILURE EVENT
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
     DETERMINISTIC DOMAIN              LEARNED ML MODELS
       (Known Knowns)                  (Unknown Signals)
   • Allowed actions per error      • P(Success | Context)
   • Hard compliance/risk stops     • Causal Uplift (P1 - P0)
   • Max retry limits & cooldowns   • Dynamic Timing (Bandit)
   • Zero hallucination guarantee   • Outage Anomaly Z-Score
```

1. **Deterministic Taxonomy**: Domain policy decides what actions are legally and operationally _permissible_.
2. **Success Predictor**: Learns whether an allowed intervention will _actually succeed_ given transaction context.
3. **Causal Uplift Gate**: Verifies whether our intervention adds _causal lift_ or whether the customer would self-recover without us.
4. **Data-Driven Policy Engine**: Combines taxonomy rules + tuned success threshold (0.47) + uplift gate ($\ge 0.05$) into a bounded, explainable decision.

---

## 3. Deep Dive: The 4 Advanced ML Components & Insights

### Component A: Causal Uplift Modeling (T-Learner Causal ML)

_Module: [`agent/uplift_model.py`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/agent/uplift_model.py)_

**The Problem**: A customer with a momentary 2-second bank timeout might retry 30 seconds later on their own. Intervening on them burns retry budget, sends redundant notifications, and falsely claims credit for organic revenue.

**The Solution**: A Two-Model **T-Learner** (Causal Machine Learning):

- **$\mu_1(x)$**: Classifier trained on treated subset (intervention applied) $\rightarrow P(\text{recovery} \mid \text{treated}, x)$
- **$\mu_0(x)$**: Classifier trained on control subset (no intervention) $\rightarrow P(\text{self-recovery} \mid \text{control}, x)$
- **Estimated Uplift**: $\tau(x) = \mu_1(x) - \mu_0(x)$

#### Empirical Validation on Held-Out Test Data:

- **Pearson Correlation (Estimated vs Ground-Truth Uplift)**: **`r = 0.5266`** ($p = 8.35 \times 10^{-23}$)
- **Overall Mean Estimated Uplift**: **+45.53%** vs **+35.69%** true baseline lift.

| Category        | Test Count | Estimated Uplift | True Uplift | Baseline $P_0$ (Self-Rec) | Treated $P_1$ (Recovery) | Causal Insight                                                 |
| --------------- | ---------- | ---------------- | ----------- | ------------------------- | ------------------------ | -------------------------------------------------------------- |
| `change_method` | 37         | **62.43%**       | 57.86%      | 6.92%                     | 69.36%                   | High uplift: customers rarely change cards without a nudge.    |
| `user_error`    | 39         | **65.67%**       | 45.33%      | 9.53%                     | 75.20%                   | High uplift: re-prompting CVV/OTP drives immediate resolution. |
| `retry_later`   | 94         | **49.19%**       | 39.91%      | 6.02%                     | 55.21%                   | Moderate uplift: requires cooldown for salary/funds deposit.   |
| `smart_retry`   | 120        | **34.66%**       | 25.07%      | **25.13%**                | 59.79%                   | Noticeable organic self-recovery: customer retries often work. |
| `escalate`      | 10         | **0.43%**        | 3.70%       | 4.17%                     | 4.60%                    | Zero uplift: autonomous intervention has no causal benefit.    |

#### The Net-Value Trade-off & Value Proposition:
> **Precision & Experience Over Gross Windfall**: Adding the uplift gate ($\ge 0.05$) is **essentially net-neutral in aggregate rupees** (-₹31,200 / -0.38% delta on ₹8.1M net value), because avoiding ₹362,308 in wasted retry spend on failures is balanced by ₹393,508 in forgone gross attempts that might have succeeded.
> 
> **Why deploy it?** Because its true value is **touchpoint precision and customer experience**: it prevents **47 unnecessary notification and retry spam events** on customers who self-recover organically, raising the recovery rate *of attempted interventions* from **69.30% to 69.95%**. It trades a negligible financial fraction (-0.38%) for a cleaner, higher-trust merchant brand touchpoint.

> **Calibration Bias Disclosure & Honest Causal Caveat**:
>
> 1. **Calibration Bias**: The T-Learner overestimates true mean uplift by roughly 10 percentage points on average (+45.53% estimated vs +35.69% true). The moderate correlation ($r = 0.53$) confirms that the model's **relative rank-ordering is statistically meaningful for threshold gating ($\ge 0.05$)**, but raw individual uplift scores should not be treated as perfectly calibrated absolute probabilities.
> 2. **Fundamental Causal Unobservability**: Ground-truth individual treatment effect is fundamentally unobservable in live production (you cannot observe both outcomes simultaneously for the same payment). Validating correlation on randomized synthetic holdouts confirms that the estimation mathematics, feature pipeline, and gating architecture are sound before deploying live A/B experiments.

---

### Component B: Time-Series Outage Forecasting & Degradation Monitoring

_Module: [`agent/degradation_agent.py`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/agent/degradation_agent.py)_

**The Problem**: When an issuer bank (e.g. HDFC card gateway) experiences a systemic outage, per-transaction retry policies fail repeatedly, spamming customers and degrading gateway reputation.

**The Solution**: Real-time time-series anomaly detection tracking hourly failure rates across 30 days (10,800 channel-hours):

1. **Seasonal Baseline**: Computes expected failure rate $\mu$ and variance $\sigma$ per `(bank, method, hour_of_day, is_weekend)` bucket.
2. **Z-Score Anomaly Engine**: Flags deviations where $z = \frac{\text{Observed} - \mu}{\sigma} \ge 3.0\sigma$.
3. **Financial Impact Assessment**: Quantifies excess failed transactions $\times$ average ticket size.

#### Validation Against Injected Outages:

- **Outage Recall**: **100.0%** (3/3 systemic multi-hour outages detected).
- **False Positive Rate on Normal Windows**: **0.06%** (virtually zero false alarms).

```
[OUTAGE INCIDENT #1] HDFC CARD Outage — Day 8 (14:00 - 20:00, 7 hrs)
  ├── Peak Failure Rate: 44.9% (Normal Baseline: 5.9%)
  ├── Anomaly Severity: 4.47 sigma
  └── Excess Failed Payments: 777 | Financial Impact: Rs. 2,487,659

[OUTAGE INCIDENT #2] SBI NETBANKING Outage — Day 15 (02:00 - 06:00, 5 hrs)
  ├── Peak Failure Rate: 58.6% (Normal Baseline: 8.4%)
  ├── Anomaly Severity: 4.47 sigma
  └── Excess Failed Payments: 73 | Financial Impact: Rs. 633,117

[OUTAGE INCIDENT #3] ICICI UPI Outage — Day 22 (10:00 - 13:00, 4 hrs)
  ├── Peak Failure Rate: 32.2% (Normal Baseline: 4.9%)
  ├── Anomaly Severity: 4.45 sigma
  └── Excess Failed Payments: 413 | Financial Impact: Rs. 381,847
```

_Surfaced dynamically on the live dashboard (`/`) and API (`/api/degradation-alerts`)._

> **Honest Caveat on Time-Series Outages**: The 3 multi-hour outage incidents detected in this benchmark are the exact outage windows injected into the synthetic 30-day time-series by `data/generate_timeseries.py`. This verifies that the rolling seasonal baseline, Z-score thresholding ($3.0\sigma$), and financial loss attribution calculations execute correctly on a known ground truth — not that the model has been evaluated against a production bank streaming feed.

---

### Component C: Contextual Bandit for Dynamic Retry Timing

_Module: [`agent/retry_bandit.py`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/agent/retry_bandit.py)_

**The Problem**: Static retry cooldowns (e.g. always retry after 1 minute) fail because different failure categories have different temporal physics. Insufficient funds needs 24 hours (for salary/daily balance credits), while timeouts need immediate backoff.

**The Solution**: A Beta-Bernoulli **Thompson Sampling Multi-Armed Bandit** exploring 5 discrete cooldown arms (`1 min`, `15 min`, `1 hr`, `6 hrs`, `24 hrs`).

#### 5,000-Episode Simulation Convergence Results (Fair Comparison):

| Category                           | Optimal Arm (Ground Truth) | Bandit Selected Arm  | Final Arm Pull Rate | vs Naive 1-Min Baseline | vs Taxonomy Default Cooldown            |
| ---------------------------------- | -------------------------- | -------------------- | ------------------- | ----------------------- | --------------------------------------- |
| `retry_later` (insufficient funds) | **Arm 4 (24 hours)**       | **Arm 4 (24 hours)** | **99.7%**           | **+409.7%**             | **+-0.9%** (Confirms 24h heuristic)     |
| `smart_retry` (gateway latency)    | **Arm 1 (15 min)**         | **Arm 1 (15 min)**   | **99.7%**           | **+77.7%**              | **+78.8%** (Beats immediate 1m backoff) |
| `change_method` (expired card)     | **Arm 3 (6 hours)**        | **Arm 3 (6 hours)**  | **99.6%**           | **+619.5%**             | _N/A (Taxonomy skips auto-retry)_       |
| `user_error` (wrong CVV/OTP)       | **Arm 2 (1 hour)**         | **Arm 2 (1 hour)**   | **99.8%**           | **+205.8%**             | _N/A (Taxonomy skips auto-retry)_       |

**Fair Comparison Breakdown**:

1. **Vs. Naive 1-Minute Baseline**: Shows massive lift (+77% to +619%), demonstrating why flat retry timers are disastrous.
2. **Vs. Taxonomy Hand-Set Heuristic**:
   - For `retry_later`, the hand-set default was already 24h. The bandit converged to 24h, demonstrating **0% delta** — an honest confirmation that the bandit validates domain expertise rather than artificially beating a straw man.
   - For `smart_retry`, the hand-set default was 0h (immediate retry). The bandit discovered that a 15-minute delay yields **+78.8% more recoveries** by allowing transient network congestion to clear.
   - For `change_method` and `user_error`, the taxonomy deliberately sets `auto_retry_allowed=False` (prompting method/re-prompting customer instead). The bandit simulator evaluates optimal timing windows for customer prompts (6h and 1h respectively).

_Generated convergence comparison plot: [`bandit_convergence.png`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/bandit_convergence.png)._

> **Honest Caveat on Bandit Optimization**: The "optimal" arm for each failure category is the maximum reward probability hard-coded into `GROUND_TRUTH_REWARD_DIST` in the simulator environment. The simulation proves that Thompson Sampling successfully explores, exploits, and converges with 99%+ precision to the true underlying peak — not that 24 hours is an empirically proven optimum for real live Razorpay merchant traffic.

---

### Component D: Strategic Cohort Analyst (Unsupervised Clustering)

_Module: [`agent/cohort_analyst.py`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/agent/cohort_analyst.py)_

**The Problem**: High-level failure metrics hide where the money is. Merchants need to know which multi-dimensional transaction segments account for the bulk of unrecovered revenue.

**The Solution**: Unsupervised **Gaussian Mixture Models (GMM)** + **Principal Component Analysis (PCA)** clustering on standardized continuous signals and one-hot categorical features.

#### Discovered Cohort Opportunity Ranking (n=1200 records, ₹3.76 Crore):

| Rank   | Discovered Transaction Archetype                      | Size | Amount at Risk      | Current Rec% | Recoverable Opportunity | Strategic Action                                                    |
| ------ | ----------------------------------------------------- | ---- | ------------------- | ------------ | ----------------------- | ------------------------------------------------------------------- |
| **#1** | **High-Ticket Enterprise (UPI) - First-Attempt Drop** | 227  | ₹22,725,592 (60.5%) | 53.3%        | **₹7,203,111**          | Deploy dedicated account manager nudge + high-value UPI link        |
| **#2** | **High-Ticket Enterprise (CARD) - Retry Fatigue**     | 71   | ₹7,066,674 (18.8%)  | 46.5%        | **₹2,722,162**          | Restrict aggressive retries; switch to corporate card checkout link |
| **#3** | **Mid-Market (UPI) - First-Attempt Drop**             | 419  | ₹5,773,071 (15.4%)  | 59.0%        | **₹1,503,891**          | Autonomous Smart-Retry with 15m backoff                             |
| **#4** | **Mid-Market (UPI) - Repeated Retry Fatigue**         | 181  | ₹1,084,358 (2.9%)   | 48.1%        | **₹400,493**            | Prompt alternative instrument (Netbanking / Card)                   |
| **#5** | **Mid-Market (CARD) - First-Attempt Drop**            | 302  | ₹919,925 (2.5%)     | 55.3%        | **₹273,236**            | Automated SMS / WhatsApp CVV re-prompt                              |

> **Non-Triviality Verification**: 5 of 5 discovered clusters cross taxonomy boundaries (discovering emergent patterns across ticket size, retry history, and hour-of-day rather than copying taxonomy labels).
>
> _Top 2 Enterprise cohorts account for **>79% of total recoverable revenue (₹9.92M)**._

_Generated latent space scatter projection: [`cohort_scatter.png`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/cohort_scatter.png) and full strategic report: [`cohort_report.txt`](file:///c:/Users/Acer/Desktop/razorpay-recovery-agent/cohort_report.txt)._

---

## 4. Full Batch Results: Baseline vs Tuned vs Uplift-Refined

Evaluated across **n = 1,200 synthetic records** representing **₹3.76 Crore** at risk:

| Metric                                       | Naive Baseline Policy ($P \ge 0.40$, No Uplift) | Tuned Stopping Rule ($P \ge 0.47$, No Uplift) | Tuned + Uplift Refinement ($P \ge 0.47$, Uplift Gate $\ge 0.05$) | Key Impact                                              |
| -------------------------------------------- | ----------------------------------------------- | --------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------- |
| **Total Amount at Risk**                     | ₹37,569,620                                     | ₹37,569,620                                   | ₹37,569,620                                                      | Real-schema synthetic batch                             |
| **Total Handled Records**                    | 1,200                                           | 1,200                                         | 1,200                                                            | 100% processed with audit log                           |
| **Autonomous Retries Attempted**             | 869 (72.4%)                                     | 783 (65.3%)                                   | **736 (61.3%)**                                                  | Gated, high-confidence attempts                         |
| **Skipped Low-Uplift (Self-Recovery)**       | 0 (0.0%)                                        | 0 (0.0%)                                      | **47 (3.9%)**                                                    | **47 wasted notifications eliminated**                  |
| **Escalated to Human Review**                | 331 (27.6%)                                     | 417 (34.7%)                                   | **417 (34.7%)**                                                  | Risk & compliance stops intact                          |
| **Total Amount Recovered**                   | ₹15,145,945                                     | ₹14,588,655                                   | **₹14,195,147**                                                  | Realized high-confidence recoveries                     |
| **Wasted Spend on Failed Retries**           | ₹8,687,605                                      | ₹6,461,592                                    | **₹6,099,284**                                                   | **-29.8% reduction in wasted spend** (-₹2.59M vs Naive) |
| **Net Value (Recovered − Wasted)**           | ₹6,458,340                                      | ₹8,127,063                                    | **₹8,095,863**                                                   | **+₹1,637,523 (+25.36%) vs Naive Baseline**             |
| **Recovery Rate _of Attempted Cases_**       | 63.55%                                          | 69.30%                                        | **69.95%**                                                       | **+6.4pp precision on customer touchpoints**            |

### Honest Two-Stage Performance Breakdown:

1. **Stage 1: Threshold Tuning ($0.40 \rightarrow 0.47$) is where the financial jump happens**:
   - Raising the cutoff eliminates low-probability gambles, reducing wasted spend from ₹8.69M to ₹6.46M.
   - **Net Value increases by +₹1,668,723 (+25.84%)**.
2. **Stage 2: Uplift Refinement Layer is where the precision & customer experience jump happens**:
   - Filtering self-recoveries saves ₹362,308 in wasted retry spend on failures, while foregoing ₹393,508 in gross recovery attempts.
   - **Financial impact is roughly net-neutral (-₹31,200 / -0.38% delta)**.
   - **Customer experience gain is distinct**: eliminates 47 unnecessary notifications to users who resolve independently and pushes attempt precision to **69.95%**.

### Verified Partition Invariant:

$$\text{Attempted (736)} + \text{Escalated (417)} + \text{Skipped Low-Uplift (47)} = \mathbf{1200} \text{ total records}$$

---

## 5. End-to-End System Architecture

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

## 6. Live Razorpay Test-Mode Demo Setup

### Step 1: Clone & Setup

```bash
git clone https://github.com/ayushcode001/razorpay-recovery-agent.git
cd razorpay-recovery-agent

python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### Step 2: Start the Webhook & Dashboard Server

```bash
python webhook/server.py
```

- **Live Dashboard**: `http://localhost:5000/` (Real-time audit trail + Systemic Degradation Outage Monitor)
- **Interactive Checkout Demo**: `http://localhost:5000/checkout`
- **Live Webhook Endpoint**: `http://localhost:5000/webhook/razorpay`

### Step 3: Trigger Live Payment Failures On-Camera

1. Open `http://localhost:5000/checkout`.
2. Click **⚡ Pay ₹1,299 (Test Mode)**.
3. Enter test card credentials (`4111 2222 3333 4444`, CVV `123`).
4. On Razorpay's mock bank authorization page, click **Failure**.
5. The Flask server receives `payment.failed` $\rightarrow$ verifies HMAC $\rightarrow$ evaluates Taxonomy, Success Predictor & Uplift Gate $\rightarrow$ generates recovery Payment Link $\rightarrow$ logs decision into `audit_logs/audit_trail.json` in real time.

---

## 7. How to Run All Validation & ML Modules

```bash
# 1. Run Automated End-to-End Webhook & Pipeline Integration Tests
python tests/test_webhook_flow.py

# 2. Run Causal Uplift T-Learner Validation (Evaluates r correlation on held-out test split)
python agent/uplift_model.py

# 3. Run Time-Series Outage Degradation Forecaster (Evaluates recall on 10,800 channel-hours)
python agent/degradation_agent.py

# 4. Run Thompson Sampling Contextual Bandit Simulation (Generates bandit_convergence.png)
python agent/retry_bandit.py 5000

# 5. Run Strategic Cohort Analyst (Generates cohort_scatter.png & cohort_report.txt)
python agent/cohort_analyst.py

# 6. Run Batch Orchestrator over Full Dataset (Prints Net Value & uplift-attributable delta)
python agent/orchestrator.py data/synthetic_failed_payments.json
```

---

## 8. Failure Recovery & Edge-Case Engineering Story

1. **The "Fake ML" Trap**:
   - _Problem_: Initial temptation was training an NLP classifier to parse raw error strings.
   - _Fix_: Razorpay webhooks already provide `error_reason` cleanly. We focused ML on genuine unknowns: $P(\text{Success} \mid \text{Context})$, Causal Uplift, Dynamic Delay Bandits, and Macro Outages.
2. **The Causal Self-Recovery Trap**:
   - _Problem_: Success predictors take credit for organic self-recoveries (e.g. customer immediate retries).
   - _Fix_: Added a T-Learner uplift refinement layer ($\mu_1 - \mu_0$) with a $\ge 0.05$ uplift gate. This eliminates 47 unnecessary notifications, boosting attempt precision from 69.30% to 69.95% while remaining essentially net-neutral in rupees (-0.38% delta).
3. **The Systemic Outage Blindspot**:
   - _Problem_: When an entire issuer bank goes down, transaction-level retries keep burning attempts fruitlessly.
   - _Fix_: Created the Degradation Agent with a seasonal $3.0\sigma$ Z-score alert engine that catches 100% of outages and surfaces real-time ₹ impact.
4. **Webhook Schema Nesting**:
   - _Problem_: Razorpay webhook payloads nest granular error reasons inside `payload.payment.entity.error_reason`.
   - _Fix_: Built an adapter layer in `webhook/server.py` that normalizes webhook payloads while enforcing HMAC-SHA256 signature verification.

---

## 9. Immutable Audit Trail & Honest Exceptions

Every action taken or skipped is logged to `audit_logs/audit_trail.json`:

```json
{
  "timestamp": "2026-08-30T18:24:41.102Z",
  "payment_id": "pay_live_test_42911",
  "amount": 1299.0,
  "error_code": "bank_technical_error",
  "category": "smart_retry",
  "action": "retry_with_backoff",
  "attempted": true,
  "predicted_success_prob": 0.628,
  "estimated_uplift": 0.347,
  "reason": "error_code='bank_technical_error' -> category='smart_retry'. Predicted success probability 0.63 clears threshold (0.47), estimated uplift=0.35 and retry budget available. Executing 'retry_with_backoff'."
}
```

No black boxes. No silent drops. Every single rupee accounted for.
