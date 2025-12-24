'use client'

import { Card, CardContent } from '@/components/ui/card'
import { interpolateSentimentColor, getSentimentLabel } from '@/lib/utils'
import { TrendingUp, TrendingDown, Minus, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SentimentCardProps {
  title: string
  value: number
  subtitle?: string
  trend?: number
  className?: string
  large?: boolean
}

export default function SentimentCard({
  title,
  value,
  subtitle,
  trend,
  className,
  large = false,
}: SentimentCardProps) {
  const color = interpolateSentimentColor(value)
  const label = getSentimentLabel(value)

  const TrendIcon = trend && trend > 0.05 
    ? TrendingUp 
    : trend && trend < -0.05 
      ? TrendingDown 
      : Minus

  const glowClass = value > 0.2 
    ? 'shadow-glow-positive' 
    : value < -0.2 
      ? 'shadow-glow-negative' 
      : 'shadow-glow-neutral'

  return (
    <Card className={cn('overflow-hidden', glowClass, className)}>
      {/* Colored accent bar */}
      <div 
        className="h-0.5 w-full"
        style={{ backgroundColor: color }}
      />
      
      <CardContent className={cn('p-4', large && 'p-5')}>
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-1.5 text-text-secondary">
            <Activity className="w-3 h-3" />
            <span className="text-2xs font-medium uppercase tracking-wider">{title}</span>
          </div>
          
          {trend !== undefined && (
            <div className={cn(
              'flex items-center gap-0.5 px-1.5 py-0.5 rounded text-2xs font-medium font-mono',
              trend > 0.05 ? 'bg-positive/8 text-positive' :
              trend < -0.05 ? 'bg-negative/8 text-negative' :
              'bg-neutral/8 text-neutral'
            )}>
              <TrendIcon className="w-2.5 h-2.5" />
              <span className="tabular-nums">
                {trend >= 0 ? '+' : ''}{(trend * 100).toFixed(1)}
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-baseline gap-2">
          <div
            className={cn(
              'font-medium font-mono tabular-nums tracking-tight',
              large ? 'text-3xl' : 'text-2xl'
            )}
            style={{ color }}
          >
            {value >= 0 ? '+' : ''}{(value * 100).toFixed(1)}
          </div>
          <span 
            className="text-sm"
            style={{ color }}
          >
            {label}
          </span>
        </div>
        
        {subtitle && (
          <p className="text-2xs text-text-muted mt-2">
            {subtitle}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
