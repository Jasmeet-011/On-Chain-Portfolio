// src/components/BalancesTable.tsx - PROFESSIONAL with Lucide Icons
import React from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress, formatAmount, formatUSD } from "../utils";
import { Copy, Check } from "lucide-react";

interface TokenBalance {
  symbol: string;
  address: string;
  decimals: number;
  raw: string;
  amount: number;
  usd_price?: number;
  usd_value?: number;
  wallet_name?: string;
  wallet_address?: string;
  chain?: string;
}

interface Props {
  balances: TokenBalance[];
}

const BalancesTable: React.FC<Props> = ({ balances }) => {
  const { theme } = useAppContext();
  const [copiedAddress, setCopiedAddress] = React.useState<string | null>(null);

  if (!balances || balances.length === 0) return null;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedAddress(text);
    setTimeout(() => setCopiedAddress(null), 2000);
  };

  const getChainBadge = (chain?: string) => {
    if (!chain) return null;
    
    const chainLower = chain.toLowerCase();
    const isAptos = chainLower === 'aptos';
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
        isAptos
          ? theme === "dark"
            ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
            : "bg-blue-50 text-blue-600 border border-blue-200"
          : theme === "dark"
          ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
          : "bg-purple-50 text-purple-600 border border-purple-200"
      }`}>
        <span>{isAptos ? '⬢' : '◎'}</span>
        {chain.toUpperCase()}
      </span>
    );
  };

  return (
    <>
      {/* Desktop Table */}
      <div className="hidden lg:block overflow-x-auto mt-4">
        <table className="min-w-full">
          <thead>
            <tr className={`border-b ${
              theme === "dark" ? "border-zinc-800" : "border-gray-200"
            }`}>
              <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Token
              </th>
              <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Chain
              </th>
              <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Amount
              </th>
              <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Wallet
              </th>
              <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Price
              </th>
              <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Value
              </th>
              <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-zinc-500" : "text-gray-600"
              }`}>
                Token Address
              </th>
            </tr>
          </thead>
          <tbody>
            {balances.map((bal, i) => (
              <tr
                key={i}
                className={`border-b transition-colors ${
                  theme === "dark"
                    ? "border-zinc-800 hover:bg-zinc-900/50"
                    : "border-gray-100 hover:bg-gray-50"
                }`}
              >
                {/* Token */}
                <td className="px-4 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      bal.chain === 'aptos'
                        ? "bg-gradient-to-br from-blue-500 to-cyan-600"
                        : "bg-gradient-to-br from-purple-500 to-pink-600"
                    }`}>
                      <span className="text-white text-sm font-bold">
                        {bal.symbol[0]}
                      </span>
                    </div>
                    <span className={`font-semibold ${
                      theme === "dark" ? "text-zinc-200" : "text-gray-900"
                    }`}>
                      {bal.symbol}
                    </span>
                  </div>
                </td>
                
                {/* Chain */}
                <td className="px-4 py-4">
                  {getChainBadge(bal.chain)}
                </td>
                
                {/* Amount */}
                <td className={`px-4 py-4 text-right font-medium ${
                  theme === "dark" ? "text-zinc-300" : "text-gray-700"
                }`}>
                  {formatAmount(bal.amount)}
                </td>
                
                {/* Wallet */}
                <td className="px-4 py-4">
                  <div className="flex flex-col gap-1">
                    {bal.wallet_name && (
                      <span className={`text-sm font-medium ${
                        theme === "dark" ? "text-blue-400" : "text-blue-600"
                      }`}>
                        {bal.wallet_name}
                      </span>
                    )}
                    {bal.wallet_address && (
                      <button
                        onClick={() => copyToClipboard(bal.wallet_address!)}
                        className={`font-mono text-xs transition-colors w-fit flex items-center gap-1 ${
                          theme === "dark"
                            ? "text-zinc-500 hover:text-blue-400"
                            : "text-gray-500 hover:text-blue-600"
                        }`}
                        title="Copy wallet address"
                      >
                        {shortenAddress(bal.wallet_address)}
                        {copiedAddress === bal.wallet_address ? (
                          <Check className="w-3 h-3 text-green-500" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    )}
                  </div>
                </td>
                
                {/* Price */}
                <td className={`px-4 py-4 text-right ${
                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                }`}>
                  {bal.usd_price ? formatUSD(bal.usd_price) : "-"}
                </td>
                
                {/* Value */}
                <td className={`px-4 py-4 text-right font-semibold ${
                  theme === "dark" ? "text-green-400" : "text-green-600"
                }`}>
                  {bal.usd_value ? formatUSD(bal.usd_value) : "-"}
                </td>
                
                {/* Token Address */}
                <td className="px-4 py-4">
                  <button
                    onClick={() => copyToClipboard(bal.address)}
                    className={`font-mono text-xs px-2 py-1 rounded hover:bg-opacity-20 transition-colors flex items-center gap-1 ${
                      theme === "dark"
                        ? "text-zinc-500 hover:text-blue-400 hover:bg-blue-400"
                        : "text-gray-500 hover:text-blue-600 hover:bg-blue-100"
                    }`}
                    title="Copy token address"
                  >
                    {shortenAddress(bal.address)}
                    {copiedAddress === bal.address ? (
                      <Check className="w-3 h-3 text-green-500" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="lg:hidden mt-4 space-y-3">
        {balances.map((bal, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg border ${
              theme === "dark"
                ? "bg-zinc-900 border-zinc-800"
                : "bg-white border-gray-200"
            }`}
          >
            {/* Token Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  bal.chain === 'aptos'
                    ? "bg-gradient-to-br from-blue-500 to-cyan-600"
                    : "bg-gradient-to-br from-purple-500 to-pink-600"
                }`}>
                  <span className="text-white text-sm font-bold">
                    {bal.symbol[0]}
                  </span>
                </div>
                <div>
                  <div className={`font-semibold ${
                    theme === "dark" ? "text-zinc-200" : "text-gray-900"
                  }`}>
                    {bal.symbol}
                  </div>
                  {getChainBadge(bal.chain)}
                </div>
              </div>
              <div className={`text-right font-semibold ${
                theme === "dark" ? "text-green-400" : "text-green-600"
              }`}>
                {bal.usd_value ? formatUSD(bal.usd_value) : "-"}
              </div>
            </div>

            {/* Details Grid */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className={`text-sm ${
                  theme === "dark" ? "text-zinc-500" : "text-gray-600"
                }`}>
                  Amount
                </span>
                <span className={`text-sm font-medium ${
                  theme === "dark" ? "text-zinc-300" : "text-gray-700"
                }`}>
                  {formatAmount(bal.amount)}
                </span>
              </div>

              <div className="flex justify-between">
                <span className={`text-sm ${
                  theme === "dark" ? "text-zinc-500" : "text-gray-600"
                }`}>
                  Price
                </span>
                <span className={`text-sm ${
                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                }`}>
                  {bal.usd_price ? formatUSD(bal.usd_price) : "-"}
                </span>
              </div>

              {bal.wallet_name && (
                <div className="flex justify-between">
                  <span className={`text-sm ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>
                    Wallet
                  </span>
                  <span className={`text-sm font-medium ${
                    theme === "dark" ? "text-blue-400" : "text-blue-600"
                  }`}>
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