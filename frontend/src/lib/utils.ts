import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get sentiment color based on score (-1 to 1)
 */
export function getSentimentColor(score: number): string {
  if (score > 0.2) return 'var(--positive)'
  if (score < -0.2) return 'var(--negative)'
  return 'var(--neutral)'
}

/**
 * Get sentiment label based on score
 */
export function getSentimentLabel(score: number): string {
  if (score >= 0.2) return 'Positive'
  if (score >= 0.05) return 'Leaning Positive'
  if (score > -0.05) return 'Neutral'
  if (score > -0.2) return 'Leaning Negative'
  return 'Negative'
}

/**
 * Format a number as percentage
 */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

/**
 * Format relative time
 */
export function formatRelativeTime(date: Date | string): string {
  const now = new Date()
  const then = new Date(date)
  const diffMs = now.getTime() - then.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return then.toLocaleDateString()
}

/**
 * Clamp a value between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

/**
 * Linear interpolation between two colors based on sentiment
 */
export function interpolateSentimentColor(score: number): string {
  // Clamp score to -1 to 1
  const s = clamp(score, -1, 1)

  // Color values
  const negative = { r: 196, g: 131, b: 122 } // #C4837A
  const neutral = { r: 184, g: 168, b: 152 } // #B8A898
  const positive = { r: 107, g: 142, b: 107 } // #6B8E6B

  let r, g, b

  if (s < 0) {
    // Interpolate between negative and neutral
    const t = s + 1 // 0 to 1
    r = Math.round(negative.r + (neutral.r - negative.r) * t)
    g = Math.round(negative.g + (neutral.g - negative.g) * t)
    b = Math.round(negative.b + (neutral.b - negative.b) * t)
  } else {
    // Interpolate between neutral and positive
    const t = s // 0 to 1
    r = Math.round(neutral.r + (positive.r - neutral.r) * t)
    g = Math.round(neutral.g + (positive.g - neutral.g) * t)
    b = Math.round(neutral.b + (positive.b - neutral.b) * t)
  }

  return `rgb(${r}, ${g}, ${b})`
}
