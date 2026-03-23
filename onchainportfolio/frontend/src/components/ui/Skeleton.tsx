import React from 'react';

interface SkeletonProps { className?: string; }

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => (
  <div className={`skeleton-shimmer rounded-md ${className}`} aria-hidden="true" />
);

export const SkeletonCard: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-5 space-y-3" aria-hidden="true">
    <div className="flex items-center gap-3">
      <Skeleton className="w-10 h-10 rounded-xl flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-3.5 w-2/3" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
    {Array.from({ length: lines - 1 }).map((_, i) => (
      <Skeleton key={i} className={`h-3 ${i % 2 === 0 ? 'w-full' : 'w-4/5'}`} />
    ))}
  </div>
);

export const SkeletonRow: React.FC<{ cols?: number }> = ({ cols = 4 }) => (
  <div className="flex items-center gap-4 px-5 py-3.5 border-b border-zinc-800/60" aria-hidden="true">
    <Skeleton className="w-8 h-8 rounded-full flex-shrink-0" />
    {Array.from({ length: cols - 1 }).map((_, i) => (
      <Skeleton key={i} className={`h-3.5 flex-1 ${i === 0 ? 'max-w-[120px]' : ''}`} />
    ))}
  </div>
);

export const SkeletonSummaryCards: React.FC = () => (
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" aria-hidden="true">
    {[...Array(4)].map((_, i) => (
      <div key={i} className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-5 space-y-3">
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="w-9 h-9 rounded-xl" />
        </div>
        <Skeleton className="h-8 w-28" />
        <Skeleton className="h-3 w-16" />
      </div>
    ))}
  </div>
);
