'use client'

import { useState, useEffect, useCallback } from 'react'
import { useGlobalSentiment, useHealth } from '@/hooks/useSentiment'
import GlobeWrapper from '@/components/Globe/GlobeWrapper'
import SentimentCard from '@/components/Dashboard/SentimentCard'
import CountryList from '@/components/Dashboard/CountryList'
import CountryPanel from '@/components/Dashboard/CountryPanel'
import StatsBar from '@/components/Dashboard/StatsBar'
import Legend from '@/components/Dashboard/Legend'
import KeyboardHints from '@/components/Dashboard/KeyboardHints'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { RefreshCw, Globe2, MapPin, X } from 'lucide-react'

export default function Home() {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [showPanel, setShowPanel] = useState(false)
  const [sentimentFilter, setSentimentFilter] = useState<'all' | 'positive' | 'neutral' | 'negative'>('all')
  const { data, isLoading, error, refresh } = useGlobalSentiment()
  const { data: health, isHealthy } = useHealth()

  // Handle country selection with panel animation
  const handleCountrySelect = useCallback((countryCode: string | null) => {
    if (countryCode) {
      setSelectedCountry(countryCode)
      setShowPanel(true)
    } else {
      setShowPanel(false)
      setTimeout(() => setSelectedCountry(null), 200)
    }
  }, [])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedCountry) {
        handleCountrySelect(null)
      }
      if (e.key === 'r' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        refresh()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedCountry, handleCountrySelect, refresh])

  // Calculate trend from previous update
  const globalTrend = data?.countries.length 
    ? (data.countries.reduce((acc, c) => acc + (c.trend || 0), 0) / data.countries.length)
    : undefined

  const positiveCountries = data?.countries.filter(c => c.sentiment_score > 0.2) || []
  const negativeCountries = data?.countries.filter(c => c.sentiment_score < -0.2) || []
  const neutralCountries = data?.countries.filter(c => c.sentiment_score >= -0.2 && c.sentiment_score <= 0.2) || []
  
  const positiveCount = positiveCountries.length
  const negativeCount = negativeCountries.length
  const neutralCount = neutralCountries.length
  
  // Filter countries based on sentiment filter
  const filteredCountries = sentimentFilter === 'all' 
    ? (data?.countries || [])
    : sentimentFilter === 'positive'
      ? positiveCountries
      : sentimentFilter === 'negative'
        ? negativeCountries
        : neutralCountries

  return (
    <main className="h-screen flex flex-col bg-background overflow-hidden relative">
      {/* Header */}
      <header className="border-b border-border/60">
        <div className="px-4 lg:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Logo */}
              <div className="flex items-baseline gap-1.5">
                <h1 className="text-xl font-semibold tracking-tight">
                  Sentiment
                </h1>
                <span className="text-xl font-light text-text-secondary">Engine</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <KeyboardHints />
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={() => refresh()}
                disabled={isLoading}
                className="gap-1.5"
              >
                <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline text-xs">Refresh</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="border-b border-border/60 bg-surface/40">
        <div className="px-4 lg:px-6 py-2.5">
          <StatsBar
            totalArticles={data?.total_articles || 0}
            countryCount={data?.countries.length || 0}
            lastUpdated={data?.last_updated || null}
            isHealthy={isHealthy}
            positiveCount={positiveCount}
            negativeCount={negativeCount}
            neutralCount={neutralCount}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - All Panels Stacked */}
        <div className="w-80 xl:w-96 flex-shrink-0 border-r border-border/60 overflow-y-auto">
          <div className="p-4 space-y-4">
            {/* Global Sentiment Card */}
            {isLoading ? (
              <Card className="overflow-hidden">
                <CardContent className="p-4">
                  <Skeleton className="h-2.5 w-16 mb-3" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-2.5 w-28 mt-2.5" />
                </CardContent>
              </Card>
            ) : (
              <SentimentCard
                title="Global Average"
                value={data?.global_average || 0}
                subtitle={`${data?.total_articles?.toLocaleString() || 0} articles`}
                trend={globalTrend}
                large
              />
            )}

            {/* Quick Stats Grid - Clickable Filters */}
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setSentimentFilter(sentimentFilter === 'positive' ? 'all' : 'positive')}
                className={`rounded-md p-2.5 text-center border transition-all cursor-pointer ${
                  sentimentFilter === 'positive'
                    ? 'bg-positive/15 border-positive/40 ring-1 ring-positive/30'
                    : 'bg-positive/5 border-positive/10 hover:bg-positive/10'
                }`}
              >
                <div className="text-base font-medium text-positive font-mono tabular-nums">
                  {positiveCount}
                </div>
                <div className="text-2xs text-text-muted mt-0.5">Positive</div>
              </button>
              <button
                onClick={() => setSentimentFilter(sentimentFilter === 'neutral' ? 'all' : 'neutral')}
                className={`rounded-md p-2.5 text-center border transition-all cursor-pointer ${
                  sentimentFilter === 'neutral'
                    ? 'bg-neutral/15 border-neutral/40 ring-1 ring-neutral/30'
                    : 'bg-neutral/5 border-neutral/10 hover:bg-neutral/10'
                }`}
              >
                <div className="text-base font-medium text-neutral font-mono tabular-nums">
                  {neutralCount}
                </div>
                <div className="text-2xs text-text-muted mt-0.5">Neutral</div>
              </button>
              <button
                onClick={() => setSentimentFilter(sentimentFilter === 'negative' ? 'all' : 'negative')}
                className={`rounded-md p-2.5 text-center border transition-all cursor-pointer ${
                  sentimentFilter === 'negative'
                    ? 'bg-negative/15 border-negative/40 ring-1 ring-negative/30'
                    : 'bg-negative/5 border-negative/10 hover:bg-negative/10'
                }`}
              >
                <div className="text-base font-medium text-negative font-mono tabular-nums">
                  {negativeCount}
                </div>
                <div className="text-2xs text-text-muted mt-0.5">Negative</div>
              </button>
            </div>

            {/* Country List */}
            <Card className="overflow-hidden">
              <div className="px-4 py-3 border-b border-border/50">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-medium">
                    Countries
                    {sentimentFilter !== 'all' && (
                      <span className="ml-1.5 text-2xs font-normal text-text-muted">
                        ({sentimentFilter})
                      </span>
                    )}
                  </h2>
                  <div className="flex items-center gap-2">
                    {sentimentFilter !== 'all' && (
                      <button
                        onClick={() => setSentimentFilter('all')}
                        className="text-2xs text-text-muted hover:text-foreground transition-colors"
                      >
                        Clear
                      </button>
                    )}
                    <span className="text-2xs text-text-muted font-mono">
                      {filteredCountries.length}
                    </span>
                  </div>
                </div>
              </div>
              <div className="max-h-[240px] overflow-y-auto">
                {isLoading ? (
                  <div className="p-3 space-y-1.5">
                    {[...Array(5)].map((_, i) => (
                      <Skeleton key={i} className="h-10 w-full rounded-md" />
                    ))}
                  </div>
                ) : (
                  <CountryList
                    countries={filteredCountries}
                    selectedCountry={selectedCountry}
                    onSelect={handleCountrySelect}
                    sortBy="articles"
                  />
                )}
              </div>
            </Card>

            {/* Country Detail Panel */}
            {selectedCountry ? (
              <CountryPanel
                countryCode={selectedCountry}
                onClose={() => handleCountrySelect(null)}
              />
            ) : (
              <Card className="flex flex-col items-center justify-center text-center p-5 border-dashed">
                <div className="w-10 h-10 rounded-lg bg-surface flex items-center justify-center mb-3">
                  <MapPin className="w-5 h-5 text-text-muted" />
                </div>
                <h3 className="text-sm font-medium text-foreground mb-1">Select a country</h3>
                <p className="text-xs text-text-secondary max-w-[180px]">
                  Click on a country from the list or globe to view details
                </p>
                <div className="mt-4 flex items-center gap-1.5 text-2xs text-text-muted">
                  <span className="kbd">↑</span>
                  <span className="kbd">↓</span>
                  <span>to navigate</span>
                </div>
              </Card>
            )}
          </div>
        </div>

        {/* Right - Globe (takes remaining space) */}
        <div className="flex-1 relative bg-[#FAFAF9]">
          {isLoading ? (
            <div className="w-full h-full flex flex-col items-center justify-center gap-3">
              <div className="relative">
                <Skeleton className="w-48 h-48 rounded-full" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <RefreshCw className="w-8 h-8 text-text-muted animate-spin" />
                </div>
              </div>
              <p className="text-sm text-text-muted">Loading sentiment data...</p>
            </div>
          ) : (
            <>
              <GlobeWrapper
                countries={data?.countries || []}
                onCountrySelect={handleCountrySelect}
                selectedCountry={selectedCountry}
              />
              
              {/* Legend overlay */}
              <div className="absolute bottom-6 left-1/2 -translate-x-1/2 glass px-5 py-2.5 rounded-full border border-border/40 shadow-soft">
                <Legend />
              </div>
              
              {/* Interaction hint */}
              <div className="absolute top-4 right-4 glass px-3 py-1.5 rounded-md text-xs text-text-secondary border border-border/40">
                Drag to rotate · Scroll to zoom · Click marker for details
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer - positioned at bottom of sidebar */}
      <div className="absolute bottom-0 left-0 w-80 xl:w-96 border-t border-r border-border/60 bg-background/95 backdrop-blur-sm">
        <div className="px-4 py-3">
          <p className="text-2xs text-text-muted text-center">
            Haider © 2025
          </p>
        </div>
      </div>

      {/* Mobile slide-up panel */}
      {selectedCountry && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div 
            className={`absolute inset-0 bg-foreground/15 backdrop-blur-sm transition-opacity duration-200 ${showPanel ? 'opacity-100' : 'opacity-0'}`}
            onClick={() => handleCountrySelect(null)}
          />
          <div className={`absolute bottom-0 left-0 right-0 max-h-[85vh] transition-transform duration-200 ${showPanel ? 'translate-y-0' : 'translate-y-full'}`}>
            <div className="bg-background rounded-t-xl shadow-lg overflow-hidden">
              <div className="flex justify-center py-1.5">
                <div className="w-8 h-0.5 rounded-full bg-border" />
              </div>
              <div className="max-h-[80vh] overflow-y-auto">
                <CountryPanel
                  countryCode={selectedCountry}
                  onClose={() => handleCountrySelect(null)}
                  mobile
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  )
}
