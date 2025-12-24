'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center max-w-md px-6">
        <div className="w-16 h-16 rounded-full bg-negative/10 flex items-center justify-center mx-auto mb-6">
          <span className="text-2xl">⚠️</span>
        </div>
        <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
        <p className="text-text-secondary mb-6">
          We couldn&apos;t load the sentiment data. This might be a temporary issue.
        </p>
        <Button onClick={reset}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Try again
        </Button>
      </div>
    </div>
  )
}

