// Design tokens — single source of truth for chain + status colors

export const CHAIN_COLORS: Record<string, { bg: string; text: string; border: string; hex: string }> = {
  aptos:    { bg: 'bg-indigo-500/10',  text: 'text-indigo-400',  border: 'border-indigo-500/20',  hex: '#627EEA' },
  solana:   { bg: 'bg-purple-500/10',  text: 'text-purple-400',  border: 'border-purple-500/20',  hex: '#9945FF' },
  ethereum: { bg: 'bg-blue-500/10',    text: 'text-blue-400',    border: 'border-blue-500/20',    hex: '#627EEA' },
  sepolia:  { bg: 'bg-blue-500/10',    text: 'text-blue-400',    border: 'border-blue-500/20',    hex: '#627EEA' },
  polygon:  { bg: 'bg-violet-500/10',  text: 'text-violet-400',  border: 'border-violet-500/20',  hex: '#8247E5' },
  mumbai:   { bg: 'bg-violet-500/10',  text: 'text-violet-400',  border: 'border-violet-500/20',  hex: '#8247E5' },
  base:     { bg: 'bg-blue-600/10',    text: 'text-blue-300',    border: 'border-blue-600/20',    hex: '#0052FF' },
  bitcoin:  { bg: 'bg-orange-500/10',  text: 'text-orange-400',  border: 'border-orange-500/20',  hex: '#F7931A' },
  evm:      { bg: 'bg-blue-500/10',    text: 'text-blue-400',    border: 'border-blue-500/20',    hex: '#627EEA' },
  default:  { bg: 'bg-zinc-700/40',    text: 'text-zinc-300',    border: 'border-zinc-600/40',    hex: '#6366f1' },
};

export function getChainColors(chain?: string) {
  const key = chain?.toLowerCase() ?? 'default';
  return CHAIN_COLORS[key] ?? CHAIN_COLORS.default;
}

export const CHAIN_SYMBOLS: Record<string, string> = {
  aptos: '⬢', solana: '◎', ethereum: 'Ξ', sepolia: 'Ξ',
  polygon: '⬡', mumbai: '⬡', base: 'Β', default: '●',
};

export function getChainSymbol(chain?: string) {
  return CHAIN_SYMBOLS[chain?.toLowerCase() ?? ''] ?? CHAIN_SYMBOLS.default;
}

export const STATUS_STYLES = {
  active:    { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', dot: 'bg-emerald-400' },
  triggered: { bg: 'bg-blue-500/10',    text: 'text-blue-400',    border: 'border-blue-500/20',    dot: 'bg-blue-400'    },
  paused:    { bg: 'bg-zinc-700/40',    text: 'text-zinc-400',    border: 'border-zinc-600/40',    dot: 'bg-zinc-400'    },
  error:     { bg: 'bg-red-500/10',     text: 'text-red-400',     border: 'border-red-500/20',     dot: 'bg-red-400'     },
};

export const PRIORITY_STYLES = {
  high:   { bg: 'bg-red-500/10',   text: 'text-red-400',   border: 'border-red-500/20',   icon: 'text-red-400'   },
  medium: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', icon: 'text-amber-400' },
  low:    { bg: 'bg-zinc-700/40',  text: 'text-zinc-400',  border: 'border-zinc-600/40',  icon: 'text-zinc-400'  },
};

// Deterministic gradient picker for token icons (consistent color per symbol)
const TOKEN_GRADIENTS = [
  'from-blue-500 to-cyan-500',
  'from-purple-500 to-pink-500',
  'from-emerald-500 to-teal-500',
  'from-amber-500 to-orange-500',
  'from-red-500 to-rose-500',
  'from-indigo-500 to-violet-500',
  'from-sky-500 to-blue-600',
  'from-green-500 to-emerald-600',
];

export function getTokenGradient(symbol: string): string {
  const index = symbol.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % TOKEN_GRADIENTS.length;
  return TOKEN_GRADIENTS[index];
}
