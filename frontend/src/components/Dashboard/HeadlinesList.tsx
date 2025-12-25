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
      <div className="py-10 text-center">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-surface">
          <FileText className="h-5 w-5 text-text-muted" />
        </div>
        <p className="text-sm text-text-muted">No headlines available</p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-2', !compact && 'animate-stagger')}>
      {displayHeadlines.map((headline) => {
        const sentimentColor = interpolateSentimentColor(headline.sentiment_score)
        const badgeVariant =
          headline.sentiment_label === 'positive'
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
              'group transition-all duration-150',
              compact ? 'p-2.5' : 'p-3'
            )}
          >
            <div className="flex items-start gap-2.5">
              {/* Source icon */}
              <div className="flex-shrink-0 pt-0.5">
                <SourceIcon source={headline.source_type || 'rss'} size={compact ? 'sm' : 'md'} />
              </div>

              {/* Content */}
              <div className="min-w-0 flex-1">
                <h4
                  className={cn(
                    'line-clamp-2 leading-snug transition-colors group-hover:text-foreground',
                    compact ? 'text-xs' : 'text-sm'
                  )}
                >
                  {headline.title}
                </h4>

                <div className="mt-1.5 flex items-center gap-1.5">
                  <span
                    className={cn(
                      'max-w-[100px] truncate text-text-muted',
                      compact ? 'text-2xs' : 'text-xs'
                    )}
                  >
                    {headline.source_name}
                  </span>
                  {headline.published_at && (
                    <>
                      <span className="text-2xs text-text-muted">·</span>
                      <span className={cn('text-text-muted', compact ? 'text-2xs' : 'text-xs')}>
                        {formatRelativeTime(headline.published_at)}
                      </span>
                    </>
                  )}
                </div>
              </div>

              {/* Right side */}
              <div className="flex flex-shrink-0 flex-col items-end gap-1.5">
                <Badge variant={badgeVariant} className={compact ? 'px-1.5 py-0 text-2xs' : ''}>
                  {compact
                    ? (headline.sentiment_score >= 0 ? '+' : '') +
                      (headline.sentiment_score * 100).toFixed(0)
                    : headline.sentiment_label}
                </Badge>
                <ArrowUpRight
                  className={cn(
                    'text-text-muted opacity-0 transition-opacity group-hover:opacity-100',
                    compact ? 'h-3 w-3' : 'h-3.5 w-3.5'
                  )}
                />
              </div>
            </div>

            {/* Sentiment bar */}
            {!compact && (
              <div className="mt-2.5 flex items-center gap-2.5">
                <div className="h-0.5 flex-1 overflow-hidden rounded-full bg-border/50">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${((headline.sentiment_score + 1) / 2) * 100}%`,
                      backgroundColor: sentimentColor,
                    }}
                  />
                </div>
                <span className="font-mono text-2xs tabular-nums" style={{ color: sentimentColor }}>
                  {headline.sentiment_score >= 0 ? '+' : ''}
                  {(headline.sentiment_score * 100).toFixed(0)}
                </span>
              </div>
            )}
          </a>
        )
      })}
    </div>
  )
}
