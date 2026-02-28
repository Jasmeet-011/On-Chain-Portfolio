// src/components/InsightsQuickCard.tsx - Uses centralized API client
import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { TrendingUp, AlertCircle, CheckCircle, ArrowRight } from "lucide-react";
import { api } from "../api";

interface Props {
  onViewDetails?: () => void;
}

const InsightsQuickCard: React.FC<Props> = ({ onViewDetails }) => {
  const { theme } = useAppContext();
  const [insights, setInsights] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const data = await api.getInsightsSummary();
      setInsights(data);
    } catch (err) {
      console.error("Failed to fetch insights:", err);
    } finally {
      setLoading(false);
    }
  };

  // Get risk color
  const getRiskColor = (risk: string) => {
    if (risk === "high") return theme === "dark" ? "text-red-400" : "text-red-600";
    if (risk === "moderate") return theme === "dark" ? "text-yellow-400" : "text-yellow-600";
    return theme === "dark" ? "text-green-400" : "text-green-600";
  };

  // Get risk emoji
  const getRiskEmoji = (risk: string) => {
    if (risk === "high") return "🔴";
    if (risk === "moderate") return "🟡";
    return "🟢";
  };

  // Get risk label
  const getRiskLabel = (risk: string) => {
    return risk.charAt(0).toUpperCase() + risk.slice(1);
  };

  if (loading) {
    return (
      <div
        className={`rounded-xl p-6 ${
          theme === "dark"
            ? "bg-zinc-900 border border-zinc-800"
            : "bg-white border border-gray-200 shadow-sm"
        }`}
      >
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            Analyzing portfolio...
          </span>
        </div>
      </div>
    );
  }

  if (!insights) return null;

  // Check if insights are empty (no real data)
  if (insights.total_tokens === 0 || insights.total_value_usd === 0) {
    return (
      <div
        className={`rounded-xl p-6 ${
          theme === "dark"
            ? "bg-zinc-900 border border-zinc-800"
            : "bg-white border border-gray-200 shadow-sm"
        }`}
      >
        <div className="flex items-center gap-3 mb-4">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center ${
              theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
            }`}
          >
            <TrendingUp className={`w-5 h-5 ${theme === "dark" ? "text-zinc-500" : "text-gray-400"}`} />
          </div>
          <div>
            <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Portfolio Health
            </h3>
            <p className={`text-sm ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
              No data available yet
            </p>
          </div>
        </div>
        <p className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
          Add wallets with token balances to see insights
        </p>
      </div>
    );
  }

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
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center ${
              theme === "dark" ? "bg-blue-500/10" : "bg-blue-50"
            }`}
          >
            <TrendingUp className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h3
              className={`text-lg font-bold ${
                theme === "dark" ? "text-white" : "text-gray-900"
              }`}
            >
              Portfolio Health
            </h3>
            <p className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
              AI-powered insights
            </p>
          </div>
        </div>

        {/* Risk Score Badge */}
        <div
          className={`px-3 py-1.5 rounded-full flex items-center gap-2 ${
            insights.overall_risk_score === "high"
              ? theme === "dark"
                ? "bg-red-500/10 border border-red-500/20"
                : "bg-red-50 border border-red-200"
              : insights.overall_risk_score === "moderate"
              ? theme === "dark"
                ? "bg-yellow-500/10 border border-yellow-500/20"
                : "bg-yellow-50 border border-yellow-200"
              : theme === "dark"
              ? "bg-green-500/10 border border-green-500/20"
              : "bg-green-50 border border-green-200"
          }`}
        >
          <span className="text-lg">{getRiskEmoji(insights.overall_risk_score)}</span>
          <span
            className={`text-sm font-semibold ${getRiskColor(
              insights.overall_risk_score
            )}`}
          >
            {getRiskLabel(insights.overall_risk_score)} Risk
          </span>
        </div>
      </div>

      {/* Top Insights */}
      {insights.key_insights && insights.key_insights.length > 0 && (
        <div className="space-y-2 mb-4">
          {insights.key_insights.slice(0, 3).map((insight: string, idx: number) => (
            <div
              key={idx}
              className={`flex items-start gap-2 p-2 rounded-lg ${
                theme === "dark" ? "bg-zinc-800/50" : "bg-gray-50"
              }`}
            >
              <span className="text-base mt-0.5">{insight.split(" ")[0]}</span>
              <span
                className={`text-sm flex-1 ${
                  theme === "dark" ? "text-zinc-300" : "text-gray-700"
                }`}
              >
                {insight.split(" ").slice(1).join(" ")}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Stats Row */}
      <div
        className={`grid grid-cols-3 gap-3 py-3 mb-4 border-t border-b ${
          theme === "dark" ? "border-zinc-800" : "border-gray-200"
        }`}
      >
        <div className="text-center">
          <div
            className={`text-2xl font-bold ${
              theme === "dark" ? "text-white" : "text-gray-900"
            }`}
          >
            ${(insights.total_value_usd || 0).toLocaleString()}
          </div>
          <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
            Total Value
          </div>
        </div>
        <div className="text-center">
          <div
            className={`text-2xl font-bold ${
              theme === "dark" ? "text-white" : "text-gray-900"
            }`}
          >
            {insights.total_tokens || 0}
          </div>
          <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
            Tokens
          </div>
        </div>
        <div className="text-center">
          <div
            className={`text-2xl font-bold ${
              theme === "dark" ? "text-white" : "text-gray-900"
            }`}
          >
            {insights.total_wallets || 0}
          </div>
          <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
            Wallets
          </div>
        </div>
      </div>

      {/* View Details Button */}
      <button
        onClick={onViewDetails}
        className={`w-full py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 font-medium transition-colors ${
          theme === "dark"
            ? "bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 border border-blue-500/20"
            : "bg-blue-50 text-blue-600 hover:bg-blue-100 border border-blue-200"
        }`}
      >
        View Full Analysis
        <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
};

export default InsightsQuickCard;