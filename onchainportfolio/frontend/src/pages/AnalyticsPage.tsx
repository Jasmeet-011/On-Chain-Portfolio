// src/pages/AnalyticsPage.tsx - UPDATED: Added Insights Section
import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import PortfolioHistoryChart from "../components/PortfolioHistoryChart";
import TokenMiniChart from "../components/TokenMiniChart";
import InsightsSection from "../components/InsightsSection";
import { BarChart3, RefreshCw, Lightbulb, TrendingUp } from "lucide-react";

interface UniqueToken {
  symbol: string;
  balance: number;
  chain: string;
}

type AnalyticsScope = 'complete' | string; // 'complete' or wallet address

const AnalyticsPage: React.FC = () => {
  const { theme, activeWallet, wallets, portfolioData, setPortfolioData } = useAppContext();
  
  const [selectedScope, setSelectedScope] = useState<AnalyticsScope>('complete');
  const [scopeLabel, setScopeLabel] = useState<string>('Complete Portfolio');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getScopeOptions = () => {
    const options: Array<{ value: AnalyticsScope; label: string; chain?: string }> = [
      { value: 'complete', label: 'Complete Portfolio (All Wallets)' },
    ];

    wallets.forEach((wallet) => {
      const chainEmoji = wallet.chain === 'aptos' ? '⬢' : '◎';
      options.push({
        value: wallet.address,
        label: `${chainEmoji} ${wallet.label}`,
        chain: wallet.chain,
      });
    });

    return options;
  };

  const loadPortfolio = async (scope: AnalyticsScope) => {
    if (wallets.length === 0) {
      setPortfolioData(null);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      if (scope === 'complete') {
        console.log('[Analytics] Loading complete portfolio for all wallets');
        
        const allBalances: any[] = [];
        let totalValue = 0;

        for (const wallet of wallets) {
          try {
            const portfolio = await api.getPortfolio(wallet.address, wallet.chain);
            
            const balancesWithWallet = portfolio.balances.map((bal: any) => ({
              ...bal,
              wallet_name: wallet.label,
              wallet_address: wallet.address,
              chain: wallet.chain,
            }));
            
            allBalances.push(...balancesWithWallet);
            totalValue += portfolio.total_usd_value || 0;
          } catch (err) {
            console.error(`Failed to load wallet ${wallet.label}:`, err);
          }
        }
        
        setPortfolioData({
          balances: allBalances,
          total_usd_value: totalValue,
          address: 'aggregate',
          wallet_name: 'Complete Portfolio',
          chain: 'multi-chain',
        });
        
        setScopeLabel('Complete Portfolio');
        
      } else {
        const wallet = wallets.find(w => w.address === scope);
        if (!wallet) {
          setError('Selected wallet not found');
          return;
        }

        console.log(`[Analytics] Loading portfolio for ${wallet.chain} wallet:`, wallet.address);
        
        const portfolio = await api.getPortfolio(wallet.address, wallet.chain);
        
        const balancesWithWallet = portfolio.balances.map((bal: any) => ({
          ...bal,
          wallet_name: wallet.label,
          wallet_address: wallet.address,
          chain: wallet.chain,
        }));
        
        setPortfolioData({
          balances: balancesWithWallet,
          total_usd_value: portfolio.total_usd_value || 0,
          address: portfolio.address || wallet.address,
          wallet_name: wallet.label,
          chain: wallet.chain,
        });
        
        setScopeLabel(wallet.label);
      }
      
    } catch (error) {
      console.error("[Analytics] Failed to load portfolio:", error);
      setError("Failed to load portfolio data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (wallets.length > 0) {
      loadPortfolio(selectedScope);
    }
  }, [selectedScope, wallets.length]);

  useEffect(() => {
    if (wallets.length > 0 && selectedScope === 'complete') {
      loadPortfolio('complete');
    }
  }, [wallets.length]);

  // No wallet connected
  if (wallets.length === 0) {
    return (
      <div className={`rounded-xl p-16 text-center ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
      }`}>
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 ${
          theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
        }`}>
          <BarChart3 className={`w-8 h-8 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
        </div>
        <h3 className={`text-2xl font-bold mb-3 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          No Wallets Connected
        </h3>
        <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
          Connect a wallet to view analytics
        </p>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Portfolio Analytics
            </h2>
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
              Loading {scopeLabel}...
            </p>
          </div>
        </div>

        <div className={`rounded-xl p-12 text-center ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <div className="flex justify-center mb-4">
            <RefreshCw className={`w-8 h-8 animate-spin ${theme === "dark" ? "text-white" : "text-black"}`} />
          </div>
          <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            Loading portfolio data...
          </p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Portfolio Analytics
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <label className={`text-sm font-medium ${
              theme === "dark" ? "text-zinc-400" : "text-gray-600"
            }`}>
              Analyzing:
            </label>
            <select
              value={selectedScope}
              onChange={(e) => setSelectedScope(e.target.value)}
              className={`px-4 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
                theme === "dark"
                  ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                  : "bg-white border-gray-200 text-gray-900 focus:ring-black focus:border-black"
              }`}
            >
              {getScopeOptions().map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className={`rounded-xl p-12 text-center ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <div className="text-4xl mb-4">⚠️</div>
          <h3 className={`text-xl font-bold mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            Error Loading Portfolio
          </h3>
          <p className={`mb-6 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            {error}
          </p>
          <button
            onClick={() => loadPortfolio(selectedScope)}
            className={`px-6 py-2.5 rounded-lg font-medium transition-colors ${
              theme === "dark"
                ? "bg-white text-black hover:bg-gray-200"
                : "bg-black text-white hover:bg-gray-800"
            }`}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Get unique tokens from portfolio
  const tokens = portfolioData?.balances || [];
  
  const uniqueTokens: UniqueToken[] = tokens.reduce((acc: UniqueToken[], balance: any) => {
    if (!balance || !balance.symbol || balance.amount === undefined) {
      return acc;
    }
    
    const existing = acc.find((t: UniqueToken) => t.symbol === balance.symbol && t.chain === balance.chain);
    if (!existing) {
      acc.push({
        symbol: balance.symbol,
        balance: Number(balance.amount) || 0,
        chain: balance.chain
      });
    } else {
      existing.balance += Number(balance.amount) || 0;
    }
    return acc;
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header with Scope Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            Portfolio Analytics
          </h2>
          <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            Viewing: <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>{scopeLabel}</span>
            {selectedScope === 'complete' && wallets.length > 1 && (
              <span className="ml-2">
                ({wallets.length} wallets aggregated)
              </span>
            )}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Scope Selector */}
          <div className="flex items-center gap-2">
            <label className={`text-sm font-medium whitespace-nowrap ${
              theme === "dark" ? "text-zinc-400" : "text-gray-600"
            }`}>
              Analyzing:
            </label>
            <select
              value={selectedScope}
              onChange={(e) => setSelectedScope(e.target.value)}
              className={`px-4 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
                theme === "dark"
                  ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                  : "bg-white border-gray-200 text-gray-900 focus:ring-black focus:border-black"
              }`}
            >
              {getScopeOptions().map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={() => loadPortfolio(selectedScope)}
            disabled={loading}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              theme === "dark"
                ? "bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border border-zinc-800"
                : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
            } disabled:opacity-50`}
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Portfolio Value Overview */}
      {portfolioData && (
        <div className={`rounded-xl p-6 ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <div className="flex items-center justify-between mb-2">
            <h3 className={`text-sm font-medium ${
              theme === "dark" ? "text-zinc-400" : "text-gray-600"
            }`}>
              Total Portfolio Value
            </h3>
            {selectedScope === 'complete' && (
              <span className={`text-xs px-2 py-1 rounded-full ${
                theme === "dark"
                  ? "bg-zinc-800 text-zinc-400 border border-zinc-700"
                  : "bg-gray-100 text-gray-600 border border-gray-200"
              }`}>
                Aggregated
              </span>
            )}
          </div>
          <div className={`text-4xl font-bold ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}>
            ${portfolioData.total_usd_value?.toFixed(2) || '0.00'}
          </div>
        </div>
      )}

      {/* Portfolio History Chart */}
      <div className={`rounded-xl p-6 ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
      }`}>
        <PortfolioHistoryChart selectedScope={selectedScope} />
      </div>

      {/* ✨ NEW: Portfolio Intelligence Section */}
      <InsightsSection />

      {/* Token Performance Section */}
      {uniqueTokens.length > 0 && (
        <div>
          <h3 className={`text-lg font-bold mb-4 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            Token Performance
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {uniqueTokens.map((token: UniqueToken) => (
              <TokenMiniChart
                key={`${token.symbol}-${token.chain}`}
                symbol={token.symbol}
                balance={token.balance}
                chain={token.chain}
                days={7}
              />
            ))}

            {/* Add More Tokens Card */}
            {uniqueTokens.length < 3 && (
              <div className={`rounded-xl p-6 border-2 border-dashed ${
                theme === "dark" ? "border-zinc-800" : "border-gray-200"
              }`}>
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <TrendingUp className={`w-12 h-12 mb-3 ${theme === "dark" ? "text-zinc-600" : "text-gray-400"}`} />
                  <p className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    {selectedScope === 'complete' ? 'Add more wallets' : 'Add more tokens'}
                  </p>
                  <p className={`text-xs mt-1 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                    {selectedScope === 'complete' 
                      ? 'Connect wallets with different tokens'
                      : 'Transfer more assets to this wallet'
                    }
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* No Tokens Message */}
      {uniqueTokens.length === 0 && (
        <div className={`rounded-xl p-12 text-center ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <TrendingUp className={`w-16 h-16 mx-auto mb-4 ${theme === "dark" ? "text-zinc-600" : "text-gray-400"}`} />
          <h3 className={`text-xl font-bold mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            No Tokens Found
          </h3>
          <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            {selectedScope === 'complete'
              ? 'None of your connected wallets have token balances yet'
              : 'This wallet doesn\'t have any token balances yet'
            }
          </p>
        </div>
      )}

      {/* Info Banner */}
      <div className={`rounded-xl p-4 ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-gray-50 border border-gray-200"
      }`}>
        <div className="flex items-start gap-3">
          <Lightbulb className={`w-5 h-5 mt-0.5 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
          <div>
            <p className={`text-sm font-medium ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
              Understanding Your Analytics
            </p>
            <p className={`text-xs mt-1 ${theme === "dark" ? "text-zinc-500" : "text-gray-600"}`}>
              {selectedScope === 'complete'
                ? 'Charts show your complete portfolio value aggregated across all wallets. Switch to individual wallets to see specific analytics.'
                : 'Charts show this wallet\'s value over time based on current holdings × historical prices. Data availability depends on wallet age.'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;