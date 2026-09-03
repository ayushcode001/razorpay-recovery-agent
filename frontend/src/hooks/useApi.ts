// All TanStack Query hooks for backend data fetching.
// Each hook returns { data, isLoading, error } with appropriate polling.

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/api/client'
import { FALLBACK_COHORT_DATA, FALLBACK_BANDIT_DATA } from '@/data/fallbackStats'

// --- Types ---

export interface AuditEntry {
  id?: number
  timestamp: string
  payment_id: string
  amount: number
  error_code: string
  category: string
  action: string
  attempted: boolean
  predicted_success_prob: number
  estimated_uplift?: number | null
  reason: string
  outcome?: { succeeded?: boolean } | null
}

export interface AuditSummary {
  total_records: number
  attempted: number
  skipped_low_uplift: number
  escalated_to_human: number
  amount_at_risk: number
  amount_recovered: number
  amount_wasted_on_failed_attempts: number
  recovery_rate_overall: number
  recovery_rate_of_attempted: number
}

export interface DegradationIncident {
  bank: string
  method: string
  peak_z_score: number
  peak_failure_rate: number
  baseline_failure_rate: number
  time_window: string
  hours_duration: number
  total_excess_failures: number
  total_impact_inr: number
}

export interface PolicyProposal {
  proposal_id: string
  timestamp: string
  drift_detected: boolean
  evaluated_on: string
  dataset_size?: number
  original_performance?: { accuracy: number }
  drift_batch_performance?: { accuracy: number }
  current_threshold: number
  proposed_threshold: number
  net_value_current_threshold: number
  net_value_proposed_threshold: number
  estimated_net_value_gain?: number
  status: string
  note?: string
  resolved_at?: string
}

export interface CohortSummary {
  cluster_id: number
  archetype_name: string
  size: number
  pct_of_transactions: number
  total_at_risk_inr: number
  pct_of_total_risk: number
  avg_amount: number
  avg_retries: number
  avg_hour_of_day: number
  current_recovery_rate: number
  estimated_recoverable_inr: number
  dominant_categories: string[]
  dominant_methods: string[]
  dominant_sources: string[]
  distinct_taxonomy_categories: number
}

export interface ScatterPoint {
  pca_x: number
  pca_y: number
  amount: number
  method: string
}

export interface BanditCategoryResult {
  bandit_cum_rewards: number[]
  fixed_cum_rewards: number[]
  taxonomy_cum_rewards: number[] | null
  random_cum_rewards: number[]
  optimal_arm: number
  most_chosen_arm: number
  final_optimal_pull_rate: number
  percentage_gain_vs_fixed: number
  percentage_gain_vs_taxonomy: number | null
  taxonomy_default_arm: number | null
  converged: boolean
}

// --- Hooks ---

export function useAuditTrail() {
  return useQuery({
    queryKey: ['audit-trail'],
    queryFn: () =>
      apiFetch<{ summary: AuditSummary; entries: AuditEntry[] }>('/api/v1/audit-trail'),
    refetchInterval: 10_000,
    staleTime: 8_000,
  })
}

export function useKPIs() {
  const query = useAuditTrail()
  return {
    ...query,
    data: query.data?.summary,
  }
}

export function useDegradationAlerts() {
  return useQuery({
    queryKey: ['degradation-alerts'],
    queryFn: () =>
      apiFetch<{ status: string; incidents: DegradationIncident[] }>(
        '/api/v1/degradation-alerts'
      ),
    staleTime: 60_000,
  })
}

export function usePolicyProposals() {
  return useQuery({
    queryKey: ['policy-proposals'],
    queryFn: () =>
      apiFetch<{ proposals: PolicyProposal[]; current_threshold: number }>(
        '/api/v1/policy-proposals'
      ),
    staleTime: 15_000,
  })
}

export function useCohortReport() {
  return useQuery({
    queryKey: ['cohort-report'],
    queryFn: () =>
      apiFetch<{
        status: string
        cohorts: CohortSummary[]
        scatter_by_cluster: Record<string, ScatterPoint[]>
        pca_variance_ratio: number[]
        total_at_risk: number
        non_trivial_passed: boolean
      }>('/api/v1/cohort-report'),
    initialData: FALLBACK_COHORT_DATA as unknown as {
      status: string
      cohorts: CohortSummary[]
      scatter_by_cluster: Record<string, ScatterPoint[]>
      pca_variance_ratio: number[]
      total_at_risk: number
      non_trivial_passed: boolean
    },
    staleTime: 60_000,
  })
}

export function useBanditResults() {
  return useQuery({
    queryKey: ['bandit-results'],
    queryFn: () =>
      apiFetch<{
        status: string
        categories: string[]
        arms: { index: number; name: string; minutes: number; desc: string }[]
        results: Record<string, BanditCategoryResult>
      }>('/api/v1/bandit-results'),
    initialData: FALLBACK_BANDIT_DATA as unknown as {
      status: string
      categories: string[]
      arms: { index: number; name: string; minutes: number; desc: string }[]
      results: Record<string, BanditCategoryResult>
    },
    staleTime: 60_000,
  })
}

export function useApproveProposal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (proposalId: string) =>
      apiFetch(`/api/v1/policy-proposals/${proposalId}/approve`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['policy-proposals'] }),
  })
}

export function useRejectProposal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (proposalId: string) =>
      apiFetch(`/api/v1/policy-proposals/${proposalId}/reject`, { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['policy-proposals'] }),
  })
}

export function useCopilot() {
  return useMutation({
    mutationFn: (question: string) =>
      apiFetch<{
        answer: string
        grounded_record_count: number
        context_used: unknown
        model_used?: string
      }>('/api/v1/copilot', {
        method: 'POST',
        body: JSON.stringify({ question }),
      }),
  })
}
