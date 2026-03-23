import React from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress, formatAmount, formatUSD } from "../utils";
import { Copy, Check, TrendingUp, TrendingDown } from "lucide-react";
import { getChainColors, getTokenGradient } from "../utils/tokens";

interface TokenBalance {
  symbol: string;
  address: string;
  decimals: number;
  raw: string;
  amount: number;
  usd_price?: number;
  usd_value?: number;
  change_24h?: number | null;
  wallet_name?: string;
  wallet_address?: string;
  chain?: string;
}

interface Props {
  balances: TokenBalance[];
  showWalletColumn?: boolean;
}

// Format a ±percentage value with sign and 2 decimal places
function formatPct(val?: number | null): string | null {
  if (val == null || isNaN(val)) return null;
  const sign = val >= 0 ? "+" : "";
  return `${sign}${val.toFixed(2)}%`;
}

const BalancesTable: React.FC<Props> = ({ balances, showWalletColumn = true }) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";
  const [copiedAddress, setCopiedAddress] = React.useState<string | null>(null);

  if (!balances || balances.length === 0) return null;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedAddress(text);
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  const ChainBadge = ({ chain }: { chain?: string }) => {
    if (!chain) return null;
    const c = getChainColors(chain);
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}>
        {chain.charAt(0).toUpperCase() + chain.slice(1)}
      </span>
    );
  };

  const TokenIcon = ({ symbol }: { symbol: string }) => (
    <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${getTokenGradient(symbol)}`}>
      <span className="text-white text-sm font-bold">{symbol[0]?.toUpperCase()}</span>
    </div>
  );

  // 24h change cell — shared between desktop and mobile
  const Change24h = ({ value }: { value?: number | null }) => {
    const formatted = formatPct(value);
    if (!formatted) return <span className={isDark ? "text-zinc-600" : "text-gray-300"}>—</span>;
    const positive = (value ?? 0) >= 0;
    return (
      <span
        className={`inline-flex items-center gap-0.5 text-xs font-semibold font-numeric ${
          positive ? "text-emerald-400" : "text-red-400"
        }`}
      >
        {positive
          ? <TrendingUp className="w-3 h-3 shrink-0" />
          : <TrendingDown className="w-3 h-3 shrink-0" />}
        {formatted}
      </span>
    );
  };

  const thClass = `px-4 py-3 text-xs font-semibold uppercase tracking-wider ${
    isDark ? "text-zinc-500" : "text-gray-500"
  }`;
  const tdClass = `px-4 py-3.5 ${isDark ? "text-zinc-300" : "text-gray-700"}`;

  return (
    <>
      {/* Desktop Table */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className={`border-b ${isDark ? "border-zinc-800/80" : "border-gray-200"}`}>
              <th className={`${thClass} text-left`}>Token</th>
              <th className={`${thClass} text-left`}>Chain</th>
              <th className={`${thClass} text-right`}>Amount</th>
              {showWalletColumn && <th className={`${thClass} text-left`}>Wallet</th>}
              <th className={`${thClass} text-right`}>Price</th>
              <th className={`${thClass} text-right`}>24h</th>
              <th className={`${thClass} text-right`}>Value</th>
              <th className={`${thClass} text-left`}>Address</th>
            </tr>
          </thead>
          <tbody>
            {balances.map((bal, i) => (
              <tr
                key={i}
                className={`border-b transition-colors ${
                  isDark
                    ? "border-zinc-800/60 hover:bg-zinc-800/40"
                    : "border-gray-100 hover:bg-gray-50"
                }`}
              >
                {/* Token */}
                <td className={tdClass}>
                  <div className="flex items-center gap-3">
                    <TokenIcon symbol={bal.symbol} />
                    <span className={`font-semibold ${isDark ? "text-zinc-100" : "text-gray-900"}`}>
                      {bal.symbol}
                    </span>
                  </div>
                </td>

                {/* Chain */}
                <td className={tdClass}>
                  <ChainBadge chain={bal.chain} />
                </td>

                {/* Amount */}
                <td className={`${tdClass} text-right font-medium font-numeric`}>
                  {formatAmount(bal.amount)}
                </td>

                {/* Wallet */}
                {showWalletColumn && (
                  <td className={tdClass}>
                    <div className="flex flex-col gap-0.5">
                      {bal.wallet_name && (
                        <span className={`text-sm font-medium ${isDark ? "text-blue-400" : "text-blue-600"}`}>
                          {bal.wallet_name}
                        </span>
                      )}
                      {bal.wallet_address && (
                        <button
                          onClick={() => copyToClipboard(bal.wallet_address!)}
                          className={`font-mono text-xs transition-colors flex items-center gap-1 w-fit ${
                            isDark ? "text-zinc-500 hover:text-blue-400" : "text-gray-400 hover:text-blue-600"
                          }`}
                          title="Copy wallet address"
                        >
                          {shortenAddress(bal.wallet_address)}
                          {copiedAddress === bal.wallet_address
                            ? <Check className="w-3 h-3 text-emerald-500" />
                            : <Copy className="w-3 h-3" />}
                        </button>
                      )}
                    </div>
                  </td>
                )}

                {/* Price */}
                <td className={`${tdClass} text-right font-numeric ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
                  {bal.usd_price ? formatUSD(bal.usd_price) : "—"}
                </td>

                {/* 24h Change */}
                <td className={`${tdClass} text-right`}>
                  <Change24h value={bal.change_24h} />
                </td>

                {/* Value */}
                <td className={`${tdClass} text-right font-semibold font-numeric ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>
                  {bal.usd_value ? formatUSD(bal.usd_value) : "—"}
                </td>

                {/* Token Address */}
                <td className={tdClass}>
                  <button
                    onClick={() => copyToClipboard(bal.address)}
                    className={`font-mono text-xs transition-colors flex items-center gap-1 px-2 py-1 rounded-md ${
                      isDark
                        ? "text-zinc-500 hover:text-blue-400 hover:bg-zinc-800"
                        : "text-gray-400 hover:text-blue-600 hover:bg-gray-100"
                    }`}
                    title="Copy token address"
                  >
                    {shortenAddress(bal.address)}
                    {copiedAddress === bal.address
                      ? <Check className="w-3 h-3 text-emerald-500" />
                      : <Copy className="w-3 h-3" />}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="lg:hidden space-y-3">
        {balances.map((bal, i) => (
          <div
            key={i}
            className={`p-4 rounded-xl border transition-colors ${
              isDark
                ? "bg-zinc-900 border-zinc-800/80 hover:border-zinc-700"
                : "bg-white border-gray-200 hover:border-gray-300"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <TokenIcon symbol={bal.symbol} />
                <div>
                  <p className={`font-semibold ${isDark ? "text-zinc-100" : "text-gray-900"}`}>
                    {bal.symbol}
                  </p>
                  <ChainBadge chain={bal.chain} />
                </div>
              </div>
              <div className="text-right">
                <p className={`font-semibold font-numeric ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>
                  {bal.usd_value ? formatUSD(bal.usd_value) : "—"}
                </p>
                <Change24h value={bal.change_24h} />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between">
                <span className={`text-sm ${isDark ? "text-zinc-500" : "text-gray-500"}`}>Amount</span>
                <span className={`text-sm font-medium font-numeric ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
                  {formatAmount(bal.amount)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={`text-sm ${isDark ? "text-zinc-500" : "text-gray-500"}`}>Price</span>
                <span className={`text-sm font-numeric ${isDark ? "text-zinc-400" : "text-gray-600"}`}>
                  {bal.usd_price ? formatUSD(bal.usd_price) : "—"}
                </span>
              </div>
              {showWalletColumn && bal.wallet_name && (
                <div className="flex justify-between">
                  <span className={`text-sm ${isDark ? "text-zinc-500" : "text-gray-500"}`}>Wallet</span>
                  <span className={`text-sm font-medium ${isDark ? "text-blue-400" : "text-blue-600"}`}>
                    {bal.wallet_name}
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
};

export default BalancesTable;
