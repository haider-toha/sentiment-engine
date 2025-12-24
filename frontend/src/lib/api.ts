/**
 * API client for the sentiment engine backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export interface CountryData {
  country_code: string
  country_name: string
  sentiment_score: number
  article_count: number
  trend?: number
}

export interface GlobalSentiment {
  countries: CountryData[]
  global_average: number
  total_articles: number
  last_updated: string
}

export interface HourlyTrend {
  hour: string
  sentiment: number
  articles: number
}

export interface Headline {
  id: number
  title: string
  source_name: string
  source_type?: string
  sentiment_score: number
  sentiment_label: string
  url: string
  published_at: string | null
  created_at?: string
}

export interface CountryDetail {
  country_code: string
  country_name: string
  current_sentiment: number
  article_count: number
  hourly_trend: HourlyTrend[]
  top_headlines: Headline[]
  source_breakdown: Record<string, number>
}

export interface HealthStatus {
  status: string
  last_collection: string | null
  articles_today: number
  model_loaded: boolean
  database_ok: boolean
}

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`)
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }
  
  return response.json()
}

export const api = {
  /**
   * Get global sentiment overview
   */
  getGlobalSentiment: () => fetchAPI<GlobalSentiment>('/sentiment/global'),
  
  /**
   * Get detailed data for a specific country
   */
  getCountryDetail: (countryCode: string, hours = 24) => 
    fetchAPI<CountryDetail>(`/sentiment/${countryCode}?hours=${hours}`),
  
  /**
   * Get headlines for a country
   */
  getHeadlines: (countryCode: string, limit = 20, sentiment?: string) => {
    let url = `/headlines/${countryCode}?limit=${limit}`
    if (sentiment) url += `&sentiment=${sentiment}`
    return fetchAPI<Headline[]>(url)
  },
  
  /**
   * Get global trends over time
   */
  getTrends: (hours = 24) => 
    fetchAPI<HourlyTrend[]>(`/trends?hours=${hours}`),
  
  /**
   * Get health status
   */
  getHealth: () => fetchAPI<HealthStatus>('/health'),
  
  /**
   * Trigger a data collection
   */
  triggerCollection: async () => {
    const response = await fetch(`${API_BASE}/collect/trigger`, {
      method: 'POST',
    })
    return response.json()
  },
}

