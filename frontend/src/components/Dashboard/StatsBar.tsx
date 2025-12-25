'use client'

import { useEffect, useState } from 'react'
import { formatRelativeTime } from '@/lib/utils'
import { Globe2, FileText, Clock, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatsBarProps {
  totalArticles: number
  countryCount: number
  lastUpdated: string | null
  isHealthy: boolean
  positiveCount?: number
  negativeCount?: number
  neutralCount?: number
}

function AnimatedNumber({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    if (value === 0) {
      setDisplayValue(0)
      return
    }

    const duration = 600
    const steps = 20
    const increment = value / steps
    let current = 0
    let step = 0

    const timer = setInterval(() => {
      step++
      current = Math.min(Math.round(increment * step), value)
      setDisplayValue(current)

      if (step >= steps) {
        clearInterval(timer)
        setDisplayValue(value)
      }
    }, duration / steps)

    return () => clearInterval(timer)
  }, [value])

  return <>{displayValue.toLocaleString()}</>
}

export default function StatsBar({
  totalArticles,
  countryCount,
  lastUpdated,
  isHealthy,
  positiveCount = 0,
  negativeCount = 0,
}: StatsBarProps) {
  const dominantSentiment =
    positiveCount > negativeCount
      ? 'positive'
      : negativeCount > positiveCount
        ? 'negative'
        : 'neutral'

  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-xs">
      {/* Live Status */}
      <div className="flex items-center gap-1.5">
        <div className="relative">
          <div
            className={`h-1.5 w-1.5 rounded-full ${isHealthy ? 'bg-positive' : 'bg-negative'}`}
          />
          {isHealthy && (
            <div className="absolute inset-0 h-1.5 w-1.5 animate-ping rounded-full bg-positive opacity-40" />
          )}
        </div>
        <span className={`text-2xs font-medium ${isHealthy ? 'text-positive' : 'text-negative'}`}>
          {isHealthy ? 'Live' : 'Offline'}
        </span>
      </div>

      <div className="hidden h-3 w-px bg-border sm:block" />

      {/* Articles */}
      <div className="flex items-center gap-1.5 text-text-secondary">
        <FileText className="h-3 w-3" />
        <span className="text-2xs">
          <span className="font-mono font-medium tabular-nums text-foreground">
            <AnimatedNumber value={totalArticles} />
          </span>{' '}
          articles
        </span>
      </div>

      {/* Countries */}
      <div className="flex items-center gap-1.5 text-text-secondary">
        <Globe2 className="h-3 w-3" />
        <span className="text-2xs">
          <span className="font-mono font-medium tabular-nums text-foreground">
            <AnimatedNumber value={countryCount} />
          </span>{' '}
          countries
        </span>
      </div>

      <div className="hidden h-3 w-px bg-border md:block" />

      {/* Dominant Sentiment */}
      <div className="hidden items-center gap-1.5 text-text-secondary md:flex">
        {dominantSentiment === 'positive' && (
          <>
            <TrendingUp className="h-3 w-3 text-positive" />
            <span className="text-2xs">
              Leaning <span className="font-medium text-positive">positive</span>
            </span>
          </>
        )}
        {dominantSentiment === 'negative' && (
          <>
            <TrendingDown className="h-3 w-3 text-negative" />
            <span className="text-2xs">
              Leaning <span className="font-medium text-negative">negative</span>
            </span>
          </>
        )}
        {dominantSentiment === 'neutral' && (
          <>
            <Minus className="h-3 w-3 text-neutral" />
            <span className="text-2xs">
              Mostly <span className="font-medium text-neutral">neutral</span>
            </span>
          </>
        )}
      </div>

      {/* Last Updated */}
      {lastUpdated && (
        <div className="ml-auto flex items-center gap-1.5 text-text-muted">
          <Clock className="h-3 w-3" />
          <span className="text-2xs">{formatRelativeTime(lastUpdated)}</span>
        </div>
      )}
    </div>
  )
}
