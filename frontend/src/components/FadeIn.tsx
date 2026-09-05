import type { ReactNode } from 'react'

interface FadeInProps {
  children: ReactNode
  className?: string
  delay?: number
  direction?: 'up' | 'down' | 'none'
  duration?: number
  distance?: number
}

export function FadeIn({
  children,
  className = '',
}: FadeInProps) {
  return <div className={className}>{children}</div>
}

