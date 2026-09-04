// StatCard: number + label only. No description, no icon, no filler.
// color prop controls the number color. value can be a string or number.

interface StatCardProps {
  label: string
  value: string | number
  color?: 'default' | 'success' | 'warning' | 'danger' | 'primary'
  footnote?: string // Only for genuinely ambiguous numbers (the -0.38% exception)
  className?: string
  dark?: boolean
}

const colorMapLight = {
  default: 'text-navy',
  primary: 'text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
}

const colorMapDark = {
  default: 'text-dark-cream',
  primary: 'text-amber',
  success: 'text-emerald-400',
  warning: 'text-amber-light',
  danger: 'text-rose-400',
}

export function StatCard({
  label,
  value,
  color = 'default',
  footnote,
  className = '',
  dark = true,
}: StatCardProps) {
  const colorMap = dark ? colorMapDark : colorMapLight

  return (
    <div className={`${dark ? 'card-dark' : 'card-interactive'} cursor-default ${className}`}>
      <div className={`text-xs md:text-sm mb-2 font-medium ${dark ? 'text-dark-muted' : 'text-muted'}`}>
        {label}
      </div>
      <div className={`stat-number ${colorMap[color]}`}>{value}</div>
      {footnote && (
        <div className={`mt-2 text-2xs leading-snug ${dark ? 'text-dark-subtle' : 'text-muted'}`}>
          {footnote}
        </div>
      )}
    </div>
  )
}
