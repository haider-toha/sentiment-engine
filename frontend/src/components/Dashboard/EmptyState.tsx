'use client'

import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

interface EmptyStateProps {
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="px-6 py-12 text-center">
      <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-surface">
        <span className="text-2xl">📭</span>
      </div>
      <h3 className="mb-2 text-lg font-medium">{title}</h3>
      <p className="mx-auto mb-6 max-w-sm text-sm text-text-secondary">{description}</p>
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          <RefreshCw className="mr-2 h-4 w-4" />
          {action.label}
        </Button>
      )}
    </div>
  )
}
