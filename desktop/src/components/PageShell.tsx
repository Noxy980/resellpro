import { ReactNode } from 'react'

export default function PageShell({
  children,
  className = '',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <div className={`page-shell animate-fade-in ${className}`}>
      {children}
    </div>
  )
}
