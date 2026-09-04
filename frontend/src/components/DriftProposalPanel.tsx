// DriftProposalPanel: policy change proposals with working approve/reject buttons.

import { useState } from 'react'
import type { PolicyProposal } from '@/hooks/useApi'
import { useApproveProposal, useRejectProposal } from '@/hooks/useApi'
import { CardSkeleton, BackendConnecting } from '@/components/LoadingSkeleton'

function formatINR(n: number) {
  if (Math.abs(n) >= 100_000) return `₹${(n / 100_000).toFixed(2)}L`
  if (Math.abs(n) >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`
  return `₹${n}`
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'approved')
    return <span className="text-2xs font-semibold text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded uppercase">Approved</span>
  if (status === 'rejected')
    return <span className="text-2xs font-semibold text-dark-muted bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 rounded uppercase">Rejected</span>
  return <span className="text-2xs font-semibold text-amber bg-amber/15 border border-amber/30 px-2 py-0.5 rounded uppercase">Pending</span>
}

function ProposalCard({ proposal }: { proposal: PolicyProposal }) {
  const approve = useApproveProposal()
  const reject = useRejectProposal()
  const [limitError, setLimitError] = useState(false)

  const isPending = proposal.status === 'pending_human_approval'

  async function handleAction(action: 'approve' | 'reject') {
    setLimitError(false)
    try {
      if (action === 'approve') await approve.mutateAsync(proposal.proposal_id)
      else await reject.mutateAsync(proposal.proposal_id)
    } catch (err) {
      if (err instanceof Error && err.message.includes('429')) {
        setLimitError(true)
      }
    }
  }

  const gain = proposal.estimated_net_value_gain ?? (proposal.net_value_proposed_threshold - proposal.net_value_current_threshold)

  return (
    <div className="border border-white/[0.08] rounded-lg p-4 bg-white/[0.02] shadow-xs">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <div className="font-mono text-xs text-dark-muted">{proposal.proposal_id}</div>
          <div className="text-xs text-dark-muted mt-0.5">{proposal.timestamp?.slice(0, 19).replace('T', ' ')}</div>
        </div>
        <StatusBadge status={proposal.status} />
      </div>

      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs mb-4">
        <div className="text-dark-muted">Drift detected: <span className={`font-semibold ${proposal.drift_detected ? 'text-rose-400' : 'text-emerald-400'}`}>{proposal.drift_detected ? 'YES' : 'NO'}</span></div>
        <div className="text-dark-muted">Evaluated on: <span className="font-mono text-dark-cream">{proposal.evaluated_on?.slice(0, 10)}</span></div>
        <div className="text-dark-muted">Current threshold: <span className="font-mono text-dark-cream">{proposal.current_threshold.toFixed(2)}</span></div>
        <div className="text-dark-muted">Proposed threshold: <span className="font-mono font-semibold text-amber">{proposal.proposed_threshold.toFixed(2)}</span></div>
        <div className="text-dark-muted">Net value now: <span className="font-mono text-dark-cream">{formatINR(proposal.net_value_current_threshold)}</span></div>
        <div className="text-dark-muted">Net value proposed: <span className={`font-mono font-semibold ${gain >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{formatINR(proposal.net_value_proposed_threshold)}</span></div>
        <div className="col-span-2 text-dark-muted">
          Estimated gain: <span className={`font-mono font-semibold ${gain >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{gain >= 0 ? '+' : ''}{formatINR(gain)}</span>
        </div>
      </div>

      {limitError && (
        <div className="text-xs text-amber mb-3">Rate limited. Try again in a moment.</div>
      )}

      {isPending && (
        <div className="flex gap-2">
          <button
            id={`approve-${proposal.proposal_id}`}
            onClick={() => handleAction('approve')}
            disabled={approve.isPending || reject.isPending}
            className="flex-1 text-sm font-medium py-1.5 px-3 rounded-md bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors"
          >
            {approve.isPending ? 'Approving…' : 'Approve'}
          </button>
          <button
            id={`reject-${proposal.proposal_id}`}
            onClick={() => handleAction('reject')}
            disabled={approve.isPending || reject.isPending}
            className="flex-1 text-sm font-medium py-1.5 px-3 rounded-md bg-white/[0.06] text-dark-cream border border-white/[0.1] hover:bg-white/[0.1] disabled:opacity-50 transition-colors"
          >
            {reject.isPending ? 'Rejecting…' : 'Reject'}
          </button>
        </div>
      )}
    </div>
  )
}

interface Props {
  proposals: PolicyProposal[]
  currentThreshold?: number
  isLoading: boolean
  error?: Error | null
}

export function DriftProposalPanel({ proposals, currentThreshold, isLoading, error }: Props) {
  return (
    <div className="card-dark rounded-lg shadow-sm overflow-hidden border border-white/[0.08]">
      <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-dark-cream">Policy Proposals</h2>
          {currentThreshold != null && (
            <div className="text-xs text-dark-muted mt-0.5">Active threshold: <span className="font-mono font-semibold text-amber">{currentThreshold.toFixed(2)}</span></div>
          )}
        </div>
        {proposals.filter(p => p.status === 'pending_human_approval').length > 0 && (
          <span className="text-2xs font-semibold text-rose-400 bg-rose-500/15 border border-rose-500/30 px-2 py-0.5 rounded">
            {proposals.filter(p => p.status === 'pending_human_approval').length} PENDING
          </span>
        )}
      </div>
      <div className="p-5 space-y-3">
        {isLoading && !error && <><BackendConnecting /><CardSkeleton lines={5} /></>}
        {error && <div className="text-sm text-rose-400">{error.message}</div>}
        {!isLoading && !error && proposals.length === 0 && (
          <div className="text-sm text-dark-muted text-center py-4">No policy proposals. Trigger a drift-check via the backend.</div>
        )}
        {proposals.slice(0, 5).map((p) => <ProposalCard key={p.proposal_id} proposal={p} />)}
      </div>
    </div>
  )
}
