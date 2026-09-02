// CohortScatterChart — Recharts ScatterChart rendering PCA 2D data from /api/v1/cohort-report.
// 5 clusters, colored by cohort, tooltip shows archetype + INR recoverable.

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { CohortSummary, ScatterPoint } from '@/hooks/useApi'
import { CardSkeleton } from '@/components/LoadingSkeleton'

const CLUSTER_COLORS = ['#2563EB', '#16A34A', '#D97706', '#7C3AED', '#DB2777']

interface Props {
  cohorts: CohortSummary[]
  scatterByCluster: Record<string, ScatterPoint[]>
  isLoading?: boolean
}

function formatINR(n: number) {
  if (n >= 1_000_000) return `₹${(n / 100_000).toFixed(1)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(0)}K`
  return `₹${n}`
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: ScatterPoint & { archetype: string; recoverable: number } }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="bg-white border border-surface-border rounded-md p-3 shadow-md text-sm">
      <div className="font-semibold text-navy text-xs leading-tight mb-1">{d.archetype}</div>
      <div className="text-muted text-xs">Method: <span className="font-mono text-navy">{d.method}</span></div>
      <div className="text-muted text-xs">Amount: <span className="font-mono text-navy">{formatINR(d.amount)}</span></div>
      <div className="text-success text-xs font-medium mt-1">Recoverable: {formatINR(d.recoverable)}</div>
    </div>
  )
}

export function CohortScatterChart({ cohorts, scatterByCluster, isLoading }: Props) {
  if (isLoading) return <CardSkeleton lines={4} />

  // Enrich scatter points with archetype and recoverable INR
  const datasets = cohorts.map((c, i) => {
    const points = (scatterByCluster[String(c.cluster_id)] ?? []).map((p) => ({
      ...p,
      archetype: c.archetype_name,
      recoverable: c.estimated_recoverable_inr,
    }))
    return { cohort: c, points, color: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }
  })

  return (
    <div>
      <ResponsiveContainer width="100%" height={340}>
        <ScatterChart margin={{ top: 8, right: 20, bottom: 8, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
          <XAxis dataKey="pca_x" type="number" name="PCA 1" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
          <YAxis dataKey="pca_y" type="number" name="PCA 2" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} />
          <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
          {datasets.map(({ cohort, points, color }) => (
            <Scatter
              key={cohort.cluster_id}
              name={`#${cohorts.indexOf(cohort) + 1} ${cohort.archetype_name.split(' - ')[0]}`}
              data={points}
              fill={color}
              opacity={0.7}
              r={3.5}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
      <div className="mt-3 text-2xs text-muted text-center">
        PCA 2D latent space · {cohorts.length} discovered cohorts · {cohorts.reduce((s, c) => s + c.size, 0).toLocaleString()} transactions
      </div>
    </div>
  )
}
