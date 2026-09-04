// BanditConvergenceChart: 4-panel Recharts LineChart from /api/v1/bandit-results.
// Shows Thompson Sampling vs 1m baseline vs taxonomy default vs random policy.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { BanditCategoryResult } from '@/hooks/useApi'
import { CardSkeleton } from '@/components/LoadingSkeleton'

const CATEGORY_LABELS: Record<string, string> = {
  retry_later: 'Insufficient Funds → Optimal: 24h',
  smart_retry: 'Network Timeout → Optimal: 15m',
  change_method: 'Card Expired → Optimal: 6h',
  user_error: 'Wrong CVV/OTP → Optimal: 1h',
}

const CATEGORY_COLORS: Record<string, string> = {
  retry_later: '#2563EB',
  smart_retry: '#16A34A',
  change_method: '#7C3AED',
  user_error: '#D97706',
}


interface SinglePanelProps {
  category: string
  result: BanditCategoryResult
}

function SinglePanel({ category, result }: SinglePanelProps) {
  const color = CATEGORY_COLORS[category] ?? '#2563EB'
  const n = result.bandit_cum_rewards.length
  const step = Math.max(1, Math.floor(n / 200))

  const data = result.bandit_cum_rewards
    .filter((_, i) => i % step === 0 || i === n - 1)
    .map((_, i) => {
      const idx = Math.min(i * step, n - 1)
      return {
        ep: idx + 1,
        bandit: result.bandit_cum_rewards[idx],
        fixed: result.fixed_cum_rewards[idx],
        taxonomy: result.taxonomy_cum_rewards?.[idx] ?? undefined,
        random: result.random_cum_rewards[idx],
      }
    })

  const gain = (result.percentage_gain_vs_fixed * 100).toFixed(0)

  return (
    <div className="bg-white border border-surface-border rounded-lg p-4">
      <div className="mb-3">
        <div className="text-sm font-semibold text-navy">{CATEGORY_LABELS[category]}</div>
        <div className="text-2xs text-muted mt-0.5">
          +{gain}% vs 1m baseline · {(result.final_optimal_pull_rate * 100).toFixed(0)}% optimal arm rate
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
          <XAxis dataKey="ep" tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: '#94A3B8' }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid #E2E8F0' }}
            labelStyle={{ color: '#64748B', fontSize: 10 }}
          />
          <Line dataKey="bandit" name="Thompson Bandit" stroke={color} strokeWidth={2} dot={false} />
          <Line dataKey="fixed" name="1m Baseline" stroke="#94A3B8" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
          {result.taxonomy_cum_rewards && (
            <Line dataKey="taxonomy" name="Taxonomy Default" stroke="#0EA5E9" strokeWidth={1.5} strokeDasharray="2 3" dot={false} />
          )}
          <Line dataKey="random" name="Random" stroke="#CBD5E1" strokeWidth={1} strokeDasharray="1 3" dot={false} />
          <Legend iconSize={7} wrapperStyle={{ fontSize: 10 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

interface Props {
  categories: string[]
  results: Record<string, BanditCategoryResult>
  isLoading?: boolean
}

export function BanditConvergenceChart({ categories, results, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[0, 1, 2, 3].map((i) => <CardSkeleton key={i} lines={5} />)}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {categories.map((cat) =>
        results[cat] ? <SinglePanel key={cat} category={cat} result={results[cat]} /> : null
      )}
    </div>
  )
}
