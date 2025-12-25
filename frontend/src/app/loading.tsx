export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="relative mx-auto mb-6 h-20 w-20">
          {/* Animated globe */}
          <div className="absolute inset-0 rounded-full border-2 border-border" />
          <div className="absolute inset-2 animate-spin-slow rounded-full border border-text-muted" />
          <div className="absolute inset-4 rounded-full bg-surface" />
        </div>
        <p className="text-text-secondary">Loading sentiment data...</p>
      </div>
    </div>
  )
}
