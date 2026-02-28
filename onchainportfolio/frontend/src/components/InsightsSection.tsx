// src/components/InsightsSection.tsx - Uses centralized API client
import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import {
  TrendingUp,
  AlertCircle,
  PieChart,
  BarChart3,
  Activity,
  RefreshCw,
} from "lucide-react";
import { api } from "../api";
import type { PortfolioInsights } from "../api";

type TabType = "exposure" | "dominance" | "concentration" | "volatility";

interface InsightsSectionProps {
  selectedScope?: string;  // 'complete' or wallet group id — triggers refetch on change
}

const InsightsSection: React.FC<InsightsSectionProps> = ({ selectedScope }) => {
  const { theme } = useAppContext();
  const [insights, setInsights] = useState<PortfolioInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("exposure");

  // Refetch when scope changes so insights stay in sync with selected view
  useEffect(() => {
    fetchInsights();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedScope]);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const data = await api.getInsights();
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

  const getRiskBgColor = (risk: string) => {
    if (risk === "high")
      return theme === "dark"
        ? "bg-red-500/10 border-red-500/20"
        : "bg-red-50 border-red-200";
    if (risk === "moderate")
      return theme === "dark"
        ? "bg-yellow-500/10 border-yellow-500/20"
        : "bg-yellow-50 border-yellow-200";
    return theme === "dark"
      ? "bg-green-500/10 border-green-500/20"
      : "bg-green-50 border-green-200";
  };

  const getRiskEmoji = (risk: string) => {
    if (risk === "high") return "🔴";
    if (risk === "moderate") return "🟡";
    return "🟢";
  };

  if (loading) {
    return (
      <div
        className={`rounded-xl p-8 ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200"
        }`}
      >
        <div className="flex items-center justify-center gap-2">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            Analyzing portfolio...
          </span>
        </div>
      </div>
    );
  }

  if (!insights) {
    return (
      <div
        className={`rounded-xl p-8 text-center ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200"
        }`}
      >
        <AlertCircle
          className={`w-12 h-12 mx-auto mb-3 ${
            theme === "dark" ? "text-zinc-600" : "text-gray-400"
          }`}
        />
        <p className={`mb-2 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
          No insights available
        </p>
        <p className={`text-sm ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
          Add a wallet with token balances to see portfolio analytics
        </p>
        <button
          onClick={fetchInsights}
          className={`mt-4 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            theme === "dark"
              ? "bg-zinc-800 hover:bg-zinc-700 text-zinc-300"
              : "bg-gray-100 hover:bg-gray-200 text-gray-700"
          }`}
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Retry
        </button>
      </div>
    );
  }

  // Check if insights are empty (no real data)
  if (insights.total_tokens === 0 || insights.total_value_usd === 0) {
    return (
      <div
        className={`rounded-xl p-8 text-center ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200"
        }`}
      >
        <PieChart
          className={`w-12 h-12 mx-auto mb-3 ${
            theme === "dark" ? "text-zinc-600" : "text-gray-400"
          }`}
        />
        <p className={`text-lg font-medium mb-2 ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
          No Portfolio Data Yet
        </p>
        <p className={`text-sm mb-4 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
          {insights.key_insights[0] || "Add wallets with token balances to see analytics"}
        </p>
        <button
          onClick={fetchInsights}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            theme === "dark"
              ? "bg-blue-600 hover:bg-blue-700 text-white"
              : "bg-blue-500 hover:bg-blue-600 text-white"
          }`}
        >
          <RefreshCw className="w-4 h-4 inline mr-2" />
          Refresh
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Risk Score */}
      <div
        className={`rounded-xl p-6 ${
          theme === "dark"
            ? "bg-zinc-900 border border-zinc-800"
            : "bg-white border border-gray-200 shadow-sm"
        }`}
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center ${
                theme === "dark" ? "bg-blue-500/10" : "bg-blue-50"
              }`}
            >
              <Activity className="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <h2
                className={`text-2xl font-bold ${
                  theme === "dark" ? "text-white" : "text-gray-900"
                }`}
              >
                Portfolio Intelligence
              </h2>
              <p className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                AI-powered analysis & recommendations
              </p>
            </div>
          </div>

          <button
            onClick={fetchInsights}
            disabled={loading}
            className={`p-2 rounded-lg transition-colors ${
              theme === "dark"
                ? "hover:bg-zinc-800 text-zinc-400"
                : "hover:bg-gray-100 text-gray-600"
            }`}
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        {/* Risk Score */}
        <div
          className={`p-4 rounded-lg border ${getRiskBgColor(
            insights.overall_risk_score
          )}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium mb-1 opacity-75">Overall Risk Level</div>
              <div className="flex items-center gap-2">
                <span className="text-2xl">{getRiskEmoji(insights.overall_risk_score)}</span>
                <span
                  className={`text-2xl font-bold ${getRiskColor(insights.overall_risk_score)}`}
                >
                  {insights.overall_risk_score.charAt(0).toUpperCase() +
                    insights.overall_risk_score.slice(1)}
                </span>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                Portfolio Value
              </div>
              <div
                className={`text-xl font-bold ${
                  theme === "dark" ? "text-white" : "text-gray-900"
                }`}
              >
                ${insights.total_value_usd.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Key Insights & Recommendations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          {/* Key Insights */}
          <div>
            <h3
              className={`text-sm font-semibold mb-3 ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}
            >
              Key Insights
            </h3>
            <div className="space-y-2">
              {insights.key_insights.map((insight: string, idx: number) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    theme === "dark" ? "bg-zinc-800" : "bg-gray-50"
                  }`}
                >
                  <p
                    className={`text-sm ${
                      theme === "dark" ? "text-zinc-300" : "text-gray-700"
                    }`}
                  >
                    {insight}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          <div>
            <h3
              className={`text-sm font-semibold mb-3 ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}
            >
              Recommendations
            </h3>
            <div className="space-y-2">
              {insights.recommendations.map((rec: string, idx: number) => (
                <div
                  key={idx}
                  className={`p-3 rounded-lg ${
                    theme === "dark" ? "bg-blue-500/5 border border-blue-500/10" : "bg-blue-50 border border-blue-100"
                  }`}
                >
                  <p
                    className={`text-sm ${
                      theme === "dark" ? "text-blue-300" : "text-blue-700"
                    }`}
                  >
                    {rec}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Analysis Tabs */}
      <div
        className={`rounded-xl overflow-hidden ${
          theme === "dark"
            ? "bg-zinc-900 border border-zinc-800"
            : "bg-white border border-gray-200 shadow-sm"
        }`}
      >
        {/* Tab Headers */}
        <div
          className={`flex border-b ${
            theme === "dark" ? "border-zinc-800" : "border-gray-200"
          }`}
        >
          <button
            onClick={() => setActiveTab("exposure")}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "exposure"
                ? theme === "dark"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "border-b-2 border-blue-600 text-blue-600"
                : theme === "dark"
                ? "text-zinc-500 hover:text-zinc-300"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Chain Exposure
          </button>
          <button
            onClick={() => setActiveTab("dominance")}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "dominance"
                ? theme === "dark"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "border-b-2 border-blue-600 text-blue-600"
                : theme === "dark"
                ? "text-zinc-500 hover:text-zinc-300"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Token Dominance
          </button>
          <button
            onClick={() => setActiveTab("concentration")}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "concentration"
                ? theme === "dark"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "border-b-2 border-blue-600 text-blue-600"
                : theme === "dark"
                ? "text-zinc-500 hover:text-zinc-300"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Concentration
          </button>
          <button
            onClick={() => setActiveTab("volatility")}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === "volatility"
                ? theme === "dark"
                  ? "border-b-2 border-blue-500 text-blue-400"
                  : "border-b-2 border-blue-600 text-blue-600"
                : theme === "dark"
                ? "text-zinc-500 hover:text-zinc-300"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Volatility
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Chain Exposure Tab */}
          {activeTab === "exposure" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3
                  className={`text-lg font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}
                >
                  Multi-Chain Exposure
                </h3>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    insights.chain_exposure.diversity_score === "high"
                      ? theme === "dark"
                        ? "bg-green-500/10 text-green-400"
                        : "bg-green-50 text-green-600"
                      : insights.chain_exposure.diversity_score === "moderate"
                      ? theme === "dark"
                        ? "bg-yellow-500/10 text-yellow-400"
                        : "bg-yellow-50 text-yellow-600"
                      : theme === "dark"
                      ? "bg-red-500/10 text-red-400"
                      : "bg-red-50 text-red-600"
                  }`}
                >
                  {insights.chain_exposure.diversity_score} diversity
                </span>
              </div>

              {insights.chain_exposure.exposures.map((exposure: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg ${
                    theme === "dark" ? "bg-zinc-800" : "bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">
                        {exposure.chain === "solana" ? "◎" : "⬢"}
                      </span>
                      <span
                        className={`font-semibold ${
                          theme === "dark" ? "text-white" : "text-gray-900"
                        }`}
                      >
                        {exposure.chain.charAt(0).toUpperCase() + exposure.chain.slice(1)}
                      </span>
                    </div>
                    <div className="text-right">
                      <div
                        className={`font-bold ${
                          theme === "dark" ? "text-white" : "text-gray-900"
                        }`}
                      >
                        ${exposure.value_usd.toLocaleString()}
                      </div>
                      <div
                        className={`text-sm ${
                          theme === "dark" ? "text-zinc-400" : "text-gray-600"
                        }`}
                      >
                        {exposure.percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="w-full bg-zinc-700 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-500 h-full rounded-full transition-all"
                      style={{ width: `${exposure.percentage}%` }}
                    />
                  </div>
                  <div
                    className={`text-xs mt-2 ${
                      theme === "dark" ? "text-zinc-500" : "text-gray-500"
                    }`}
                  >
                    {exposure.wallet_count} wallet{exposure.wallet_count !== 1 ? "s" : ""}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Token Dominance Tab */}
          {activeTab === "dominance" && (
            <div className="space-y-3">
              <h3
                className={`text-lg font-semibold mb-4 ${
                  theme === "dark" ? "text-white" : "text-gray-900"
                }`}
              >
                Token Holdings Ranked
              </h3>
              {insights.token_dominance.tokens.slice(0, 10).map((token: any) => (
                <div
                  key={token.rank}
                  className={`p-4 rounded-lg ${
                    theme === "dark" ? "bg-zinc-800" : "bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                          token.rank === 1
                            ? "bg-yellow-500/20 text-yellow-500"
                            : token.rank === 2
                            ? "bg-gray-400/20 text-gray-400"
                            : token.rank === 3
                            ? "bg-orange-500/20 text-orange-500"
                            : theme === "dark"
                            ? "bg-zinc-700 text-zinc-400"
                            : "bg-gray-200 text-gray-600"
                        }`}
                      >
                        #{token.rank}
                      </div>
                      <div>
                        <div
                          className={`font-semibold ${
                            theme === "dark" ? "text-white" : "text-gray-900"
                          }`}
                        >
                          {token.symbol}
                        </div>
                        <div
                          className={`text-xs ${
                            theme === "dark" ? "text-zinc-500" : "text-gray-500"
                          }`}
                        >
                          {token.chain === "solana" ? "◎ Solana" : "⬢ Aptos"}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div
                        className={`font-bold ${
                          theme === "dark" ? "text-white" : "text-gray-900"
                        }`}
                      >
                        ${token.value_usd.toLocaleString()}
                      </div>
                      <div
                        className={`text-sm ${
                          theme === "dark" ? "text-zinc-400" : "text-gray-600"
                        }`}
                      >
                        {token.percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Concentration Tab */}
          {activeTab === "concentration" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3
                  className={`text-lg font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}
                >
                  Concentration Analysis
                </h3>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskBgColor(
                    insights.concentration.overall_risk
                  )}`}
                >
                  {getRiskEmoji(insights.concentration.overall_risk)}{" "}
                  {insights.concentration.overall_risk} risk
                </span>
              </div>

              <div
                className={`p-4 rounded-lg ${theme === "dark" ? "bg-zinc-800" : "bg-gray-50"}`}
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div
                      className={`text-sm ${
                        theme === "dark" ? "text-zinc-400" : "text-gray-600"
                      }`}
                    >
                      Token Count
                    </div>
                    <div
                      className={`text-2xl font-bold ${
                        theme === "dark" ? "text-white" : "text-gray-900"
                      }`}
                    >
                      {insights.concentration.token_count}
                    </div>
                  </div>
                  <div>
                    <div
                      className={`text-sm ${
                        theme === "dark" ? "text-zinc-400" : "text-gray-600"
                      }`}
                    >
                      HHI Index
                    </div>
                    <div
                      className={`text-2xl font-bold ${
                        theme === "dark" ? "text-white" : "text-gray-900"
                      }`}
                    >
                      {insights.concentration.herfindahl_index.toFixed(3)}
                    </div>
                  </div>
                </div>
              </div>

              {insights.concentration.warnings.length > 0 && (
                <div>
                  <h4
                    className={`text-sm font-semibold mb-2 ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}
                  >
                    Concentration Warnings
                  </h4>
                  {insights.concentration.warnings.map((warning: any, idx: number) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg mb-2 ${
                        warning.risk_level === "high"
                          ? theme === "dark"
                            ? "bg-red-500/10 border border-red-500/20"
                            : "bg-red-50 border border-red-200"
                          : theme === "dark"
                          ? "bg-yellow-500/10 border border-yellow-500/20"
                          : "bg-yellow-50 border border-yellow-200"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <AlertCircle
                          className={`w-4 h-4 ${
                            warning.risk_level === "high" ? "text-red-500" : "text-yellow-500"
                          }`}
                        />
                        <span
                          className={`text-sm ${
                            theme === "dark" ? "text-zinc-300" : "text-gray-700"
                          }`}
                        >
                          {warning.message}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Volatility Tab */}
          {activeTab === "volatility" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between mb-4">
                <h3
                  className={`text-lg font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}
                >
                  Volatility Breakdown
                </h3>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    insights.volatility.risk_label === "balanced"
                      ? theme === "dark"
                        ? "bg-green-500/10 text-green-400"
                        : "bg-green-50 text-green-600"
                      : insights.volatility.risk_label === "moderate"
                      ? theme === "dark"
                        ? "bg-yellow-500/10 text-yellow-400"
                        : "bg-yellow-50 text-yellow-600"
                      : theme === "dark"
                      ? "bg-red-500/10 text-red-400"
                      : "bg-red-50 text-red-600"
                  }`}
                >
                  {insights.volatility.risk_label}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Stablecoins */}
                <div
                  className={`p-4 rounded-lg ${
                    theme === "dark"
                      ? "bg-green-500/5 border border-green-500/10"
                      : "bg-green-50 border border-green-100"
                  }`}
                >
                  <div className="text-3xl mb-2">🟢</div>
                  <div
                    className={`text-sm mb-1 ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}
                  >
                    Stablecoins
                  </div>
                  <div
                    className={`text-2xl font-bold ${
                      theme === "dark" ? "text-white" : "text-gray-900"
                    }`}
                  >
                    ${insights.volatility.stablecoins.value_usd.toLocaleString()}
                  </div>
                  <div
                    className={`text-lg ${theme === "dark" ? "text-green-400" : "text-green-600"}`}
                  >
                    {insights.volatility.stablecoins.percentage.toFixed(1)}%
                  </div>
                </div>

                {/* Volatile */}
                <div
                  className={`p-4 rounded-lg ${
                    theme === "dark"
                      ? "bg-orange-500/5 border border-orange-500/10"
                      : "bg-orange-50 border border-orange-100"
                  }`}
                >
                  <div className="text-3xl mb-2">🔴</div>
                  <div
                    className={`text-sm mb-1 ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}
                  >
                    Volatile Assets
                  </div>
                  <div
                    className={`text-2xl font-bold ${
                      theme === "dark" ? "text-white" : "text-gray-900"
                    }`}
                  >
                    ${insights.volatility.volatile.value_usd.toLocaleString()}
                  </div>
                  <div
                    className={`text-lg ${
                      theme === "dark" ? "text-orange-400" : "text-orange-600"
                    }`}
                  >
                    {insights.volatility.volatile.percentage.toFixed(1)}%
                  </div>
                </div>
              </div>

              {insights.volatility.stablecoin_list.length > 0 && (
                <div>
                  <h4
                    className={`text-sm font-semibold mb-2 ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}
                  >
                    Stablecoins Held
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {insights.volatility.stablecoin_list.map((coin: string, idx: number) => (
                      <span
                        key={idx}
                        className={`px-3 py-1 rounded-full text-sm font-medium ${
                          theme === "dark"
                            ? "bg-zinc-800 text-zinc-300"
                            : "bg-gray-100 text-gray-700"
                        }`}
                      >
                        {coin}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InsightsSection;