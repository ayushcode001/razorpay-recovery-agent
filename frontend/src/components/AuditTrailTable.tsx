// AuditTrailTable: live-polling table of recent audit entries.

import type { AuditEntry } from '@/hooks/useApi'
import { TableRowSkeleton, BackendConnecting } from '@/components/LoadingSkeleton'

function ActionPill({ action }: { action: string }) {
  if (action.includes('escalate')) return <span className="pill pill-escalate">Escalate</span>
  if (action.includes('skip')) return <span className="pill pill-skip">Skip</span>
  if (action.includes('retry')) return <span className="pill pill-retry">{action}</span>
  return <span className="pill pill-prompt">{action}</span>
}

interface Props {
  entries: AuditEntry[]
  isLoading: boolean
  error?: Error | null
}

export function AuditTrailTable({ entries, isLoading, error }: Props) {
  return (
    <div className="card-dark rounded-lg overflow-hidden border border-white/[0.08]">
      <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between">
        <h2 className="text-base font-semibold text-dark-cream">Live Audit Trail</h2>
        <div className="flex items-center gap-1.5 text-2xs text-dark-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
          Polling every 10s
        </div>
      </div>

      {error && (
        <div className="px-5 py-3 text-sm text-rose-400 bg-rose-500/10 border-b border-white/[0.08]">
          {error.message}
        </div>
      )}

      {isLoading && entries.length === 0 && (
        <div className="px-5 py-3 border-b border-white/[0.08]">
          <BackendConnecting />
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-white/[0.02] border-b border-white/[0.08]">
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">Time</th>
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">Payment ID</th>
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">Amount</th>
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">Error Code</th>
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">Category</th>
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">P(Success)</th>
              <th className="px-4 py-3 text-2xs font-semibold text-dark-muted uppercase tracking-wide">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && entries.length === 0
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={7} />)
              : entries.length === 0
              ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-dark-muted">
                    No audit events yet. Trigger a payment failure via the checkout demo.
                  </td>
                </tr>
              )
              : entries.map((e, i) => (
                <tr key={e.id ?? `${e.payment_id}-${i}`} className="border-b border-white/[0.04] last:border-0 hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-dark-muted whitespace-nowrap">
                    {e.timestamp?.slice(11, 19) ?? '-'}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-dark-cream font-medium whitespace-nowrap">
                    {e.payment_id}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-dark-cream whitespace-nowrap">
                    ₹{e.amount.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-dark-muted">{e.error_code}</td>
                  <td className="px-4 py-3 text-xs text-dark-muted">{e.category}</td>
                  <td className="px-4 py-3 font-mono text-xs text-amber font-semibold">
                    {(e.predicted_success_prob * 100).toFixed(1)}%
                  </td>
                  <td className="px-4 py-3">
                    <ActionPill action={e.action} />
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>
    </div>
  )
}
