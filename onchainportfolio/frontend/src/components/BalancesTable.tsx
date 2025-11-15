import React from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress, formatAmount, formatUSD } from "../utils";

interface Props {
  balances: any[];
  prices?: Record<string, number>;
}

const BalancesTable: React.FC<Props> = ({ balances, prices }) => {
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
            <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Token</th>
            <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Amount</th>
            <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Value</th>
            <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}>Address</th>
          </tr>
        </thead>
        <tbody>
          {balances.map((bal, i) => {
            const usdValue = prices?.[bal.symbol]
              ? bal.display_amount * prices[bal.symbol]
              : null;
            return (
              <tr
                key={i}
                className={`border-b transition-colors ${
                  theme === "dark"
                    ? "border-gray-800 hover:bg-gray-800/50"
                    : "border-gray-100 hover:bg-gray-50"
                }`}
              >
                <td className="px-4 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs font-bold">
                        {bal.symbol[0]}
                      </span>
                    </div>
                    <span
                      className={`font-semibold ${
                        theme === "dark"
                          ? "text-gray-200"
                          : "text-gray-900"
                      }`}
                    >
                      {bal.symbol}
                    </span>
                  </div>
                </td>
                <td
                  className={`px-4 py-4 text-right font-medium ${
                    theme === "dark" ? "text-gray-300" : "text-gray-700"
                  }`}
                >
                  {formatAmount(bal.display_amount)}
                </td>
                <td
                  className={`px-4 py-4 text-right font-semibold ${
                    theme === "dark" ? "text-green-400" : "text-green-600"
                  }`}
                >
                  {usdValue ? formatUSD(usdValue) : "-"}
                </td>
                <td className="px-4 py-4">
                  <button
                    onClick={() => copyToClipboard(bal.token_address)}
                    className={`font-mono text-xs px-2 py-1 rounded hover:bg-opacity-20 transition-colors ${
                      theme === "dark"
                        ? "text-gray-500 hover:text-blue-400 hover:bg-blue-400"
                        : "text-gray-500 hover:text-blue-600 hover:bg-blue-100"
                    }`}
                    title="Copy address"
                  >
                    {shortenAddress(bal.token_address)}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default BalancesTable;
