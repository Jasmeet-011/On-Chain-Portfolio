// src/components/TokenMiniChart.tsx - PROFESSIONAL: Black/White/Gray Theme
import React, { useState, useEffect } from "react";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import type { PriceHistoryResponse } from "../api";
import { RefreshCw } from "lucide-react";

interface TokenMiniChartProps {
  symbol: string;
  balance: number;
  chain?: string;
  days?: number;
}

const TokenMiniChart: React.FC<TokenMiniChartProps> = ({
  symbol,
  balance,
  chain,
  days = 7,
}) => {
  const { theme } = useAppContext();
  const [data, setData] = useState<PriceHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [symbol, days, chain]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await api.getPriceHistory(symbol, days, chain);
      setData(response);
    } catch (err) {
      console.error(`Failed to fetch ${symbol} history:`, err);
    } finally {
      setLoading(false);
    }
  };

  // Format data for mini chart
  const chartData = data?.prices.map((point) => ({
    value: point.price,
  })) || [];

  const isPositive = (data?.period_change_percent || 0) >= 0;
  const lineColor = isPositive ? "#10b981" : "#ef4444";

  // Get chain badge
  const getChainBadge = (chain?: string) => {
    if (!chain) return null;
    
    return (
      <span className={`text-xs px-2 py-0.5 rounded font-medium ${
        theme === "dark"
          ? "bg-zinc-800 text-zinc-400 border border-zinc-700"
          : "bg-gray-100 text-gray-600 border border-gray-200"
      }`}>
        {chain === "aptos" ? "⬢" : "◎"} {chain.toUpperCase()}
      </span>
    );
  };

  return (
    <div
      className={`rounded-xl p-6 ${
        theme === "dark"
          ? "bg-zinc-900 border border-zinc-800"
          : "bg-white border border-gray-200 shadow-sm"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`font-bold text-lg ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            {symbol}
          </span>
          {getChainBadge(chain)}
        </div>
        {data && (
          <span
            className={`text-sm font-medium ${
              isPositive ? "text-green-500" : "text-red-500"
            }`}
          >
            {isPositive ? "+" : ""}
            {data.period_change_percent.toFixed(2)}%
          </span>
        )}
      </div>

      {/* Mini Chart */}
      <div className="h-24 mb-4">
        {loading ? (
          <div className="h-full flex items-center justify-center">
            <RefreshCw className={`w-5 h-5 animate-spin ${
              theme === "dark" ? "text-white" : "text-black"
            }`} />
          </div>
        ) : data && chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <Line
                type="monotone"
                dataKey="value"
                stroke={lineColor}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div
            className={`h-full rounded-lg flex items-center justify-center ${
              theme === "dark" ? "bg-zinc-800" : "bg-gray-50"
            }`}
          >
            <span className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-400"}`}>
              No data
            </span>
          </div>
        )}
      </div>

      {/* Balance */}
      <div className="flex justify-between items-center">
        <span className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
          Balance
        </span>
        <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          {balance.toFixed(4)} {symbol}
        </span>
      </div>

      {/* Current Price */}
      {data && (
        <div className="flex justify-between items-center mt-2">
          <span className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            Price
          </span>
          <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            ${data.current_price.toFixed(2)}
          </span>
        </div>
      )}

      {/* Total Value */}
      {data && (
        <div className={`flex justify-between items-center mt-2 pt-2 border-t ${
          theme === "dark" ? "border-zinc-800" : "border-gray-200"
        }`}>
          <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
            Total Value
          </span>
          <span className={`font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            ${(balance * data.current_price).toFixed(2)}
          </span>
        </div>
      )}
    </div>
  );
};

export default TokenMiniChart;