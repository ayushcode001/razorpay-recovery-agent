// Landing page: /
// Sections: Hero, Problem, Solution, Why, How (Architecture), Results (stats + charts), Footer
// Rule: Real content carries visual weight. No filler text.

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { StatCard } from '@/components/StatCard'
import { HowSection } from '@/components/HowSection'
import { CohortScatterChart } from '@/components/CohortScatterChart'
import { BanditConvergenceChart } from '@/components/BanditConvergenceChart'
import { Footer } from '@/components/Footer'
import { FadeIn } from '@/components/FadeIn'
import { useCohortReport, useBanditResults, type CohortSummary } from '@/hooks/useApi'

const GITHUB = 'https://github.com/ayushcode001/razorpay-recovery-agent'

const RESULT_STATS = [
  { label: 'Net Value (Recovered − Wasted)', value: '₹80.96L', color: 'navy' as const },
  { label: 'Recovery Rate of Attempted', value: '69.95%', color: 'navy' as const },
  { label: 'Wasted Spend Reduction', value: '−29.8%', color: 'navy' as const },
  { label: 'vs Naive Baseline Net Value', value: '+₹16.38L', color: 'primary' as const },
]

export function Landing() {
  const cohort = useCohortReport()
  const bandit = useBanditResults()
  const [cohortView, setCohortView] = useState<'interactive' | 'image'>('interactive')
  const [banditView, setBanditView] = useState<'interactive' | 'image'>('interactive')

  return (
    <div className="bg-white text-navy min-h-screen selection:bg-primary-light selection:text-primary-dark">

      {/* ── HERO ── */}
      <section className="py-28 md:py-36 border-b border-surface-border relative bg-white subtle-grid overflow-hidden">
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn delay={0.05} direction="up">
            <div className="mb-6">
              <span className="inline-block text-xs text-muted border border-surface-border px-3 py-1 rounded-none tracking-wide">
                Razorpay AI Buildathon · Track 03
              </span>
            </div>
          </FadeIn>
          <FadeIn delay={0.1} direction="up">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight text-navy leading-[1.1] mb-6">
              Autonomous Payment Failure <span className="text-primary">Recovery</span> Agent
            </h1>
          </FadeIn>
          <FadeIn delay={0.15} direction="up">
            <p className="text-base text-muted leading-relaxed mb-8 max-w-2xl font-normal">
              A production agent that converts failed transactions into recovered revenue using a
              two-stage causal uplift engine, real-time banking degradation monitoring, contextual
              multi-armed bandits, and human-in-the-loop drift governance.
            </p>
          </FadeIn>
          <FadeIn delay={0.2} direction="up">
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-none bg-primary text-white font-semibold text-sm hover:bg-primary-dark transition-colors duration-150"
              >
                Open Live Dashboard
                <span aria-hidden="true">→</span>
              </Link>
              <a
                href={GITHUB}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-none bg-transparent border border-surface-border text-navy font-semibold text-sm hover:border-surface-border-dark transition-colors duration-150"
              >
                View on GitHub
              </a>
            </div>
          </FadeIn>
          <FadeIn delay={0.25} direction="up">
            <div className="mt-16 flex flex-col items-start gap-1" aria-hidden="true">
              <div className="w-px h-8 bg-surface-border" />
              <div className="w-1.5 h-1.5 rounded-full bg-muted-light" />
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── PROBLEM ── */}
      <section id="problem" className="section-pad border-b border-surface-border bg-surface-muted relative overflow-hidden">
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn direction="up">
            <div className="mb-2">
              <span className="text-xs uppercase tracking-wider text-primary font-semibold">
                01 · The Problem
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-semibold text-navy tracking-tight mb-6">
              The Indiscriminate Retry Trap
            </h2>
            <div className="text-muted space-y-4 text-base leading-relaxed">
              <p>
                When a payment fails in Indian fintech, merchants default to brute-force retry loops or
                generic SMS blast notifications. This destroys margins through gateway fees on hopeless
                retries and annoys customers who were already resolving the failure themselves.
              </p>
              <p>
                Rule-based systems cannot adapt to issuer degradation windows. If HDFC Netbanking failure
                rate spikes from 8% to 62%, retrying through HDFC in the next 15 minutes is burning money.
                A recovery agent must know when <em className="text-navy not-italic font-semibold">not</em> to retry.
              </p>
              <p>
                Standard ML models predict only probability of success, not uplift. A model with
                a static threshold grows stale. Most systems have no mechanism to detect this.
              </p>
              <p>
                Brute-force retry also ignores causality. A customer whose transaction failed due to a
                transient network error who then self-recovered does not need your recovery SMS.
                Sending it wastes money and degrades their experience.
              </p>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── SOLUTION ── */}
      <section id="solution" className="section-pad border-b border-surface-border bg-white relative overflow-hidden">
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn direction="up">
            <div className="mb-2">
              <span className="text-xs uppercase tracking-wider text-primary font-semibold">
                02 · The Solution
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-semibold text-navy tracking-tight mb-4">
              Autonomous, bounded recovery in a continuous loop
            </h2>
            <p className="text-base text-muted leading-relaxed mb-8 max-w-3xl">
              An intelligent recovery loop across <span className="font-semibold text-navy">Detect → Decide → Act → Audit</span>. Instead of indiscriminate retries, the agent evaluates real-time banking telemetry, isolates causal uplift, and executes bounded recovery actions with guaranteed human governance.
            </p>
          </FadeIn>

          <div className="grid md:grid-cols-2 gap-4">
            <FadeIn delay={0.05} direction="up">
              <div className="card-interactive h-full bg-surface-muted border border-surface-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-primary">01</span>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted">Detect · Instant Ingestion</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">Webhook Ingestion & Bank Outage Telemetry</h3>
                <p className="text-sm text-muted leading-relaxed">
                  Ingests failed payment events under 100ms and cross-references issuer error spikes with a real-time seasonal Z-score monitor. If HDFC or SBI degrades, retries halt immediately.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.1} direction="up">
              <div className="card-interactive h-full bg-surface-muted border border-surface-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-primary">02</span>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted">Decide · Deterministic Gates</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">Taxonomy Safety Layer First</h3>
                <p className="text-sm text-muted leading-relaxed">
                  Fraud flags, expired cards, and compliance violations hit hard deterministic stops before ML touches them. Models are never allowed to override regulatory boundaries.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.15} direction="up">
              <div className="card-interactive h-full bg-surface-muted border border-surface-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-primary">03</span>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted">Act · Targeted Causal ML</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">ML Only Where Uncertainty Exists</h3>
                <p className="text-sm text-muted leading-relaxed">
                  A T-Learner estimates incremental uplift so retries are only spent when the agent causes the recovery. Thompson Sampling dynamically learns optimal cooldown periods per error category.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.2} direction="up">
              <div className="card-interactive h-full bg-surface-muted border border-surface-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-primary">04</span>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted">Audit · Immutable Governance</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">Human Sign-off on Policy Shifts</h3>
                <p className="text-sm text-muted leading-relaxed">
                  Every decision is recorded in an immutable PostgreSQL ledger. Drift-detection agents monitor model decay and propose threshold adjustments that require explicit human approval to activate.
                </p>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ── WHY THIS APPROACH ── */}
      <section id="why" className="section-pad bg-surface-muted border-b border-surface-border relative overflow-hidden">
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn direction="up">
            <div className="mb-2">
              <span className="text-xs uppercase tracking-wider text-primary font-semibold">
                03 · Architectural Principles
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-semibold text-navy tracking-tight mb-6">
              Why This Approach
            </h2>
          </FadeIn>
          <div className="grid md:grid-cols-2 gap-4">
            <FadeIn delay={0.05} direction="up">
              <div className="card-interactive h-full bg-white border border-surface-border">
                <div className="text-xs uppercase tracking-wider text-primary mb-2 font-semibold">Causal Uplift, Not Correlation</div>
                <p className="text-sm text-muted leading-relaxed">
                  A T-Learner separates agent-caused recoveries from organic self-recovery.
                  This prevents wasting retry budget on customers who would have recovered anyway,
                  and is the architectural choice that unlocks precision without sacrificing recall.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.1} direction="up">
              <div className="card-interactive h-full bg-white border border-surface-border">
                <div className="text-xs uppercase tracking-wider text-primary mb-2 font-semibold">Drift-Gated Governance</div>
                <p className="text-sm text-muted leading-relaxed">
                  The drift-check agent evaluates model performance against fresh data and proposes
                  threshold updates, but never auto-applies them. Every policy change requires
                  explicit human approval. This is not a limitation; it's the design.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.15} direction="up">
              <div className="card-interactive h-full bg-white border border-surface-border">
                <div className="text-xs uppercase tracking-wider text-primary mb-2 font-semibold">Deterministic Safety Gates</div>
                <p className="text-sm text-muted leading-relaxed">
                  Risk, compliance, and fraud-flagged transactions are routed through a deterministic
                  taxonomy layer before any ML model sees them. No probability score can override a
                  compliance stop.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.2} direction="up">
              <div className="card-interactive h-full bg-white border border-surface-border">
                <div className="text-xs uppercase tracking-wider text-primary mb-2 font-semibold">Full Audit Trail</div>
                <p className="text-sm text-muted leading-relaxed">
                  Every decision (attempted, skipped, escalated) is logged with the predicted
                  success probability, estimated uplift, and the reason. The system is inspectable
                  at the row level by a human or the Gemini copilot.
                </p>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS (Architecture) ── */}
      <HowSection />

      {/* ── RESULTS ── */}
      <section id="results" className="section-pad bg-white border-b border-surface-border relative overflow-hidden">
        <div className="container-page relative z-10">
          <FadeIn direction="up">
            <div className="mb-2">
              <span className="font-mono text-xs uppercase tracking-wider text-primary font-semibold">
                05 · Quantitative Validation
              </span>
            </div>
            <h2 className="text-2xl md:text-3xl font-semibold text-navy tracking-tight mb-8">
              Live Results & Telemetry
            </h2>
          </FadeIn>

          {/* Stat grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
            {RESULT_STATS.map((s, idx) => (
              <FadeIn key={s.label} delay={idx * 0.08} direction="up">
                <StatCard {...s} dark={false} />
              </FadeIn>
            ))}
          </div>

          {/* Stage breakdown */}
          <FadeIn delay={0.15} direction="up">
            <div className="card-interactive mb-10 bg-surface-muted border border-surface-border">
              <h3 className="text-base font-semibold text-navy mb-4">
                Two-Stage Uplift Performance
              </h3>
              <div className="grid md:grid-cols-2 gap-6 text-sm">
                <div>
                  <div className="font-semibold text-navy mb-1">Stage 1: Threshold Tuning (0.40 → 0.47)</div>
                  <p className="text-muted leading-relaxed">
                    Raising the decision threshold eliminates low-probability gambles.
                    Wasted spend drops from ₹86.88L to ₹64.62L.
                    <span className="text-navy block mt-1 font-semibold">Net value +₹16.69L (+25.84%)</span>
                  </p>
                </div>
                <div>
                  <div className="font-semibold text-navy mb-1">Stage 2: Uplift Refinement Layer</div>
                  <p className="text-muted leading-relaxed">
                    Filtering self-recoveries saves ₹3.62L in wasted spend, foregoing ₹3.94L in gross
                    recovery. Financial impact: net-neutral (−0.38%).
                    <span className="text-navy block mt-1 font-semibold">Customer gain: −47 unnecessary touchpoints</span>
                  </p>
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Charts */}
          <div className="space-y-8">
            {/* Cohort Scatter */}
            <FadeIn delay={0.1} direction="up">
              <div className="card-interactive bg-white border border-surface-border">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-navy mb-0.5">Discovered Transaction Cohorts</h3>
                    <div className="text-xs text-muted">
                      PCA latent space · Unsupervised GMM clustering · Live from /api/v1/cohort-report
                    </div>
                  </div>
                  <div className="inline-flex rounded-none p-0.5 bg-surface-subtle border border-surface-border self-start sm:self-auto text-xs">
                    <button
                      onClick={() => setCohortView('interactive')}
                      className={`px-3 py-1 rounded-none font-semibold transition-colors duration-150 ${cohortView === 'interactive' ? 'bg-white text-navy border border-surface-border' : 'text-muted hover:text-navy'}`}
                    >
                      Interactive
                    </button>
                    <button
                      onClick={() => setCohortView('image')}
                      className={`px-3 py-1 rounded-none font-semibold transition-colors duration-150 ${cohortView === 'image' ? 'bg-white text-navy border border-surface-border' : 'text-muted hover:text-navy'}`}
                    >
                      Stats Plot (PNG)
                    </button>
                  </div>
                </div>

                {cohortView === 'interactive' ? (
                  <>
                    <CohortScatterChart
                      cohorts={cohort.data?.cohorts ?? []}
                      scatterByCluster={cohort.data?.scatter_by_cluster ?? {}}
                      isLoading={cohort.isLoading}
                    />
                    {cohort.data && (
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-3">
                        {cohort.data.cohorts.slice(0, 3).map((c: CohortSummary, i: number) => (
                          <div key={i} className="bg-surface-muted border border-surface-border rounded-none p-3 text-xs">
                            <div className="font-semibold text-navy text-xs leading-tight">{c.archetype_name}</div>
                            <div className="text-muted mt-1">At risk: <span className="font-semibold text-navy">₹{(c.total_at_risk_inr / 100000).toFixed(1)}L</span></div>
                            <div className="text-muted">Recovery: <span className="font-semibold text-navy">{(c.current_recovery_rate * 100).toFixed(1)}%</span></div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="space-y-2">
                    <div className="overflow-hidden rounded-none border border-surface-border bg-white">
                      <img
                        src="/cohort_scatter.png"
                        alt="Discovered Transaction Cohorts PCA Latent Space Scatter"
                        className="w-full h-auto object-contain max-h-[500px] mx-auto"
                      />
                    </div>
                    <p className="text-2xs text-muted text-center">
                      High-resolution projection generated by Python Latent PCA & GMM pipeline
                    </p>
                  </div>
                )}
              </div>
            </FadeIn>

            {/* Bandit Convergence */}
            <FadeIn delay={0.15} direction="up">
              <div className="card-interactive bg-white border border-surface-border">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-navy mb-0.5">Contextual Retry Bandit Convergence</h3>
                    <div className="text-xs text-muted">
                      Thompson Sampling vs baselines · 1,000 episodes · Live from /api/v1/bandit-results
                    </div>
                  </div>
                  <div className="inline-flex rounded-none p-0.5 bg-surface-subtle border border-surface-border self-start sm:self-auto text-xs">
                    <button
                      onClick={() => setBanditView('interactive')}
                      className={`px-3 py-1 rounded-none font-semibold transition-colors duration-150 ${banditView === 'interactive' ? 'bg-white text-navy border border-surface-border' : 'text-muted hover:text-navy'}`}
                    >
                      Interactive
                    </button>
                    <button
                      onClick={() => setBanditView('image')}
                      className={`px-3 py-1 rounded-none font-semibold transition-colors duration-150 ${banditView === 'image' ? 'bg-white text-navy border border-surface-border' : 'text-muted hover:text-navy'}`}
                    >
                      Stats Plot (PNG)
                    </button>
                  </div>
                </div>

                {banditView === 'interactive' ? (
                  <BanditConvergenceChart
                    categories={bandit.data?.categories ?? []}
                    results={bandit.data?.results ?? {}}
                    isLoading={bandit.isLoading}
                  />
                ) : (
                  <div className="space-y-2">
                    <div className="overflow-hidden rounded-none border border-surface-border bg-white">
                      <img
                        src="/bandit_convergence.png"
                        alt="Contextual Retry Bandit Convergence Comparison"
                        className="w-full h-auto object-contain max-h-[500px] mx-auto"
                      />
                    </div>
                    <p className="text-2xs text-muted text-center">
                      High-resolution convergence plot generated across 1,000 Thompson Sampling episodes
                    </p>
                  </div>
                )}
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
