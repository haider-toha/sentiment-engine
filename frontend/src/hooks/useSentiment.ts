'use client'

import useSWR from 'swr'
import { api, GlobalSentiment, CountryDetail, HealthStatus, Headline } from '@/lib/api'

/**
 * Hook for fetching global sentiment data
 */
export function useGlobalSentiment() {
  const { data, error, isLoading, mutate } = useSWR<GlobalSentiment>(
    'global-sentiment',
    () => api.getGlobalSentiment(),
    {
      refreshInterval: 60000, // Refresh every minute
      revalidateOnFocus: true,
    }
  )

  return {
    data,
    error,
    isLoading,
    refresh: mutate,
  }
}

/**
 * Hook for fetching country detail data with headlines from dedicated endpoint
 */
export function useCountryDetail(countryCode: string | null) {
  // Create stable fetcher functions
  const countryFetcher = async () => {
    if (!countryCode) return null
    return api.getCountryDetail(countryCode)
  }
  
  const headlinesFetcher = async () => {
    if (!countryCode) return null
    return api.getHeadlines(countryCode, 20)
  }
  
  // Both hooks must always be called in the same order
  const { data: countryData, error: countryError, isLoading: countryLoading, mutate } = useSWR<CountryDetail | null>(
    countryCode ? `country-${countryCode}` : null,
    countryFetcher,
    {
      refreshInterval: 60000,
    }
  )
  
  // Fetch headlines separately from the dedicated endpoint (which includes URLs)
  const { data: headlines, error: headlinesError, isLoading: headlinesLoading } = useSWR<Headline[] | null>(
    countryCode ? `headlines-${countryCode}` : null,
    headlinesFetcher,
    {
      refreshInterval: 60000,
    }
  )
  
  // Merge headlines into country data
  const data = countryData ? {
    ...countryData,
    top_headlines: headlines || countryData.top_headlines,
  } : undefined

  return {
    data,
    error: countryError || headlinesError,
    isLoading: countryLoading || headlinesLoading,
    refresh: mutate,
  }
}

/**
 * Hook for fetching health status
 */
export function useHealth() {
  const { data, error, isLoading } = useSWR<HealthStatus>(
    'health',
    () => api.getHealth(),
    {
      refreshInterval: 30000,
    }
  )

  return {
    data,
    error,
    isLoading,
    isHealthy: data?.status === 'healthy',
  }
}

/**
 * Hook for fetching trends
 */
export function useTrends(hours = 24) {
  const { data, error, isLoading } = useSWR(
    `trends-${hours}`,
    () => api.getTrends(hours),
    {
      refreshInterval: 60000,
    }
  )

  return {
    data,
    error,
    isLoading,
  }
}

