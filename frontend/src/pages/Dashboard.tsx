// Dashboard page: /dashboard
// 6 panels: KPIs, Audit Trail, Degradation Alerts, Policy Proposals, Copilot, Checkout Demo
// TanStack Query for all data. Skeleton loading states. Graceful degradation.

import { StatCard } from '@/components/StatCard'
import { StatCardSkeleton } from '@/components/LoadingSkeleton'
import { AuditTrailTable } from '@/components/AuditTrailTable'
import { DegradationPanel } from '@/components/DegradationPanel'
import { DriftProposalPanel } from '@/components/DriftProposalPanel'
import { CheckoutTrigger } from '@/components/CheckoutTrigger'
import { useAuditTrail, useDegradationAlerts, usePolicyProposals } from '@/hooks/useApi'

function formatINR(n: number) {
  if (n >= 10_000_000) return `₹${(n / 100_000).toFixed(1)}L`
  if (n >= 100_000) return `₹${(n / 100_000).toFixed(2)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`
  return `₹${n}`
}

function KPIRow() {
  const { data, isLoading } = useAuditTrail()
  const s = data?.summary

  if (isLoading && !s) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => <StatCardSkeleton key={i} />)}
      </div>
    )
  }

  if (!s) return null

  const netValue = s.amount_recovered - s.amount_wasted_on_failed_attempts
  const cards = [
    {
      label: 'Net Value',
      value: formatINR(netValue),
      color: netValue >= 0 ? 'success' as const : 'danger' as const,
    },
    {
      label: 'Recovery Rate (attempted)',
      value: s.recovery_rate_of_attempted != null
        ? `${(s.recovery_rate_of_attempted * 100).toFixed(1)}%`
        : '-',
      color: 'primary' as const,
    },
    {
      label: 'Total Handled',
      value: s.total_records.toLocaleString(),
      color: 'default' as const,
    },
    {
      label: 'Attempted',
      value: s.attempted.toLocaleString(),
      color: 'default' as const,
    },
    {
      label: 'Escalated',
      value: s.escalated_to_human.toLocaleString(),
      color: 'warning' as const,
    },
    {
      label: 'Wasted Spend',
      value: formatINR(s.amount_wasted_on_failed_attempts),
      color: 'danger' as const,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((c) => <StatCard key={c.label} {...c} />)}
    </div>
  )
}

export function Dashboard() {
  const auditQuery = useAuditTrail()
  const degradQuery = useDegradationAlerts()
  const proposalQuery = usePolicyProposals()

  const entries = auditQuery.data?.entries ?? []
  const incidents = degradQuery.data?.incidents ?? []
  const proposals = proposalQuery.data?.proposals ?? []
  const currentThreshold = proposalQuery.data?.current_threshold

  return (
    <div className="min-h-screen bg-surface-muted">
      <div className="container-page py-8 space-y-6">

        {/* ── PAGE HEADER ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-navy">Live Dashboard</h1>
            <div className="text-sm text-muted mt-0.5">
              Real-time decisions from the autonomous recovery agent
            </div>
          </div>
          <div className="text-xs text-muted font-mono">
            {new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
          </div>
        </div>

        {/* ── KPI ROW ── */}
        <KPIRow />

        {/* ── AUDIT TRAIL ── */}
        <AuditTrailTable
          entries={entries.slice(0, 50)}
          isLoading={auditQuery.isLoading}
          error={auditQuery.error as Error | null}
        />

        {/* ── ALERTS + PROPOSALS ── */}
        <div className="grid md:grid-cols-2 gap-6">
          <DegradationPanel
            incidents={incidents}
            isLoading={degradQuery.isLoading}
            error={degradQuery.error as Error | null}
          />
          <DriftProposalPanel
            proposals={proposals}
            currentThreshold={currentThreshold}
            isLoading={proposalQuery.isLoading}
            error={proposalQuery.error as Error | null}
          />
        </div>

        {/* ── CHECKOUT DEMO & TESTING GUIDE ── */}
        <div className="grid md:grid-cols-2 gap-6">
          <CheckoutTrigger />
          <div className="card-interactive flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-surface-border pb-3 mb-4">
                <h2 className="text-base font-semibold text-navy">Autonomous Pipeline Guide</h2>
                <span className="text-2xs font-mono font-medium text-primary bg-primary-50 px-2 py-0.5 rounded border border-primary-light">
                  Live System
                </span>
              </div>
              <div className="space-y-3 text-xs text-muted leading-relaxed">
                <div className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary font-mono font-bold text-2xs flex items-center justify-center shrink-0 mt-0.5">1</span>
                  <div>
                    <strong className="text-navy">Simulate a failure</strong> using the test cards on the left. The Razorpay checkout modal generates a mock transaction failure.
                  </div>
                </div>
                <div className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary font-mono font-bold text-2xs flex items-center justify-center shrink-0 mt-0.5">2</span>
                  <div>
                    <strong className="text-navy">Autonomous decisioning</strong> intercepts the webhook: checks bank degradation, evaluates the deterministic taxonomy safety gate, and computes causal uplift.
                  </div>
                </div>
                <div className="flex gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-primary/10 text-primary font-mono font-bold text-2xs flex items-center justify-center shrink-0 mt-0.5">3</span>
                  <div>
                    <strong className="text-navy">Live Audit Trail</strong> records the chosen recovery action (retry, nudge, or human escalation) into PostgreSQL within 10 seconds.
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-surface-border text-2xs text-muted flex items-center justify-between">
              <span>Have questions about the results?</span>
              <span className="text-primary font-medium">Use Copilot in the bottom-right →</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
