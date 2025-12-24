'use client'

import { cn } from '@/lib/utils'

interface SourceIconProps {
  source: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

const SOURCE_CONFIG: Record<string, { letter: string; label: string; color: string; bg: string }> = {
  reddit: { 
    letter: 'R', 
    label: 'Reddit', 
    color: 'text-source-reddit',
    bg: 'bg-source-reddit/8'
  },
  hn: { 
    letter: 'Y', 
    label: 'Hacker News', 
    color: 'text-source-hn',
    bg: 'bg-source-hn/8'
  },
  mastodon: { 
    letter: 'M', 
    label: 'Mastodon', 
    color: 'text-source-mastodon',
    bg: 'bg-source-mastodon/8'
  },
  rss: { 
    letter: 'R', 
    label: 'RSS', 
    color: 'text-source-rss',
    bg: 'bg-source-rss/8'
  },
  scraper: { 
    letter: 'W', 
    label: 'Web', 
    color: 'text-text-secondary',
    bg: 'bg-surface'
  },
}

const SIZES = {
  sm: 'w-4 h-4 text-2xs',
  md: 'w-5 h-5 text-2xs',
  lg: 'w-6 h-6 text-xs',
}

export function SourceIcon({ source, size = 'md', showLabel = false, className }: SourceIconProps) {
  const normalizedSource = source.toLowerCase()
  const config = SOURCE_CONFIG[normalizedSource] || SOURCE_CONFIG.scraper
  
  return (
    <div className={cn('flex items-center gap-1.5', className)}>
      <div 
        className={cn(
          'inline-flex items-center justify-center rounded font-medium font-mono',
          config.color,
          config.bg,
          SIZES[size]
        )}
      >
        {config.letter}
      </div>
      {showLabel && (
        <span className="text-2xs text-text-secondary">{config.label}</span>
      )}
    </div>
  )
}

export function getSourceUrl(source: string, query?: string): string {
  switch (source.toLowerCase()) {
    case 'reddit':
      return query ? `https://reddit.com/search?q=${encodeURIComponent(query)}` : 'https://reddit.com'
    case 'hn':
      return query ? `https://hn.algolia.com/?q=${encodeURIComponent(query)}` : 'https://news.ycombinator.com'
    case 'mastodon':
      return 'https://mastodon.social'
    default:
      return '#'
  }
}
