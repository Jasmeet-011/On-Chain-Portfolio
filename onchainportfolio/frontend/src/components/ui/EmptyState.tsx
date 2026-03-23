import React from 'react';

interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  className = '',
}) => (
  <div className={`flex flex-col items-center justify-center py-16 px-6 text-center ${className}`}>
    {Icon && (
      <div className="w-14 h-14 rounded-2xl bg-zinc-800/80 border border-zinc-700/50 flex items-center justify-center mb-5">
        <Icon className="w-7 h-7 text-zinc-400" />
      </div>
    )}
    <p className="text-base font-semibold text-white mb-1.5">{title}</p>
    {description && (
      <p className="text-sm text-zinc-400 max-w-xs mb-5 leading-relaxed">{description}</p>
    )}
    {action && <div>{action}</div>}
  </div>
);
