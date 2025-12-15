import React from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress, formatAmount, formatUSD } from "../utils";

interface TokenBalance {
  symbol: string;
  address: string;
  decimals: number;
  raw: string;
  amount: number;
  usd_price?: number;
  usd_value?: number;
  wallet_name?: string;  // NEW: Wallet name
  wallet_address?: string;  // NEW: Wallet address
}

interface Props {
  balances: TokenBalance[];
}

const BalancesTable: React.FC<Props> = ({ balances }) => {
  const { theme } = useAppContext();

  if (!balances || balances.length === 0) return null;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="overflow-x-auto mt-4">
      <table className="min-w-full">
        <thead>
          <tr
            className={`border-b ${
              theme === "dark" ? "border-gray-700" : "border-gray-200"
            }`}
          >
            <th
              className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Token
            </th>
            <th
              className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Amount
            </th>
            <th
              className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Wallet
            </th>
            <th
              className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Price
            </th>
            <th
              className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Value
            </th>
            <th
              className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
                theme === "dark" ? "text-gray-400" : "text-gray-600"
              }`}
            >
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
                  ? "border-gray-800 hover:bg-gray-800/50"
                  : "border-gray-100 hover:bg-gray-50"
              }`}
            >
              {/* Token */}
              <td className="px-4 py-4">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-bold">
                      {bal.symbol[0]}
                    </span>
                  </div>
                  <span
                    className={`font-semibold ${
                      theme === "dark" ? "text-gray-200" : "text-gray-900"
                    }`}
                  >
                    {bal.symbol}
                  </span>
                </div>
              </td>
              
              {/* Amount */}
              <td
                className={`px-4 py-4 text-right font-medium ${
                  theme === "dark" ? "text-gray-300" : "text-gray-700"
                }`}
              >
                {formatAmount(bal.amount)}
              </td>
              
              {/* Wallet - NEW COLUMN */}
              <td className="px-4 py-4">
                <div className="flex flex-col gap-1">
                  {bal.wallet_name && (
                    <span
                      className={`text-sm font-medium ${
                        theme === "dark" ? "text-blue-400" : "text-blue-600"
                      }`}
                    >
                      {bal.wallet_name}
                    </span>
                  )}
                  {bal.wallet_address && (
                    <button
                      onClick={() => copyToClipboard(bal.wallet_address!)}
                      className={`font-mono text-xs transition-colors w-fit ${
                        theme === "dark"
                          ? "text-gray-500 hover:text-blue-400"
                          : "text-gray-500 hover:text-blue-600"
                      }`}
                      title="Copy wallet address"
                    >
                      {shortenAddress(bal.wallet_address)}
                    </button>
                  )}
                </div>
              </td>
              
              {/* Price */}
              <td
                className={`px-4 py-4 text-right ${
                  theme === "dark" ? "text-gray-400" : "text-gray-600"
                }`}
              >
                {bal.usd_price ? formatUSD(bal.usd_price) : "-"}
              </td>
              
              {/* Value */}
              <td
                className={`px-4 py-4 text-right font-semibold ${
                  theme === "dark" ? "text-green-400" : "text-green-600"
                }`}
              >
                {bal.usd_value ? formatUSD(bal.usd_value) : "-"}
              </td>
              
              {/* Token Address */}
              <td className="px-4 py-4">
                <button
                  onClick={() => copyToClipboard(bal.address)}
                  className={`font-mono text-xs px-2 py-1 rounded hover:bg-opacity-20 transition-colors ${
                    theme === "dark"
                      ? "text-gray-500 hover:text-blue-400 hover:bg-blue-400"
                      : "text-gray-500 hover:text-blue-600 hover:bg-blue-100"
                  }`}
                  title="Copy token address"
                >
                  {shortenAddress(bal.address)}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BalancesTable;