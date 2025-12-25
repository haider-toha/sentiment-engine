'use client'

import { useState } from 'react'
import { CountryData } from '@/lib/api'
import { interpolateSentimentColor, getSentimentLabel } from '@/lib/utils'
import { cn } from '@/lib/utils'
import { ChevronRight, ArrowUpDown, Globe2 } from 'lucide-react'

interface CountryListProps {
  countries: CountryData[]
  selectedCountry: string | null
  onSelect: (countryCode: string) => void
  sortBy?: 'sentiment' | 'articles' | 'name'
}

export default function CountryList({
  countries,
  selectedCountry,
  onSelect,
  sortBy: initialSort = 'articles',
}: CountryListProps) {
  const [sortBy, setSortBy] = useState(initialSort)

  const sortedCountries = [...countries].sort((a, b) => {
    switch (sortBy) {
      case 'sentiment':
        return b.sentiment_score - a.sentiment_score
      case 'articles':
        return b.article_count - a.article_count
      case 'name':
        return a.country_name.localeCompare(b.country_name)
      default:
        return 0
    }
  })

  if (sortedCountries.length === 0) {
    return (
      <div className="px-4 py-12 text-center">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-surface">
          <Globe2 className="h-5 w-5 text-text-muted" />
        </div>
        <p className="text-sm text-text-muted">No country data available</p>
      </div>
    )
  }

  const cycleSortBy = () => {
    const order: (typeof sortBy)[] = ['articles', 'sentiment', 'name']
    const currentIndex = order.indexOf(sortBy)
    setSortBy(order[(currentIndex + 1) % order.length])
  }

  const sortLabels = {
    articles: 'By activity',
    sentiment: 'By sentiment',
    name: 'Alphabetical',
  }

  return (
    <div>
      {/* Sort toggle */}
      <div className="border-b border-border/50 px-4 py-2">
        <button
          onClick={cycleSortBy}
          className="flex items-center gap-1.5 text-xs text-text-muted transition-colors hover:text-foreground"
        >
          <ArrowUpDown className="h-3 w-3" />
          <span>{sortLabels[sortBy]}</span>
        </button>
      </div>

      {/* Country list */}
      <div className="animate-stagger space-y-0.5 p-2">
        {sortedCountries.map((country, index) => {
          const color = interpolateSentimentColor(country.sentiment_score)
          const isSelected = selectedCountry === country.country_code
          const label = getSentimentLabel(country.sentiment_score)

          return (
            <button
              key={country.country_code}
              onClick={() => onSelect(country.country_code)}
              className={cn(
                'group flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left transition-all',
                isSelected ? 'bg-foreground text-background' : 'hover:bg-surface'
              )}
            >
              {/* Rank number */}
              <span
                className={cn(
                  'w-4 font-mono text-2xs tabular-nums',
                  isSelected ? 'text-background/50' : 'text-text-muted'
                )}
              >
                {index + 1}
              </span>

              {/* Sentiment indicator */}
              <div
                className="h-2 w-2 flex-shrink-0 rounded-full"
                style={{ backgroundColor: isSelected ? 'currentColor' : color }}
              />

              {/* Country info */}
              <div className="min-w-0 flex-1">
                <span className={cn('block truncate text-sm', isSelected && 'text-background')}>
                  {country.country_name}
                </span>
                <span
                  className={cn('text-2xs', isSelected ? 'text-background/50' : 'text-text-muted')}
                >
                  {country.article_count} articles
                </span>
              </div>

              {/* Sentiment value */}
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    'font-mono text-sm tabular-nums',
                    isSelected ? 'text-background' : ''
                  )}
                  style={{ color: isSelected ? undefined : color }}
                >
                  {country.sentiment_score >= 0 ? '+' : ''}
                  {(country.sentiment_score * 100).toFixed(0)}
                </span>
                <ChevronRight
                  className={cn(
                    'h-3.5 w-3.5 opacity-0 transition-opacity group-hover:opacity-100',
                    isSelected ? 'text-background/50 opacity-100' : 'text-text-muted'
                  )}
                />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
