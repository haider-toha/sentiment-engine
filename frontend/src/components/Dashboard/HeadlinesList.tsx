'use client'

import { Headline } from '@/lib/api'
import { Badge } from '@/components/ui/badge'
import { SourceIcon } from '@/components/ui/source-icon'
import { formatRelativeTime, interpolateSentimentColor } from '@/lib/utils'
import { ArrowUpRight, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

interface HeadlinesListProps {
  headlines: Headline[]
  maxItems?: number
  compact?: boolean
}

export default function HeadlinesList({ 
  headlines, 
  maxItems = 10,
  compact = false,
}: HeadlinesListProps) {
  const displayHeadlines = headlines.slice(0, maxItems)

  if (displayHeadlines.length === 0) {
    return (
      <div className="text-center py-10">
        <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center mx-auto mb-3">
          <FileText className="w-5 h-5 text-text-muted" />
        </div>
        <p className="text-sm text-text-muted">No headlines available</p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-2', !compact && 'animate-stagger')}>
      {displayHeadlines.map((headline) => {
        const sentimentColor = interpolateSentimentColor(headline.sentiment_score)
        const badgeVariant = headline.sentiment_label === 'positive' 
          ? 'positive' 
          : headline.sentiment_label === 'negative' 
            ? 'negative' 
            : 'neutral'

        return (
          <a
            key={headline.id}
            href={headline.url}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              'block rounded-lg border border-border/50 hover:border-border',
              'bg-surface-elevated hover:bg-surface',
              'transition-all duration-150 group',
              compact ? 'p-2.5' : 'p-3'
            )}
          >
            <div className="flex items-start gap-2.5">
              {/* Source icon */}
              <div className="flex-shrink-0 pt-0.5">
                <SourceIcon 
                  source={headline.source_type || 'rss'} 
                  size={compact ? 'sm' : 'md'}
                />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h4 className={cn(
                  'leading-snug line-clamp-2 group-hover:text-foreground transition-colors',
                  compact ? 'text-xs' : 'text-sm'
                )}>
                  {headline.title}
                </h4>
                
                <div className="flex items-center gap-1.5 mt-1.5">
                  <span className={cn(
                    'text-text-muted truncate max-w-[100px]',
                    compact ? 'text-2xs' : 'text-xs'
                  )}>
                    {headline.source_name}
                  </span>
                  {headline.published_at && (
                    <>
                      <span className="text-text-muted text-2xs">·</span>
                      <span className={cn(
                        'text-text-muted',
                        compact ? 'text-2xs' : 'text-xs'
                      )}>
                        {formatRelativeTime(headline.published_at)}
                      </span>
                    </>
                  )}
                </div>
              </div>
              
              {/* Right side */}
              <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                <Badge variant={badgeVariant} className={compact ? 'text-2xs px-1.5 py-0' : ''}>
                  {compact 
                    ? (headline.sentiment_score >= 0 ? '+' : '') + (headline.sentiment_score * 100).toFixed(0)
                    : headline.sentiment_label
                  }
                </Badge>
                <ArrowUpRight className={cn(
                  'text-text-muted opacity-0 group-hover:opacity-100 transition-opacity',
                  compact ? 'w-3 h-3' : 'w-3.5 h-3.5'
                )} />
              </div>
            </div>
            
            {/* Sentiment bar */}
            {!compact && (
              <div className="mt-2.5 flex items-center gap-2.5">
                <div className="flex-1 h-0.5 bg-border/50 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${((headline.sentiment_score + 1) / 2) * 100}%`,
                      backgroundColor: sentimentColor,
                    }}
                  />
                </div>
                <span 
                  className="text-2xs font-mono tabular-nums"
                  style={{ color: sentimentColor }}
                >
                  {headline.sentiment_score >= 0 ? '+' : ''}{(headline.sentiment_score * 100).toFixed(0)}
                </span>
              </div>
            )}
          </a>
        )
      })}
    </div>
  )
}
