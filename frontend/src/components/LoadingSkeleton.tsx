// LoadingSkeleton — pulsing placeholder that matches content shape.
// Shows "Connecting to backend..." context for cold Render starts.

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return <div className={`skeleton ${className}`} />
}

export function StatCardSkeleton() {
  return (
    <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm">
      <Skeleton className="h-4 w-24 mb-3" />
      <Skeleton className="h-8 w-32" />
    </div>
  )
}

export function TableRowSkeleton({ cols = 7 }: { cols?: number }) {
  return (
    <tr>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  )
}

export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-white border border-surface-border rounded-lg p-5 shadow-sm space-y-3">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === 0 ? 'w-48' : 'w-full'}`} />
      ))}
    </div>
  )
}

export function BackendConnecting() {
  return (
    <div className="flex items-center gap-2 text-sm text-muted py-2">
      <span className="inline-block w-2 h-2 rounded-full bg-warning animate-pulse" />
      Connecting to backend — may take a moment on first load
    </div>
  )
}
