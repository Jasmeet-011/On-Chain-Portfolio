import React from 'react';

type Variant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'purple';

interface BadgeProps {
  variant?: Variant;
  children: React.ReactNode;
  dot?: boolean;
  className?: string;
}

const variantClasses: Record<Variant, string> = {
  default: 'bg-zinc-800 text-zinc-300 border-zinc-700/50',
  success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  warning: 'bg-amber-500/10  text-amber-400  border-amber-500/20',
  error:   'bg-red-500/10    text-red-400    border-red-500/20',
  info:    'bg-blue-500/10   text-blue-400   border-blue-500/20',
  purple:  'bg-purple-500/10 text-purple-400 border-purple-500/20',
};

const dotColors: Record<Variant, string> = {
  default: 'bg-zinc-400',
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  error:   'bg-red-400',
  info:    'bg-blue-400',
  purple:  'bg-purple-400',
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  children,
  dot,
  className = '',
}) => (
  <span
    className={[
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border',
      variantClasses[variant],
      className,
    ].join(' ')}
  >
    {dot && <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotColors[variant]}`} />}
    {children}
  </span>
);
