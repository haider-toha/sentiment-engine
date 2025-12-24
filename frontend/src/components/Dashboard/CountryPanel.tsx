'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useCountryDetail } from '@/hooks/useSentiment'
import { getCountryName } from '@/lib/countries'
import { interpolateSentimentColor, getSentimentLabel, cn } from '@/lib/utils'
import TrendSparkline from './TrendSparkline'
import HeadlinesList from './HeadlinesList'
import { X, Newspaper, TrendingUp, BarChart3, ChevronDown, Search } from 'lucide-react'

interface CountryPanelProps {
  countryCode: string
  onClose: () => void
  mobile?: boolean
}

type TabId = 'overview' | 'headlines'

export default function CountryPanel({ countryCode, onClose, mobile = false }: CountryPanelProps) {
  const { data, isLoading, error } = useCountryDetail(countryCode)
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  if (isLoading) {
    return (
      <Card className={cn('h-full overflow-hidden', mobile && 'rounded-none border-0')}>
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <Skeleton className="h-5 w-28" />
          <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7">
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
        <div className="p-4 space-y-3">
          <Skeleton className="h-20 w-full rounded-lg" />
          <Skeleton className="h-28 w-full rounded-lg" />
          <Skeleton className="h-40 w-full rounded-lg" />
        </div>
      </Card>
    )
  }

  if (error || !data) {
    return (
      <Card className={cn('h-full', mobile && 'rounded-none border-0')}>
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <h2 className="text-sm font-medium">{getCountryName(countryCode)}</h2>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-7 w-7">
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
        <div className="p-8 text-center">
          <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center mx-auto mb-3">
            <Search className="w-5 h-5 text-text-muted" />
          </div>
          <p className="text-sm text-text-muted">No data available</p>
        </div>
      </Card>
    )
  }

  const sentimentColor = interpolateSentimentColor(data.current_sentiment)
  const sentimentLabel = getSentimentLabel(data.current_sentiment)
  const badgeVariant = sentimentLabel.includes('Positive') 
    ? 'positive' 
    : sentimentLabel.includes('Negative') 
      ? 'negative' 
      : 'neutral'

  const tabs = [
    { id: 'overview' as TabId, label: 'Overview', icon: BarChart3 },
    { id: 'headlines' as TabId, label: `Headlines`, count: data.top_headlines.length, icon: Newspaper },
  ]

  return (
    <Card className={cn(
      'h-full overflow-hidden flex flex-col animate-slide-in-right',
      mobile && 'rounded-none border-0'
    )}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border/50 flex-shrink-0">
        <div>
          <h2 className="text-base font-medium">{data.country_name}</h2>
          <p className="text-2xs text-text-muted mt-0.5">
            {data.article_count.toLocaleString()} articles
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={onClose}
          className="h-7 w-7"
        >
          {mobile ? <ChevronDown className="w-3.5 h-3.5" /> : <X className="w-3.5 h-3.5" />}
        </Button>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-border/50 flex-shrink-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs transition-colors relative',
              activeTab === tab.id 
                ? 'text-foreground' 
                : 'text-text-muted hover:text-text-secondary'
            )}
          >
            <tab.icon className="w-3 h-3" />
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="text-2xs text-text-muted">({tab.count})</span>
            )}
            {activeTab === tab.id && (
              <div className="absolute bottom-0 left-3 right-3 h-px bg-foreground" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'overview' && (
          <div className="p-4 space-y-3">
            {/* Sentiment Score Card */}
            <div 
              className="rounded-lg p-3.5 border-l-2"
              style={{ 
                backgroundColor: `color-mix(in srgb, ${sentimentColor} 6%, var(--surface))`,
                borderLeftColor: sentimentColor
              }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-2xs text-text-secondary uppercase tracking-wider mb-1.5">
                    Current Sentiment
                  </p>
                  <p
                    className="text-2xl font-medium font-mono tabular-nums tracking-tight"
                    style={{ color: sentimentColor }}
                  >
                    {data.current_sentiment >= 0 ? '+' : ''}
                    {(data.current_sentiment * 100).toFixed(1)}
                  </p>
                </div>
                <Badge variant={badgeVariant} className="text-xs">
                  {sentimentLabel}
                </Badge>
              </div>
            </div>

            {/* 24h Trend */}
            <div className="bg-surface rounded-lg p-3.5">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-text-muted" />
                  <h3 className="text-xs font-medium">24h Trend</h3>
                </div>
                <span className="text-2xs text-text-muted font-mono">
                  {data.hourly_trend.length} pts
                </span>
              </div>
              <TrendSparkline 
                data={data.hourly_trend} 
                height={100} 
                showAxis 
              />
            </div>

            {/* Source Breakdown */}
            {Object.keys(data.source_breakdown).length > 0 && (
              <div className="bg-surface rounded-lg p-3.5">
                <div className="flex items-center gap-1.5 mb-2.5">
                  <BarChart3 className="w-3.5 h-3.5 text-text-muted" />
                  <h3 className="text-xs font-medium">Sources</h3>
                </div>
                <div className="space-y-2">
                  {Object.entries(data.source_breakdown)
                    .sort((a, b) => b[1] - a[1])
                    .map(([source, count]) => {
                      const total = Object.values(data.source_breakdown).reduce((a, b) => a + b, 0)
                      const percent = (count / total) * 100
                      
                      return (
                        <div key={source} className="flex items-center gap-2.5">
                          <span className="text-2xs text-text-secondary w-14 capitalize">
                            {source}
                          </span>
                          <div className="flex-1 h-1 bg-border/50 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-foreground/15 rounded-full"
                              style={{ width: `${percent}%` }}
                            />
                          </div>
                          <span className="text-2xs text-text-muted font-mono w-6 text-right">
                            {count}
                          </span>
                        </div>
                      )
                    })}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'headlines' && (
          <div className="p-4">
            <HeadlinesList 
              headlines={data.top_headlines} 
              maxItems={10}
              compact={!mobile}
            />
          </div>
        )}
      </div>
    </Card>
  )
}
