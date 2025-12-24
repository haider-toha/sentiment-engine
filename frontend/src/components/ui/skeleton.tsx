import { cn } from '@/lib/utils'

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-lg bg-surface skeleton-shimmer',
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
