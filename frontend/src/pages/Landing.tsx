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
import heroDarkBg from '@/assets/hero_dark.jpg'

const GITHUB = 'https://github.com/ayushcode001/razorpay-recovery-agent'

const RESULT_STATS = [
  { label: 'Net Value (Recovered − Wasted)', value: '₹80.96L', color: 'success' as const },
  { label: 'Recovery Rate of Attempted', value: '69.95%', color: 'primary' as const },
  { label: 'Wasted Spend Reduction', value: '−29.8%', color: 'warning' as const },
  { label: 'vs Naive Baseline Net Value', value: '+₹16.38L', color: 'success' as const },
]

export function Landing() {
  const cohort = useCohortReport()
  const bandit = useBanditResults()
  const [cohortView, setCohortView] = useState<'interactive' | 'image'>('interactive')
  const [banditView, setBanditView] = useState<'interactive' | 'image'>('interactive')

  return (
    <div className="bg-white text-navy min-h-screen selection:bg-primary-light selection:text-primary-dark">

      {/* ── HERO ── */}
      <section
        className="section-pad border-b border-surface-border relative bg-cover bg-center bg-no-repeat overflow-hidden"
        style={{ backgroundImage: `url(${heroDarkBg})` }}
      >
        {/* Directional light scrim: dense on text side, atmospheric reveal toward network nodes */}
        <div className="absolute inset-0 bg-gradient-to-r from-white via-white/95 to-white/60 pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-b from-white/70 via-transparent to-white pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_80%_40%,rgba(37,99,235,0.08),transparent)] pointer-events-none" />
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn delay={0.05} direction="up">
            <div className="mb-6">
              <span className="inline-block font-mono text-xs text-primary bg-primary-50 border border-primary-100 px-3 py-1 rounded-none tracking-wide shadow-xs font-semibold">
                Razorpay AI Buildathon · Track 03
              </span>
            </div>
          </FadeIn>
          <FadeIn delay={0.1} direction="up">
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-navy leading-[1.08] mb-6">
              Autonomous Payment Failure <span className="text-primary">Recovery</span> Agent
            </h1>
          </FadeIn>
          <FadeIn delay={0.15} direction="up">
            <p className="text-lg md:text-xl text-muted leading-relaxed mb-8 max-w-3xl font-normal">
              A production agent that converts failed transactions into recovered revenue using a
              two-stage causal uplift engine, real-time banking degradation monitoring, contextual
              multi-armed bandits, and human-in-the-loop drift governance.
            </p>
          </FadeIn>
          <FadeIn delay={0.2} direction="up">
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-none bg-primary text-white font-semibold text-sm hover:bg-primary-dark hover:shadow-md transition-all"
              >
                Open Live Dashboard
                <span aria-hidden="true">→</span>
              </Link>
              <a
                href={GITHUB}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-none bg-white border border-surface-border text-navy font-medium text-sm hover:bg-surface-muted hover:border-surface-border-dark transition-all shadow-xs"
              >
                View on GitHub
              </a>
            </div>
          </FadeIn>
          <FadeIn delay={0.25} direction="up">
            <div className="mt-14 pt-8 border-t border-surface-border flex items-center gap-3 text-xs font-mono text-muted tracking-widest uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
              <span>Scroll to explore architecture</span>
              <span className="text-primary">↓</span>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── PROBLEM ── */}
      <section id="problem" className="section-pad border-b border-surface-border bg-surface-muted relative overflow-hidden">
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn direction="up">
            <div className="mb-2">
              <span className="font-mono text-xs uppercase tracking-wider text-primary font-semibold">
                01 · The Problem
              </span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-navy tracking-tight mb-6">
              The Indiscriminate Retry Trap
            </h2>
            <div className="text-muted space-y-4 text-base md:text-lg leading-relaxed">
              <p>
                When a payment fails in Indian fintech, merchants default to brute-force retry loops or
                generic SMS blast notifications. This destroys margins through gateway fees on hopeless
                retries and annoys customers who were already resolving the failure themselves.
              </p>
              <p>
                Rule-based systems cannot adapt to issuer degradation windows. If HDFC Netbanking failure
                rate spikes from 8% to 62%, retrying through HDFC in the next 15 minutes is burning money.
                A recovery agent must know when <em className="text-navy not-italic font-medium">not</em> to retry.
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
              <span className="font-mono text-xs uppercase tracking-wider text-primary font-semibold">
                02 · The Solution
              </span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-navy tracking-tight mb-4">
              Autonomous, bounded recovery in a continuous loop
            </h2>
            <p className="text-base md:text-lg text-muted leading-relaxed mb-8 max-w-3xl">
              An intelligent recovery loop across <span className="font-semibold text-navy">Detect → Decide → Act → Audit</span>. Instead of indiscriminate retries, the agent evaluates real-time banking telemetry, isolates causal uplift, and executes bounded recovery actions with guaranteed human governance.
            </p>
          </FadeIn>

          <div className="grid md:grid-cols-2 gap-4">
            <FadeIn delay={0.05} direction="up">
              <div className="card-interactive h-full bg-surface-muted/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-none bg-primary-50 border border-primary/20 text-primary font-mono font-bold text-xs flex items-center justify-center">
                    01
                  </span>
                  <div className="text-xs font-mono text-primary font-medium">Detect · Instant Ingestion</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">Webhook Ingestion & Bank Outage Telemetry</h3>
                <p className="text-xs md:text-sm text-muted leading-relaxed">
                  Ingests failed payment events under 100ms and cross-references issuer error spikes with a real-time seasonal Z-score monitor. If HDFC or SBI degrades, retries halt immediately.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.1} direction="up">
              <div className="card-interactive h-full bg-surface-muted/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-none bg-primary-50 border border-primary/20 text-primary font-mono font-bold text-xs flex items-center justify-center">
                    02
                  </span>
                  <div className="text-xs font-mono text-primary font-medium">Decide · Deterministic Gates</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">Taxonomy Safety Layer First</h3>
                <p className="text-xs md:text-sm text-muted leading-relaxed">
                  Fraud flags, expired cards, and compliance violations hit hard deterministic stops before ML touches them. Models are never allowed to override regulatory boundaries.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.15} direction="up">
              <div className="card-interactive h-full bg-surface-muted/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-none bg-primary-50 border border-primary/20 text-primary font-mono font-bold text-xs flex items-center justify-center">
                    03
                  </span>
                  <div className="text-xs font-mono text-primary font-medium">Act · Targeted Causal ML</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">ML Only Where Uncertainty Exists</h3>
                <p className="text-xs md:text-sm text-muted leading-relaxed">
                  A T-Learner estimates incremental uplift so retries are only spent when the agent causes the recovery. Thompson Sampling dynamically learns optimal cooldown periods per error category.
                </p>
              </div>
            </FadeIn>

            <FadeIn delay={0.2} direction="up">
              <div className="card-interactive h-full bg-surface-muted/30">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-none bg-primary-50 border border-primary/20 text-primary font-mono font-bold text-xs flex items-center justify-center">
                    04
                  </span>
                  <div className="text-xs font-mono text-primary font-medium">Audit · Immutable Governance</div>
                </div>
                <h3 className="text-base font-semibold text-navy mb-1">Human Sign-off on Policy Shifts</h3>
                <p className="text-xs md:text-sm text-muted leading-relaxed">
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
              <span className="font-mono text-xs uppercase tracking-wider text-primary font-semibold">
                03 · Architectural Principles
              </span>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-navy tracking-tight mb-6">
              Why This Approach
            </h2>
          </FadeIn>
          <div className="grid md:grid-cols-2 gap-6">
            <FadeIn delay={0.05} direction="up">
              <div className="card-interactive h-full bg-white">
                <div className="text-xs font-mono text-primary mb-2 font-semibold">Causal Uplift, Not Correlation</div>
                <p className="text-sm text-muted leading-relaxed">
                  A T-Learner separates agent-caused recoveries from organic self-recovery.
                  This prevents wasting retry budget on customers who would have recovered anyway,
                  and is the architectural choice that unlocks precision without sacrificing recall.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.1} direction="up">
              <div className="card-interactive h-full bg-white">
                <div className="text-xs font-mono text-primary mb-2 font-semibold">Drift-Gated Governance</div>
                <p className="text-sm text-muted leading-relaxed">
                  The drift-check agent evaluates model performance against fresh data and proposes
                  threshold updates, but never auto-applies them. Every policy change requires
                  explicit human approval. This is not a limitation; it's the design.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.15} direction="up">
              <div className="card-interactive h-full bg-white">
                <div className="text-xs font-mono text-primary mb-2 font-semibold">Deterministic Safety Gates</div>
                <p className="text-sm text-muted leading-relaxed">
                  Risk, compliance, and fraud-flagged transactions are routed through a deterministic
                  taxonomy layer before any ML model sees them. No probability score can override a
                  compliance stop.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.2} direction="up">
              <div className="card-interactive h-full bg-white">
                <div className="text-xs font-mono text-primary mb-2 font-semibold">Full Audit Trail</div>
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
            <h2 className="text-3xl md:text-4xl font-bold text-navy tracking-tight mb-8">
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
            <div className="card-interactive mb-10 bg-surface-muted/30">
              <h3 className="text-base md:text-lg font-semibold text-navy mb-4">
                Two-Stage Uplift Performance
              </h3>
              <div className="grid md:grid-cols-2 gap-6 text-sm">
                <div>
                  <div className="font-medium text-navy mb-1">Stage 1: Threshold Tuning (0.40 → 0.47)</div>
                  <p className="text-muted leading-relaxed">
                    Raising the decision threshold eliminates low-probability gambles.
                    Wasted spend drops from ₹86.88L to ₹64.62L.
                    <strong className="text-success block mt-1 font-semibold">Net value +₹16.69L (+25.84%)</strong>
                  </p>
                </div>
                <div>
                  <div className="font-medium text-navy mb-1">Stage 2: Uplift Refinement Layer</div>
                  <p className="text-muted leading-relaxed">
                    Filtering self-recoveries saves ₹3.62L in wasted spend, foregoing ₹3.94L in gross
                    recovery. Financial impact: net-neutral (−0.38%).
                    <strong className="text-primary block mt-1 font-semibold">Customer gain: −47 unnecessary touchpoints</strong>
                  </p>
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Charts */}
          <div className="space-y-8">
            {/* Cohort Scatter */}
            <FadeIn delay={0.1} direction="up">
              <div className="card-interactive bg-white">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-base md:text-lg font-semibold text-navy mb-0.5">Discovered Transaction Cohorts</h3>
                    <div className="text-xs text-muted">
                      PCA latent space · Unsupervised GMM clustering · Live from <span className="font-mono text-primary">/api/v1/cohort-report</span>
                    </div>
                  </div>
                  <div className="inline-flex rounded-none p-0.5 bg-surface-subtle border border-surface-border self-start sm:self-auto text-xs">
                    <button
                      onClick={() => setCohortView('interactive')}
                      className={`px-3 py-1 rounded-none font-medium transition-colors ${cohortView === 'interactive' ? 'bg-white text-primary shadow-xs border border-surface-border' : 'text-muted hover:text-navy'}`}
                    >
                      Interactive
                    </button>
                    <button
                      onClick={() => setCohortView('image')}
                      className={`px-3 py-1 rounded-none font-medium transition-colors ${cohortView === 'image' ? 'bg-white text-primary shadow-xs border border-surface-border' : 'text-muted hover:text-navy'}`}
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
                            <div className="font-semibold text-navy text-2xs leading-tight">{c.archetype_name}</div>
                            <div className="text-muted mt-1">At risk: <span className="font-mono font-medium text-danger">₹{(c.total_at_risk_inr / 100000).toFixed(1)}L</span></div>
                            <div className="text-muted">Recovery: <span className="font-mono font-medium text-success">{(c.current_recovery_rate * 100).toFixed(1)}%</span></div>
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
              <div className="card-interactive bg-white">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-base md:text-lg font-semibold text-navy mb-0.5">Contextual Retry Bandit Convergence</h3>
                    <div className="text-xs text-muted">
                      Thompson Sampling vs baselines · 1,000 episodes · Live from <span className="font-mono text-primary">/api/v1/bandit-results</span>
                    </div>
                  </div>
                  <div className="inline-flex rounded-none p-0.5 bg-surface-subtle border border-surface-border self-start sm:self-auto text-xs">
                    <button
                      onClick={() => setBanditView('interactive')}
                      className={`px-3 py-1 rounded-none font-medium transition-colors ${banditView === 'interactive' ? 'bg-white text-primary shadow-xs border border-surface-border' : 'text-muted hover:text-navy'}`}
                    >
                      Interactive
                    </button>
                    <button
                      onClick={() => setBanditView('image')}
                      className={`px-3 py-1 rounded-none font-medium transition-colors ${banditView === 'image' ? 'bg-white text-primary shadow-xs border border-surface-border' : 'text-muted hover:text-navy'}`}
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
