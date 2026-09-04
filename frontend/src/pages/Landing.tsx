// Landing page: /
// Sections: Hero, Problem, Why, How (Architecture), Results (stats + charts), Footer
// Rule: Real content carries visual weight. No filler text.

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { StatCard } from '@/components/StatCard'
import { ArchitectureDiagram } from '@/components/ArchitectureDiagram'
import { CohortScatterChart } from '@/components/CohortScatterChart'
import { BanditConvergenceChart } from '@/components/BanditConvergenceChart'
import { Footer } from '@/components/Footer'
import { FadeIn } from '@/components/FadeIn'
import { useCohortReport, useBanditResults, type CohortSummary } from '@/hooks/useApi'
import heroBg from '@/assets/hero_bg.webp'

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
    <div className="bg-white">

      {/* ── HERO ── */}
      <section
        className="section-pad border-b border-surface-border relative bg-cover bg-center bg-no-repeat overflow-hidden"
        style={{ backgroundImage: `url(${heroBg})` }}
      >
        <div className="absolute inset-0 bg-white/70 backdrop-blur-[0.5px] pointer-events-none" />
        <div className="container-page max-w-4xl relative z-10">
          <FadeIn delay={0.05} direction="up">
            <div className="mb-6">
              <span className="inline-block font-mono text-xs text-primary bg-primary-50 border border-primary-light px-2.5 py-1 rounded">
                Razorpay AI Buildathon · Track 03
              </span>
            </div>
          </FadeIn>
          <FadeIn delay={0.1} direction="up">
            <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-navy leading-tight mb-6">
              Autonomous Payment Failure Recovery Agent
            </h1>
          </FadeIn>
          <FadeIn delay={0.15} direction="up">
            <p className="text-lg md:text-xl text-muted leading-relaxed mb-8 max-w-3xl">
              A production agent that converts failed transactions into recovered revenue using a
              two-stage causal uplift engine, real-time banking degradation monitoring, contextual
              multi-armed bandits, and human-in-the-loop drift governance.
            </p>
          </FadeIn>
          <FadeIn delay={0.2} direction="up">
            <div className="flex flex-wrap items-center gap-4">
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-primary text-white font-medium text-sm hover:bg-primary-hover hover:shadow-md hover:-translate-y-0.5 transition-all shadow-sm"
              >
                Open Live Dashboard
                <span aria-hidden="true">→</span>
              </Link>
              <a
                href={GITHUB}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-white border border-surface-border text-navy font-medium text-sm hover:bg-surface-muted hover:shadow-sm hover:-translate-y-0.5 transition-all shadow-xs"
              >
                View on GitHub
              </a>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ── PROBLEM ── */}
      <section id="problem" className="section-pad border-b border-surface-border">
        <div className="container-page max-w-4xl">
          <FadeIn direction="up">
            <h2 className="text-2xl font-semibold text-navy mb-4">The Problem</h2>
            <div className="prose text-muted space-y-4 text-base leading-relaxed">
              <p>
                When a payment fails in Indian fintech, merchants default to brute-force retry loops or
                generic SMS blast notifications. This destroys margins through gateway fees on hopeless
                retries and annoys customers who were already resolving the failure themselves.
              </p>
              <p>
                Rule-based systems cannot adapt to issuer degradation windows. If HDFC Netbanking failure
                rate spikes from 8% to 62%, retrying through HDFC in the next 15 minutes is burning money.
                A recovery agent must know when <em>not</em> to retry.
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

      {/* ── WHY THIS APPROACH ── */}
      <section id="why" className="section-pad bg-surface-muted border-b border-surface-border">
        <div className="container-page max-w-4xl">
          <FadeIn direction="up">
            <h2 className="text-2xl font-semibold text-navy mb-4">Why This Approach</h2>
          </FadeIn>
          <div className="grid md:grid-cols-2 gap-6">
            <FadeIn delay={0.05} direction="up">
              <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 h-full">
                <div className="text-xs font-mono text-primary mb-2">Causal Uplift, Not Correlation</div>
                <p className="text-sm text-muted leading-relaxed">
                  A T-Learner separates agent-caused recoveries from organic self-recovery.
                  This prevents wasting retry budget on customers who would have recovered anyway,
                  and is the architectural choice that unlocks precision without sacrificing recall.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.1} direction="up">
              <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 h-full">
                <div className="text-xs font-mono text-primary mb-2">Drift-Gated Governance</div>
                <p className="text-sm text-muted leading-relaxed">
                  The drift-check agent evaluates model performance against fresh data and proposes
                  threshold updates, but never auto-applies them. Every policy change requires
                  explicit human approval. This is not a limitation; it's the design.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.15} direction="up">
              <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 h-full">
                <div className="text-xs font-mono text-primary mb-2">Deterministic Safety Gates</div>
                <p className="text-sm text-muted leading-relaxed">
                  Risk, compliance, and fraud-flagged transactions are routed through a deterministic
                  taxonomy layer before any ML model sees them. No probability score can override a
                  compliance stop.
                </p>
              </div>
            </FadeIn>
            <FadeIn delay={0.2} direction="up">
              <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 h-full">
                <div className="text-xs font-mono text-primary mb-2">Full Audit Trail</div>
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
      <section id="how" className="section-pad border-b border-surface-border">
        <div className="container-page">
          <FadeIn direction="up">
            <div className="mb-8">
              <h2 className="text-2xl font-semibold text-navy">How It Works</h2>
            </div>
          </FadeIn>
          <ArchitectureDiagram />
        </div>
      </section>

      {/* ── RESULTS ── */}
      <section id="results" className="section-pad bg-surface-muted border-b border-surface-border">
        <div className="container-page">
          <FadeIn direction="up">
            <h2 className="text-2xl font-semibold text-navy mb-8">Results</h2>
          </FadeIn>

          {/* Stat grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
            {RESULT_STATS.map((s, idx) => (
              <FadeIn key={s.label} delay={idx * 0.08} direction="up">
                <StatCard {...s} />
              </FadeIn>
            ))}
          </div>

          {/* Stage breakdown */}
          <FadeIn delay={0.15} direction="up">
            <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm mb-10">
              <h3 className="text-base font-semibold text-navy mb-4">Two-Stage Performance</h3>
              <div className="grid md:grid-cols-2 gap-6 text-sm">
                <div>
                  <div className="font-medium text-navy mb-1">Stage 1: Threshold Tuning (0.40 → 0.47)</div>
                  <p className="text-muted leading-relaxed">
                    Raising the decision threshold eliminates low-probability gambles.
                    Wasted spend drops from ₹86.88L to ₹64.62L.
                    <strong className="text-navy block mt-1">Net value +₹16.69L (+25.84%)</strong>
                  </p>
                </div>
                <div>
                  <div className="font-medium text-navy mb-1">Stage 2: Uplift Refinement Layer</div>
                  <p className="text-muted leading-relaxed">
                    Filtering self-recoveries saves ₹3.62L in wasted spend, foregoing ₹3.94L in gross
                    recovery. Financial impact: net-neutral (−0.38%).
                    <strong className="text-navy block mt-1">Customer gain: −47 unnecessary touchpoints</strong>
                  </p>
                </div>
              </div>
            </div>
          </FadeIn>

          {/* Charts */}
          <div className="space-y-8">
            {/* Cohort Scatter */}
            <FadeIn delay={0.1} direction="up">
              <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-navy mb-0.5">Discovered Transaction Cohorts</h3>
                    <div className="text-xs text-muted">
                      PCA latent space · Unsupervised GMM clustering · Live from <span className="font-mono">/api/v1/cohort-report</span>
                    </div>
                  </div>
                  <div className="inline-flex rounded-md p-1 bg-surface-subtle border border-surface-border self-start sm:self-auto text-xs">
                    <button
                      onClick={() => setCohortView('interactive')}
                      className={`px-2.5 py-1 rounded font-medium transition-colors ${cohortView === 'interactive' ? 'bg-white shadow-xs text-primary' : 'text-muted hover:text-navy'}`}
                    >
                      📊 Interactive
                    </button>
                    <button
                      onClick={() => setCohortView('image')}
                      className={`px-2.5 py-1 rounded font-medium transition-colors ${cohortView === 'image' ? 'bg-white shadow-xs text-primary' : 'text-muted hover:text-navy'}`}
                    >
                      🖼️ Stats Plot (PNG)
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
                          <div key={i} className="bg-surface-subtle rounded-md p-3 text-xs">
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
                    <div className="overflow-hidden rounded-lg border border-surface-border bg-surface-muted">
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
              <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                  <div>
                    <h3 className="text-base font-semibold text-navy mb-0.5">Contextual Retry Bandit Convergence</h3>
                    <div className="text-xs text-muted">
                      Thompson Sampling vs baselines · 1,000 episodes · Live from <span className="font-mono">/api/v1/bandit-results</span>
                    </div>
                  </div>
                  <div className="inline-flex rounded-md p-1 bg-surface-subtle border border-surface-border self-start sm:self-auto text-xs">
                    <button
                      onClick={() => setBanditView('interactive')}
                      className={`px-2.5 py-1 rounded font-medium transition-colors ${banditView === 'interactive' ? 'bg-white shadow-xs text-primary' : 'text-muted hover:text-navy'}`}
                    >
                      📊 Interactive
                    </button>
                    <button
                      onClick={() => setBanditView('image')}
                      className={`px-2.5 py-1 rounded font-medium transition-colors ${banditView === 'image' ? 'bg-white shadow-xs text-primary' : 'text-muted hover:text-navy'}`}
                    >
                      🖼️ Stats Plot (PNG)
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
                    <div className="overflow-hidden rounded-lg border border-surface-border bg-surface-muted">
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
