// DegradationPanel: displays active bank/gateway outage alerts.

import type { DegradationIncident } from '@/hooks/useApi'
import { CardSkeleton, BackendConnecting } from '@/components/LoadingSkeleton'

function formatINR(n: number) {
  if (n >= 100_000) return `₹${(n / 100_000).toFixed(1)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`
  return `₹${n}`
}

interface Props {
  incidents: DegradationIncident[]
  isLoading: boolean
  error?: Error | null
}

export function DegradationPanel({ incidents, isLoading, error }: Props) {
  return (
    <div className="card-dark rounded-lg shadow-sm overflow-hidden border border-white/[0.08]">
      <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between">
        <h2 className="text-base font-semibold text-dark-cream">Degradation Alerts</h2>
        {incidents.length > 0 && (
          <span className="text-2xs font-semibold text-amber bg-amber/15 border border-amber/30 px-2 py-0.5 rounded">
            {incidents.length} ACTIVE
          </span>
        )}
      </div>

      <div className="p-5 space-y-3">
        {isLoading && !error && <><BackendConnecting /><CardSkeleton lines={4} /></>}

        {error && (
          <div className="text-sm text-rose-400">{error.message}</div>
        )}

        {!isLoading && !error && incidents.length === 0 && (
          <div className="text-sm text-dark-muted text-center py-4">
            No active degradation events.
          </div>
        )}

        {incidents.map((inc, i) => (
          <div key={i} className="border border-amber/30 bg-amber/[0.03] rounded-md p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-dark-cream">{inc.bank}</span>
                  <span className="font-mono text-2xs text-dark-muted uppercase">{inc.method}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-dark-muted">
                  <div>Z-score: <span className="font-mono font-semibold text-amber">{inc.peak_z_score.toFixed(1)}σ</span></div>
                  <div>Failure rate: <span className="font-mono font-semibold text-rose-400">{(inc.peak_failure_rate * 100).toFixed(1)}%</span></div>
                  <div>Baseline: <span className="font-mono text-dark-cream">{(inc.baseline_failure_rate * 100).toFixed(1)}%</span></div>
                  <div>Duration: <span className="font-mono text-dark-cream">{inc.hours_duration}h</span></div>
                  <div>Excess failures: <span className="font-mono text-dark-cream">{inc.total_excess_failures}</span></div>
                  <div>Financial impact: <span className="font-mono font-semibold text-rose-400">{formatINR(inc.total_impact_inr)}</span></div>
                </div>
              </div>
              <div className="text-2xs font-mono text-dark-muted whitespace-nowrap shrink-0">{inc.time_window}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
