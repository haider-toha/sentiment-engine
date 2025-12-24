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
      <div className="text-center py-12 px-4">
        <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center mx-auto mb-3">
          <Globe2 className="w-5 h-5 text-text-muted" />
        </div>
        <p className="text-sm text-text-muted">No country data available</p>
      </div>
    )
  }

  const cycleSortBy = () => {
    const order: typeof sortBy[] = ['articles', 'sentiment', 'name']
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
      <div className="px-4 py-2 border-b border-border/50">
        <button
          onClick={cycleSortBy}
          className="flex items-center gap-1.5 text-xs text-text-muted hover:text-foreground transition-colors"
        >
          <ArrowUpDown className="w-3 h-3" />
          <span>{sortLabels[sortBy]}</span>
        </button>
      </div>

      {/* Country list */}
      <div className="p-2 space-y-0.5 animate-stagger">
        {sortedCountries.map((country, index) => {
          const color = interpolateSentimentColor(country.sentiment_score)
          const isSelected = selectedCountry === country.country_code
          const label = getSentimentLabel(country.sentiment_score)

          return (
            <button
              key={country.country_code}
              onClick={() => onSelect(country.country_code)}
              className={cn(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-md transition-all text-left group',
                isSelected
                  ? 'bg-foreground text-background'
                  : 'hover:bg-surface'
              )}
            >
              {/* Rank number */}
              <span className={cn(
                'w-4 text-2xs font-mono tabular-nums',
                isSelected ? 'text-background/50' : 'text-text-muted'
              )}>
                {index + 1}
              </span>

              {/* Sentiment indicator */}
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: isSelected ? 'currentColor' : color }}
              />

              {/* Country info */}
              <div className="flex-1 min-w-0">
                <span className={cn(
                  'text-sm truncate block',
                  isSelected && 'text-background'
                )}>
                  {country.country_name}
                </span>
                <span className={cn(
                  'text-2xs',
                  isSelected ? 'text-background/50' : 'text-text-muted'
                )}>
                  {country.article_count} articles
                </span>
              </div>
              
              {/* Sentiment value */}
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    'text-sm font-mono tabular-nums',
                    isSelected ? 'text-background' : ''
                  )}
                  style={{ color: isSelected ? undefined : color }}
                >
                  {country.sentiment_score >= 0 ? '+' : ''}
                  {(country.sentiment_score * 100).toFixed(0)}
                </span>
                <ChevronRight className={cn(
                  'w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity',
                  isSelected ? 'text-background/50 opacity-100' : 'text-text-muted'
                )} />
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
