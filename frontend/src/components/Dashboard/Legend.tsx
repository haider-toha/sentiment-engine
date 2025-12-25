'use client'

export default function Legend() {
  const items = [
    { color: 'bg-positive', label: 'Positive' },
    { color: 'bg-neutral', label: 'Neutral' },
    { color: 'bg-negative', label: 'Negative' },
  ]

  return (
    <div className="flex items-center gap-4 text-2xs">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5">
          <div className={`h-2 w-2 rounded-full ${item.color}`} />
          <span className="text-text-secondary">{item.label}</span>
        </div>
      ))}
    </div>
  )
}
