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
  const dominantSentiment = positiveCount > negativeCount 
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
            className={`w-1.5 h-1.5 rounded-full ${isHealthy ? 'bg-positive' : 'bg-negative'}`}
          />
          {isHealthy && (
            <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-positive animate-ping opacity-40" />
          )}
        </div>
        <span className={`text-2xs font-medium ${isHealthy ? 'text-positive' : 'text-negative'}`}>
          {isHealthy ? 'Live' : 'Offline'}
        </span>
      </div>

      <div className="w-px h-3 bg-border hidden sm:block" />

      {/* Articles */}
      <div className="flex items-center gap-1.5 text-text-secondary">
        <FileText className="w-3 h-3" />
        <span className="text-2xs">
          <span className="font-medium text-foreground font-mono tabular-nums">
            <AnimatedNumber value={totalArticles} />
          </span>
          {' '}articles
        </span>
      </div>

      {/* Countries */}
      <div className="flex items-center gap-1.5 text-text-secondary">
        <Globe2 className="w-3 h-3" />
        <span className="text-2xs">
          <span className="font-medium text-foreground font-mono tabular-nums">
            <AnimatedNumber value={countryCount} />
          </span>
          {' '}countries
        </span>
      </div>

      <div className="w-px h-3 bg-border hidden md:block" />

      {/* Dominant Sentiment */}
      <div className="hidden md:flex items-center gap-1.5 text-text-secondary">
        {dominantSentiment === 'positive' && (
          <>
            <TrendingUp className="w-3 h-3 text-positive" />
            <span className="text-2xs">Leaning <span className="text-positive font-medium">positive</span></span>
          </>
        )}
        {dominantSentiment === 'negative' && (
          <>
            <TrendingDown className="w-3 h-3 text-negative" />
            <span className="text-2xs">Leaning <span className="text-negative font-medium">negative</span></span>
          </>
        )}
        {dominantSentiment === 'neutral' && (
          <>
            <Minus className="w-3 h-3 text-neutral" />
            <span className="text-2xs">Mostly <span className="text-neutral font-medium">neutral</span></span>
          </>
        )}
      </div>

      {/* Last Updated */}
      {lastUpdated && (
        <div className="flex items-center gap-1.5 text-text-muted ml-auto">
          <Clock className="w-3 h-3" />
          <span className="text-2xs">
            {formatRelativeTime(lastUpdated)}
          </span>
        </div>
      )}
    </div>
  )
}
