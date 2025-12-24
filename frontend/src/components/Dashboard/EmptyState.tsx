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
    <div className="text-center py-12 px-6">
      <div className="w-16 h-16 rounded-full bg-surface flex items-center justify-center mx-auto mb-4">
        <span className="text-2xl">📭</span>
      </div>
      <h3 className="text-lg font-medium mb-2">{title}</h3>
      <p className="text-text-secondary text-sm mb-6 max-w-sm mx-auto">
        {description}
      </p>
      {action && (
        <Button variant="secondary" onClick={action.onClick}>
          <RefreshCw className="w-4 h-4 mr-2" />
          {action.label}
        </Button>
      )}
    </div>
  )
}

