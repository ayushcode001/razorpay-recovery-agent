// StatCard: number + label only. No description, no icon, no filler.
// color prop controls the number color. value can be a string or number.

interface StatCardProps {
  label: string
  value: string | number
  color?: 'default' | 'success' | 'warning' | 'danger' | 'primary' | 'navy'
  footnote?: string
  className?: string
  dark?: boolean
}

const colorMapLight: Record<string, string> = {
  default: 'text-navy',
  navy: 'text-navy',
  primary: 'text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

export function StatCard({
  label,
  value,
  color = 'default',
  footnote,
  className = '',
}: StatCardProps) {
  const numberColor = colorMapLight[color] || 'text-navy'

  return (
    <div className={`bg-white border border-surface-border p-5 rounded-none ${className}`}>
      <div className={`stat-number ${numberColor}`}>{value}</div>
      <div className="text-xs text-muted mt-1 font-normal">
        {label}
      </div>
      {footnote && (
        <div className="mt-2 text-2xs leading-snug text-muted">
          {footnote}
        </div>
      )}
    </div>
  )
}
