// StatCard: number + label only. No description, no icon, no filler.
// color prop controls the number color. value can be a string or number.

interface StatCardProps {
  label: string
  value: string | number
  color?: 'default' | 'success' | 'warning' | 'danger' | 'primary'
  footnote?: string // Only for genuinely ambiguous numbers (the -0.38% exception)
  className?: string
}

const colorMap = {
  default: 'text-navy',
  primary: 'text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

export function StatCard({ label, value, color = 'default', footnote, className = '' }: StatCardProps) {
  return (
    <div className={`bg-white border border-surface-border rounded-lg p-5 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-default ${className}`}>
      <div className="text-sm text-muted mb-2 font-medium">{label}</div>
      <div className={`stat-number ${colorMap[color]}`}>{value}</div>
      {footnote && (
        <div className="mt-2 text-2xs text-muted leading-snug">{footnote}</div>
      )}
    </div>
  )
}
