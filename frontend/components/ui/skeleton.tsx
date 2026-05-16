export function JobCardSkeleton() {
  return (
    <div className="glass p-5 space-y-3 animate-pulse">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-white/[0.07] rounded w-3/4" />
          <div className="h-3 bg-white/[0.04] rounded w-1/2" />
        </div>
        <div className="h-6 w-12 bg-white/[0.07] rounded-full shrink-0" />
      </div>
      <div className="space-y-1.5">
        <div className="h-3 bg-white/[0.04] rounded w-full" />
        <div className="h-3 bg-white/[0.04] rounded w-5/6" />
      </div>
      <div className="flex gap-2 pt-1">
        <div className="h-11 w-24 bg-white/[0.04] rounded-lg" />
        <div className="h-11 w-14 bg-white/[0.04] rounded-lg" />
        <div className="h-11 w-28 bg-white/[0.04] rounded-lg" />
      </div>
    </div>
  )
}

export function ApplicationRowSkeleton() {
  return (
    <div className="glass p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between animate-pulse">
      <div className="flex-1 space-y-2 min-w-0">
        <div className="h-4 bg-white/[0.07] rounded w-2/3" />
        <div className="h-3 bg-white/[0.04] rounded w-1/2" />
      </div>
      <div className="flex items-center gap-2 sm:shrink-0">
        <div className="h-11 w-10 bg-white/[0.04] rounded-lg" />
        <div className="h-11 w-28 bg-white/[0.04] rounded-lg" />
      </div>
    </div>
  )
}
