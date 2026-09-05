// Architecture diagram: 8-component flow layout.
// CSS-positioned boxes with connector lines. Not ASCII, not an image.
// Adapts the ASCII diagram from README into a styled visual flow.
// Annotated with data-arch attributes for GSAP ScrollTrigger pin-and-reveal.

const COMPONENTS = [
  {
    id: 1,
    name: 'Deterministic Taxonomy',
    module: 'agent/taxonomy.py',
    pitch: 'Safety gates & compliance boundaries. Never retried.',
    color: 'border-surface-border bg-white',
    badgeColor: 'text-muted',
    textColor: 'text-navy',
  },
  {
    id: 2,
    name: 'Success Predictor',
    module: 'agent/success_predictor.py',
    pitch: 'P(success | context) via Gradient Boosting. Threshold: 0.47.',
    color: 'border-primary/30 bg-primary-50/50',
    badgeColor: 'text-primary',
    textColor: 'text-navy',
  },
  {
    id: 3,
    name: 'Causal Uplift Modeler',
    module: 'agent/uplift_model.py',
    pitch: 'T-Learner isolates intervention lift from organic self-recovery.',
    color: 'border-primary/30 bg-primary-50/50',
    badgeColor: 'text-primary',
    textColor: 'text-navy',
  },
  {
    id: 4,
    name: 'Policy Engine',
    module: 'agent/policy_engine.py',
    pitch: 'Combines taxonomy + P(success) + uplift into a bounded decision.',
    color: 'border-surface-border bg-white',
    badgeColor: 'text-muted',
    textColor: 'text-navy',
  },
  {
    id: 5,
    name: 'Degradation Forecaster',
    module: 'agent/degradation_agent.py',
    pitch: 'Seasonal Z-score (≥ 3σ) detects issuer outages in real-time.',
    color: 'border-warning/30 bg-warning-light/40',
    badgeColor: 'text-warning-text',
    textColor: 'text-navy',
  },
  {
    id: 6,
    name: 'Contextual Retry Bandit',
    module: 'agent/retry_bandit.py',
    pitch: 'Thompson Sampling learns optimal retry cooldown per error category.',
    color: 'border-success/30 bg-success-light/40',
    badgeColor: 'text-success-text',
    textColor: 'text-navy',
  },
  {
    id: 7,
    name: 'Audit Trail Copilot',
    module: 'agent/copilot.py',
    pitch: 'Gemini narration layer: read-only, zero financial action rights.',
    color: 'border-primary/30 bg-primary-50/50',
    badgeColor: 'text-primary',
    textColor: 'text-navy',
  },
  {
    id: 8,
    name: 'Drift-Check Agent',
    module: 'agent/drift_check.py',
    pitch: 'Detects model decay, proposes threshold updates. Never auto-applies.',
    color: 'border-danger/30 bg-danger-light/40',
    badgeColor: 'text-danger-text',
    textColor: 'text-navy',
  },
]

function Arrow({ vertical = false, dataArch }: { vertical?: boolean; dataArch?: string }) {
  if (vertical) {
    return (
      <div data-arch={dataArch} className="flex justify-center py-1 transition-opacity duration-200">
        <svg width="12" height="24" viewBox="0 0 12 24" fill="none" className="text-slate-400">
          <line x1="6" y1="0" x2="6" y2="18" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 2" />
          <path d="M3 16L6 22L9 16" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
      </div>
    )
  }
  return (
    <div data-arch={dataArch} className="flex items-center px-1 transition-opacity duration-200">
      <svg width="24" height="12" viewBox="0 0 24 12" fill="none" className="text-slate-400">
        <line x1="0" y1="6" x2="18" y2="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 2" />
        <path d="M16 3L22 6L16 9" stroke="currentColor" strokeWidth="1.5" fill="none" />
      </svg>
    </div>
  )
}

function ArchNode({ comp }: { comp: typeof COMPONENTS[0] }) {
  return (
    <div
      data-arch={`comp-${comp.id}`}
      className={`arch-node border ${comp.color} flex-1 min-w-0 transition-all duration-300`}
    >
      <div className="flex items-start gap-2">
        <span className={`text-2xs font-bold font-mono shrink-0 mt-0.5 ${comp.badgeColor}`}>
          {String(comp.id).padStart(2, '0')}
        </span>
        <div>
          <div className={`text-sm font-semibold ${comp.textColor} leading-tight`}>{comp.name}</div>
          <div className="text-2xs font-mono text-muted mt-0.5">{comp.module}</div>
          <div className="text-xs text-muted mt-1 leading-snug">{comp.pitch}</div>
        </div>
      </div>
    </div>
  )
}

export function ArchitectureDiagram() {
  const top = COMPONENTS.slice(0, 2)    // Taxonomy + Success Predictor
  const mid1 = COMPONENTS.slice(2, 4)   // Uplift + Policy Engine
  const actions = [
    { label: 'Autonomous Retry', desc: 'retry_after_cooldown / retry_with_backoff → Payment Link', color: 'border-success/30 bg-success-light/40 text-success-text' },
    { label: 'Customer Nudge', desc: 'prompt_new_payment_method → Payment Link + Email/SMS', color: 'border-primary/30 bg-primary-50/60 text-primary-dark' },
    { label: 'Escalate to Human', desc: 'Risk / compliance stop: bounded, auditable', color: 'border-danger/30 bg-danger-light/40 text-danger-text' },
  ]
  const support = COMPONENTS.slice(4)   // Degradation, Bandit, Copilot, Drift

  return (
    <div className="space-y-2 text-sm">
      {/* Webhook event */}
      <div data-arch="webhook" className="flex justify-center transition-all duration-300">
        <div className="arch-node bg-primary-50 border-primary-light text-navy text-center px-6 py-2 shadow-xs">
          <div className="text-xs font-mono text-primary font-medium">Razorpay Telemetry</div>
          <div className="font-semibold text-sm text-navy">payment.failed Webhook Ingest</div>
        </div>
      </div>
      <Arrow vertical dataArch="arrow-top" />

      {/* Row 1: Taxonomy + Success Predictor (parallel) */}
      <div className="flex gap-2">
        {top.map((c) => <ArchNode key={c.id} comp={c} />)}
      </div>
      <Arrow vertical dataArch="arrow-mid" />

      {/* Row 2: Uplift + Policy Engine */}
      <div className="flex gap-2">
        {mid1.map((c) => <ArchNode key={c.id} comp={c} />)}
      </div>
      <Arrow vertical dataArch="arrow-actions" />

      {/* Row 3: Action outcomes */}
      <div data-arch="actions" className="flex gap-2 transition-all duration-300">
        {actions.map((a) => (
          <div key={a.label} className={`arch-node border ${a.color} flex-1`}>
            <div className="font-semibold text-xs">{a.label}</div>
            <div className="text-2xs mt-0.5 leading-snug opacity-80">{a.desc}</div>
          </div>
        ))}
      </div>
      <Arrow vertical dataArch="arrow-audit" />

      {/* Row 4: Audit Trail */}
      <div data-arch="audit" className="flex justify-center transition-all duration-300">
        <div className="arch-node border-surface-border text-center px-8 py-2 text-navy bg-white shadow-xs">
          <div className="text-xs font-mono text-muted">agent/audit.py</div>
          <div className="font-semibold text-sm text-navy">Immutable Audit Trail → PostgreSQL</div>
        </div>
      </div>

      {/* Support components */}
      <div className="mt-6 pt-6 border-t border-surface-border">
        <div data-arch="support-header" className="text-xs font-semibold text-primary mb-3 uppercase tracking-wider transition-opacity duration-200">
          Supporting Subagents & Copilots
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          {support.map((c) => <ArchNode key={c.id} comp={c} />)}
        </div>
      </div>
    </div>
  )
}
