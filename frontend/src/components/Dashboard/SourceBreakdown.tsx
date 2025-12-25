'use client'

import { useMemo } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

interface SourceBreakdownProps {
  data: Record<string, number>
}

const SOURCE_COLORS: Record<string, string> = {
  rss: '#6B8E6B',
  reddit: '#C4837A',
  mastodon: '#B8A898',
  hn: '#78716C',
  scraper: '#525252',
}

const SOURCE_LABELS: Record<string, string> = {
  rss: 'RSS Feeds',
  reddit: 'Reddit',
  mastodon: 'Mastodon',
  hn: 'Hacker News',
  scraper: 'Web Scraping',
}

export default function SourceBreakdown({ data }: SourceBreakdownProps) {
  const chartData = useMemo(() => {
    return Object.entries(data).map(([source, count]) => ({
      name: SOURCE_LABELS[source] || source,
      value: count,
      color: SOURCE_COLORS[source] || '#A8A29E',
    }))
  }, [data])

  if (chartData.length === 0) {
    return <div className="py-8 text-center text-sm text-text-muted">No source data available</div>
  }

  const total = chartData.reduce((acc, d) => acc + d.value, 0)

  return (
    <div className="flex items-center gap-4">
      <div className="h-24 w-24 flex-shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={25}
              outerRadius={40}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#FAFAF9',
                border: '1px solid #E7E5E4',
                borderRadius: '8px',
                fontSize: '12px',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="flex-1 space-y-1.5">
        {chartData.map((entry) => (
          <div key={entry.name} className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-text-secondary">{entry.name}</span>
            </div>
            <span className="tabular-nums text-text-muted">
              {entry.value} ({Math.round((entry.value / total) * 100)}%)
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
