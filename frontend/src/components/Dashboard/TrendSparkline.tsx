'use client'

import { useMemo } from 'react'
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { HourlyTrend } from '@/lib/api'
import { interpolateSentimentColor } from '@/lib/utils'

interface TrendSparklineProps {
  data: HourlyTrend[]
  height?: number
  showAxis?: boolean
}

export default function TrendSparkline({
  data,
  height = 60,
  showAxis = false,
}: TrendSparklineProps) {
  const chartData = useMemo(() => {
    return data.map((d) => ({
      ...d,
      time: new Date(d.hour).toLocaleTimeString([], { hour: '2-digit' }),
    }))
  }, [data])

  const latestSentiment = data.length > 0 ? data[data.length - 1].sentiment : 0
  const lineColor = interpolateSentimentColor(latestSentiment)

  if (data.length === 0) {
    return (
      <div 
        className="flex items-center justify-center text-text-muted text-sm"
        style={{ height }}
      >
        No data
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        {showAxis && (
          <>
            <XAxis
              dataKey="time"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#A8A29E' }}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[-1, 1]}
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#A8A29E' }}
              width={30}
            />
          </>
        )}
        <Tooltip
          contentStyle={{
            backgroundColor: '#FAFAF9',
            border: '1px solid #E7E5E4',
            borderRadius: '8px',
            fontSize: '12px',
          }}
          labelStyle={{ color: '#1C1917' }}
          formatter={(value: number) => [(value * 100).toFixed(1), 'Sentiment']}
        />
        <Line
          type="monotone"
          dataKey="sentiment"
          stroke={lineColor}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: lineColor }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

