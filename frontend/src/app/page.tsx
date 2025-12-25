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
  const [sentimentFilter, setSentimentFilter] = useState<
    'all' | 'positive' | 'neutral' | 'negative'
  >('all')
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
    ? data.countries.reduce((acc, c) => acc + (c.trend || 0), 0) / data.countries.length
    : undefined

  const positiveCountries = data?.countries.filter((c) => c.sentiment_score > 0.2) || []
  const negativeCountries = data?.countries.filter((c) => c.sentiment_score < -0.2) || []
  const neutralCountries =
    data?.countries.filter((c) => c.sentiment_score >= -0.2 && c.sentiment_score <= 0.2) || []

  const positiveCount = positiveCountries.length
  const negativeCount = negativeCountries.length
  const neutralCount = neutralCountries.length

  // Filter countries based on sentiment filter
  const filteredCountries =
    sentimentFilter === 'all'
      ? data?.countries || []
      : sentimentFilter === 'positive'
        ? positiveCountries
        : sentimentFilter === 'negative'
          ? negativeCountries
          : neutralCountries

  return (
    <main className="relative flex h-screen flex-col overflow-hidden bg-background">
      {/* Header */}
      <header className="border-b border-border/60">
        <div className="px-4 py-4 lg:px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Logo */}
              <div className="flex items-baseline gap-1.5">
                <h1 className="text-xl font-semibold tracking-tight">Sentiment</h1>
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
                <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
                <span className="hidden text-xs sm:inline">Refresh</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="border-b border-border/60 bg-surface/40">
        <div className="px-4 py-2.5 lg:px-6">
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
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - All Panels Stacked */}
        <div className="w-80 flex-shrink-0 overflow-y-auto border-r border-border/60 xl:w-96">
          <div className="space-y-4 p-4">
            {/* Global Sentiment Card */}
            {isLoading ? (
              <Card className="overflow-hidden">
                <CardContent className="p-4">
                  <Skeleton className="mb-3 h-2.5 w-16" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="mt-2.5 h-2.5 w-28" />
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
                onClick={() =>
                  setSentimentFilter(sentimentFilter === 'positive' ? 'all' : 'positive')
                }
                className={`cursor-pointer rounded-md border p-2.5 text-center transition-all ${
                  sentimentFilter === 'positive'
                    ? 'border-positive/40 bg-positive/15 ring-1 ring-positive/30'
                    : 'border-positive/10 bg-positive/5 hover:bg-positive/10'
                }`}
              >
                <div className="font-mono text-base font-medium tabular-nums text-positive">
                  {positiveCount}
                </div>
                <div className="mt-0.5 text-2xs text-text-muted">Positive</div>
              </button>
              <button
                onClick={() =>
                  setSentimentFilter(sentimentFilter === 'neutral' ? 'all' : 'neutral')
                }
                className={`cursor-pointer rounded-md border p-2.5 text-center transition-all ${
                  sentimentFilter === 'neutral'
                    ? 'border-neutral/40 bg-neutral/15 ring-1 ring-neutral/30'
                    : 'border-neutral/10 bg-neutral/5 hover:bg-neutral/10'
                }`}
              >
                <div className="font-mono text-base font-medium tabular-nums text-neutral">
                  {neutralCount}
                </div>
                <div className="mt-0.5 text-2xs text-text-muted">Neutral</div>
              </button>
              <button
                onClick={() =>
                  setSentimentFilter(sentimentFilter === 'negative' ? 'all' : 'negative')
                }
                className={`cursor-pointer rounded-md border p-2.5 text-center transition-all ${
                  sentimentFilter === 'negative'
                    ? 'border-negative/40 bg-negative/15 ring-1 ring-negative/30'
                    : 'border-negative/10 bg-negative/5 hover:bg-negative/10'
                }`}
              >
                <div className="font-mono text-base font-medium tabular-nums text-negative">
                  {negativeCount}
                </div>
                <div className="mt-0.5 text-2xs text-text-muted">Negative</div>
              </button>
            </div>

            {/* Country List */}
            <Card className="overflow-hidden">
              <div className="border-b border-border/50 px-4 py-3">
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
                        className="text-2xs text-text-muted transition-colors hover:text-foreground"
                      >
                        Clear
                      </button>
                    )}
                    <span className="font-mono text-2xs text-text-muted">
                      {filteredCountries.length}
                    </span>
                  </div>
                </div>
              </div>
              <div className="max-h-[240px] overflow-y-auto">
                {isLoading ? (
                  <div className="space-y-1.5 p-3">
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
              <Card className="flex flex-col items-center justify-center border-dashed p-5 text-center">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-surface">
                  <MapPin className="h-5 w-5 text-text-muted" />
                </div>
                <h3 className="mb-1 text-sm font-medium text-foreground">Select a country</h3>
                <p className="max-w-[180px] text-xs text-text-secondary">
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
        <div className="relative flex-1 bg-[#FAFAF9]">
          {isLoading ? (
            <div className="flex h-full w-full flex-col items-center justify-center gap-3">
              <div className="relative">
                <Skeleton className="h-48 w-48 rounded-full" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <RefreshCw className="h-8 w-8 animate-spin text-text-muted" />
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
              <div className="glass absolute bottom-6 left-1/2 -translate-x-1/2 rounded-full border border-border/40 px-5 py-2.5 shadow-soft">
                <Legend />
              </div>

              {/* Interaction hint */}
              <div className="glass absolute right-4 top-4 rounded-md border border-border/40 px-3 py-1.5 text-xs text-text-secondary">
                Drag to rotate · Scroll to zoom · Click marker for details
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer - positioned at bottom of sidebar */}
      <div className="absolute bottom-0 left-0 w-80 border-r border-t border-border/60 bg-background/95 backdrop-blur-sm xl:w-96">
        <div className="px-4 py-3">
          <p className="text-center text-2xs text-text-muted">Haider © 2025</p>
        </div>
      </div>

      {/* Mobile slide-up panel */}
      {selectedCountry && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className={`absolute inset-0 bg-foreground/15 backdrop-blur-sm transition-opacity duration-200 ${showPanel ? 'opacity-100' : 'opacity-0'}`}
            onClick={() => handleCountrySelect(null)}
          />
          <div
            className={`absolute bottom-0 left-0 right-0 max-h-[85vh] transition-transform duration-200 ${showPanel ? 'translate-y-0' : 'translate-y-full'}`}
          >
            <div className="overflow-hidden rounded-t-xl bg-background shadow-lg">
              <div className="flex justify-center py-1.5">
                <div className="h-0.5 w-8 rounded-full bg-border" />
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
