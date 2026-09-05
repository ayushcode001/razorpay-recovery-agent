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
    <div className="bg-white border border-surface-border rounded-none overflow-hidden">
      <div className="px-5 py-4 border-b border-surface-border flex items-center justify-between">
        <h2 className="text-base font-semibold text-navy">Live Audit Trail</h2>
        <div className="flex items-center gap-1.5 text-2xs text-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse inline-block" />
          Polling every 10s
        </div>
      </div>

      {error && (
        <div className="px-5 py-3 text-sm text-danger bg-danger-light border-b border-surface-border">
          {error.message}
        </div>
      )}

      {isLoading && entries.length === 0 && (
        <div className="px-5 py-3 border-b border-surface-border">
          <BackendConnecting />
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-surface-muted border-b border-surface-border">
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">Time</th>
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">Payment ID</th>
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">Amount</th>
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">Error Code</th>
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">Category</th>
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">P(Success)</th>
              <th className="px-4 py-3 text-2xs font-semibold text-muted uppercase tracking-wide">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && entries.length === 0
              ? Array.from({ length: 5 }).map((_, i) => <TableRowSkeleton key={i} cols={7} />)
              : entries.length === 0
              ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-sm text-muted">
                    No audit events yet. Trigger a payment failure via the checkout demo.
                  </td>
                </tr>
              )
              : entries.map((e, i) => (
                <tr key={e.id ?? `${e.payment_id}-${i}`} className="border-b border-surface-border last:border-0 hover:bg-surface-muted/50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-muted whitespace-nowrap">
                    {e.timestamp?.slice(11, 19) ?? '-'}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-navy font-medium whitespace-nowrap">
                    {e.payment_id}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-navy whitespace-nowrap">
                    ₹{e.amount.toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted">{e.error_code}</td>
                  <td className="px-4 py-3 text-xs text-navy">{e.category}</td>
                  <td className="px-4 py-3 font-mono text-xs text-navy font-semibold">
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
