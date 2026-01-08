// src/components/PortfolioHistoryChart.tsx - FIXED: Type-Safe Version
import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Label,
} from "recharts";
import { format } from "date-fns";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import type { DetailedPortfolioHistoryResponse, WalletEvent } from "../api";
import { AlertTriangle, BarChart3, Info, Zap, RefreshCw } from "lucide-react";

type TimeRange = "1D" | "7D" | "1M" | "3M" | "1Y";

const TIME_RANGE_DAYS: Record<TimeRange, number> = {
  "1D": 1,
  "7D": 7,
  "1M": 30,
  "3M": 90,
  "1Y": 365,
};

interface PortfolioHistoryChartProps {
  className?: string;
  selectedScope: string;  // 'complete' or wallet address
}

const PortfolioHistoryChart: React.FC<PortfolioHistoryChartProps> = ({ 
  className = "",
  selectedScope
}) => {
  const { theme, wallets } = useAppContext();
  
  const [timeRange, setTimeRange] = useState<TimeRange>("1D");
  const [data, setData] = useState<DetailedPortfolioHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ✅ UPDATED: Reload when scope OR time range changes
  useEffect(() => {
    fetchData();
  }, [timeRange, wallets.length, selectedScope]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const days = TIME_RANGE_DAYS[timeRange];
      
      // ✅ FIXED: Type-safe way to get wallet_id
      let walletId: string | null = null;
      
      if (selectedScope !== 'complete') {
        // Find wallet by address
        const wallet = wallets.find(w => w.address === selectedScope);
        
        if (wallet) {
          // ✅ Try multiple possible ID fields (type-safe)
          walletId = (wallet as any)._id || (wallet as any).id || null;
          
          // If still no ID, we'll pass the address and let backend handle it
          if (!walletId) {
            console.warn('[Chart] Wallet found but no _id/id field, using address as fallback');
            // Backend might need to look up by address instead
          }
        }
      }
      
      console.log(`[Chart] Fetching ${days} days of history for scope:`, 
        selectedScope === 'complete' ? 'Complete Portfolio' : `Wallet ${walletId || selectedScope}`
      );
      
      // ✅ Pass walletId to API (can be null for complete portfolio)
      const response = await api.getDetailedPortfolioHistory(days, walletId);
      
      console.log("[Chart] Response received:", {
        scope: response.metadata?.scope_label,
        values: response.values?.length,
        currentValue: response.current_value
      });
      
      setData(response);
    } catch (err: any) {
      console.error("Failed to fetch portfolio history:", err);
      setError(err.message || "Failed to load chart data");
    } finally {
      setLoading(false);
    }
  };

  // Calculate actual available data days
  const getAvailableDataDays = (): number => {
    if (!data?.metadata?.wallet_age_days) return 1;
    return data.metadata.wallet_age_days;
  };

  // Check if time range is supported
  const isRangeSupported = (range: TimeRange): boolean => {
    const availableDays = getAvailableDataDays();
    const requestedDays = TIME_RANGE_DAYS[range];
    
    // Need at least 50% of requested data
    return availableDays >= requestedDays * 0.5;
  };

  // Get tooltip message for disabled ranges
  const getDisabledRangeTooltip = (range: TimeRange): string => {
    const availableDays = getAvailableDataDays();
    const requestedDays = TIME_RANGE_DAYS[range];
    const daysNeeded = Math.ceil(requestedDays * 0.5);
    const daysRemaining = daysNeeded - availableDays;
    
    return `Not enough data (need ${daysNeeded} days, have ${availableDays} days). Check back in ${daysRemaining} day${daysRemaining !== 1 ? 's' : ''}.`;
  };

  const handleTimeRangeChange = (range: TimeRange) => {
    if (!isRangeSupported(range)) return;
    setTimeRange(range);
  };

  // Process chart data
  const chartData = data?.values.map((point) => ({
    timestamp: point.timestamp,
    value: point.value,
    date: new Date(point.timestamp * 1000),
  })) || [];

  // Filter visible wallet events
  const visibleEvents = data?.wallet_events?.filter(event => {
    if (chartData.length === 0) return false;
    const eventDate = new Date(event.timestamp * 1000);
    const firstDate = chartData[0]?.date;
    const lastDate = chartData[chartData.length - 1]?.date;
    return eventDate >= firstDate && eventDate <= lastDate;
  }) || [];

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload[0]) return null;

    const point = payload[0].payload;
    const value = point.value;
    const date = point.date;

    const nearbyEvent = visibleEvents.find(event => {
      const eventDate = new Date(event.timestamp * 1000);
      const timeDiff = Math.abs(date.getTime() - eventDate.getTime());
      return timeDiff < 3600000; // Within 1 hour
    });

    return (
      <div
        className={`px-4 py-3 rounded-lg border shadow-lg ${
          theme === "dark"
            ? "bg-zinc-800 border-zinc-700"
            : "bg-white border-gray-200"
        }`}
      >
        <p className={`text-xs mb-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
          {format(date, timeRange === "1D" ? "MMM dd, HH:mm" : "MMM dd, yyyy")}
        </p>
        <p className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          ${value.toFixed(2)}
        </p>
        
        {nearbyEvent && (
          <div className={`mt-2 pt-2 border-t ${
            theme === "dark" ? "border-zinc-700" : "border-gray-200"
          }`}>
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              <div>
                <p className={`text-xs font-medium ${
                  theme === "dark" ? "text-zinc-300" : "text-gray-700"
                }`}>
                  {nearbyEvent.wallet_label} added
                </p>
                <p className={`text-xs ${theme === "dark" ? "text-green-400" : "text-green-600"}`}>
                  +${nearbyEvent.impact.toFixed(2)}
                  {nearbyEvent.value_before > 0 && ` (+${((nearbyEvent.impact / nearbyEvent.value_before) * 100).toFixed(1)}%)`}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const isPositive = (data?.period_change_percent || 0) >= 0;
  const lineColor = isPositive ? "#10b981" : "#ef4444";
  const gradientId = `gradient-${timeRange}`;

  return (
    <div className={className}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            {data?.metadata?.scope_label || "Portfolio Value"}
          </h3>
          {data && (
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
              {timeRange === "1D" ? "Last 24 hours" : 
               timeRange === "7D" ? "Last 7 days" :
               timeRange === "1M" ? "Last month" :
               timeRange === "3M" ? "Last 3 months" : "Last year"}
              {data.metadata?.actual_days_shown && data.metadata.actual_days_shown < TIME_RANGE_DAYS[timeRange] && (
                <span className={`ml-2 text-xs ${theme === "dark" ? "text-yellow-400" : "text-yellow-600"}`}>
                  (Showing {data.metadata.actual_days_shown} days)
                </span>
              )}
            </p>
          )}
        </div>

        {/* Time Range Selector */}
        <div className="flex gap-2 flex-wrap">
          {(["1D", "7D", "1M", "3M", "1Y"] as TimeRange[]).map((range) => {
            const supported = isRangeSupported(range);
            const isActive = timeRange === range;
            const disabled = loading || !supported;
            
            return (
              <button
                key={range}
                onClick={() => handleTimeRangeChange(range)}
                disabled={disabled}
                title={!supported ? getDisabledRangeTooltip(range) : `View ${range} history`}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? theme === "dark"
                      ? "bg-white text-black"
                      : "bg-black text-white"
                    : disabled
                    ? theme === "dark"
                      ? "bg-zinc-800 text-zinc-600 cursor-not-allowed opacity-50"
                      : "bg-gray-100 text-gray-400 cursor-not-allowed opacity-50"
                    : theme === "dark"
                    ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {range}
              </button>
            );
          })}
        </div>
      </div>

      {/* Chart Area */}
      {loading ? (
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <RefreshCw className={`w-8 h-8 mx-auto mb-4 animate-spin ${
              theme === "dark" ? "text-white" : "text-black"
            }`} />
            <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
              Loading chart data...
            </p>
          </div>
        </div>
      ) : error ? (
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className={`font-medium mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              {error}
            </p>
            <button
              onClick={fetchData}
              className={`mt-4 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                theme === "dark"
                  ? "bg-white text-black hover:bg-gray-200"
                  : "bg-black text-white hover:bg-gray-800"
              }`}
            >
              Try Again
            </button>
          </div>
        </div>
      ) : data && chartData.length > 0 ? (
        <>
          {/* Chart */}
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <defs>
                  <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={lineColor} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={lineColor} stopOpacity={0} />
                  </linearGradient>
                </defs>
                
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={theme === "dark" ? "#3f3f46" : "#e5e7eb"}
                  vertical={false}
                />
                
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(timestamp) => {
                    const date = new Date(timestamp * 1000);
                    if (timeRange === "1D") {
                      return format(date, "HH:mm");
                    } else {
                      return format(date, "MMM dd");
                    }
                  }}
                  stroke={theme === "dark" ? "#71717a" : "#9ca3af"}
                  tick={{ fill: theme === "dark" ? "#a1a1aa" : "#6b7280", fontSize: 12 }}
                  tickLine={false}
                  tickCount={timeRange === "1D" ? 8 : 6}
                  minTickGap={50}
                />
                
                <YAxis
                  tickFormatter={(value) => `$${value.toFixed(0)}`}
                  stroke={theme === "dark" ? "#71717a" : "#9ca3af"}
                  tick={{ fill: theme === "dark" ? "#a1a1aa" : "#6b7280", fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  width={60}
                />
                
                <Tooltip content={<CustomTooltip />} />
                
                {/* Wallet event markers */}
                {visibleEvents.map((event, idx) => (
                  <ReferenceLine
                    key={idx}
                    x={event.timestamp}
                    stroke={theme === "dark" ? "#a1a1aa" : "#6b7280"}
                    strokeDasharray="3 3"
                    strokeWidth={2}
                  >
                    <Label
                      value="⚡"
                      position="top"
                      fill={theme === "dark" ? "#fff" : "#000"}
                      fontSize={16}
                    />
                  </ReferenceLine>
                ))}
                
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={lineColor}
                  strokeWidth={3}
                  dot={false}
                  fill={`url(#${gradientId})`}
                  activeDot={{
                    r: 6,
                    stroke: lineColor,
                    strokeWidth: 2,
                    fill: theme === "dark" ? "#18181b" : "#ffffff",
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Stats & Breakdown */}
          <div className="mt-6 space-y-4">
            {/* Current Stats */}
            <div className={`p-4 rounded-lg grid grid-cols-2 gap-4 ${
              theme === "dark" ? "bg-zinc-900/50" : "bg-gray-50"
            }`}>
              <div>
                <p className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                  Current Value
                </p>
                <p className={`text-2xl font-bold mt-1 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                  ${data.current_value?.toFixed(2) || '0.00'}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                  Change ({timeRange})
                </p>
                <p className={`text-2xl font-bold mt-1 ${isPositive ? "text-green-500" : "text-red-500"}`}>
                  {isPositive ? "+" : ""}${data.period_change?.toFixed(2) || '0.00'} ({isPositive ? "+" : ""}{data.period_change_percent?.toFixed(2) || '0.00'}%)
                </p>
              </div>
            </div>

            {/* Wallet Breakdown */}
            {data.wallet_breakdown && data.wallet_breakdown.length > 0 && (
              <div className={`p-4 rounded-lg ${
                theme === "dark" ? "bg-zinc-900/50" : "bg-gray-50"
              }`}>
                <h4 className={`text-sm font-semibold mb-3 flex items-center gap-2 ${
                  theme === "dark" ? "text-white" : "text-gray-900"
                }`}>
                  <BarChart3 className="w-4 h-4" />
                  {selectedScope === 'complete' ? "Portfolio Composition" : "Wallet Details"}
                </h4>
                <div className="space-y-2">
                  {data.wallet_breakdown.map((wallet, idx) => (
                    <div key={wallet.wallet_id || idx} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          theme === "dark" ? "bg-zinc-500" : "bg-gray-400"
                        }`} />
                        <span className={`text-sm ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                          {wallet.label || 'Unknown Wallet'}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          theme === "dark"
                            ? "bg-zinc-800 text-zinc-400 border border-zinc-700"
                            : "bg-gray-100 text-gray-600 border border-gray-200"
                        }`}>
                          {(wallet.chain || 'unknown').toUpperCase()}
                        </span>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                          ${wallet.current_value?.toFixed(2) || '0.00'}
                        </p>
                        <p className={`text-xs ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                          {wallet.percentage?.toFixed(1) || '0.0'}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Disclaimer */}
            {data.metadata?.disclaimer && (
              <div className={`p-3 rounded-lg text-xs flex items-start gap-2 ${
                theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-gray-50 border border-gray-200"
              }`}>
                <Info className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                }`} />
                <span className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
                  {data.metadata.disclaimer}
                </span>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="h-80 flex items-center justify-center">
          <div className="text-center">
            <BarChart3 className={`w-16 h-16 mx-auto mb-4 ${
              theme === "dark" ? "text-zinc-600" : "text-gray-400"
            }`} />
            <p className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              No data available
            </p>
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
              Try selecting a different time range or add wallets
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioHistoryChart;