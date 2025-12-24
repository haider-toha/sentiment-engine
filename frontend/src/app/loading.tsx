export default function Loading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="relative w-20 h-20 mx-auto mb-6">
          {/* Animated globe */}
          <div className="absolute inset-0 rounded-full border-2 border-border" />
          <div className="absolute inset-2 rounded-full border border-text-muted animate-spin-slow" />
          <div className="absolute inset-4 rounded-full bg-surface" />
        </div>
        <p className="text-text-secondary">Loading sentiment data...</p>
      </div>
    </div>
  )
}

