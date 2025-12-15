// src/pages/DashboardPage.tsx - PROFESSIONAL PRODUCTION UI
import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import SummaryCards from "../components/SummaryCards";
import BalancesTable from "../components/BalancesTable";
import TransactionsTable from "../components/TransactionsTable";

const DashboardPage: React.FC = () => {
  const {
    activeWallet,
    wallets,
    portfolioData,
    setPortfolioData,
    theme,
  } = useAppContext();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPortfolio = async () => {
    if (!activeWallet) return;

    setLoading(true);
    setError(null);
    
    try {
      const portfolio = await api.getPortfolio(activeWallet.address);
      
      const balancesWithWallet = portfolio.balances.map((bal: any) => ({
        ...bal,
        wallet_name: activeWallet.label,
        wallet_address: activeWallet.address,
      }));
      
      setPortfolioData({
        balances: balancesWithWallet,
        total_usd_value: portfolio.total_usd_value || 0,
        address: portfolio.address || activeWallet.address,
        wallet_name: activeWallet.label,
      });
      
    } catch (error) {
      console.error("Failed to load portfolio:", error);
      setError("Failed to load portfolio data");
    } finally {
      setLoading(false);
    }
  };

  const loadTransactionsWithFilters = async (address: string, params: any) => {
    return await api.getTransactionsFiltered(address, params);
  };

  useEffect(() => {
    if (activeWallet) {
      loadPortfolio();
    } else {
      setPortfolioData(null);
      setError(null);
    }
  }, [activeWallet?.address]);

  // Loading state
  if (loading) {
    return (
      <div className={`rounded-xl p-12 text-center ${
        theme === "dark" ? "bg-gray-800" : "bg-white border border-gray-200"
      }`}>
        <div className="flex justify-center mb-4">
          <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
        <p className={theme === "dark" ? "text-gray-400" : "text-gray-600"}>
          Loading portfolio...
        </p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`rounded-xl p-12 text-center ${
        theme === "dark" ? "bg-gray-800" : "bg-white border border-gray-200"
      }`}>
        <div className="text-4xl mb-4">⚠️</div>
        <h3 className={`text-xl font-bold mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          Error Loading Portfolio
        </h3>
        <p className={`mb-6 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
          {error}
        </p>
        <button
          onClick={loadPortfolio}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  // No wallet connected
  if (!activeWallet) {
    return (
      <div className={`rounded-xl p-16 text-center ${
        theme === "dark" ? "bg-gray-800" : "bg-white border border-gray-200"
      }`}>
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 ${
          theme === "dark" ? "bg-blue-500/10" : "bg-blue-50"
        }`}>
          <span className="text-3xl">💼</span>
        </div>
        <h3 className={`text-2xl font-bold mb-3 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          Connect Your Wallet
        </h3>
        <p className={theme === "dark" ? "text-gray-400" : "text-gray-600"}>
          Click "Connect Wallet" in the header to get started
        </p>
      </div>
    );
  }

  // Empty portfolio
  if (portfolioData && (!portfolioData.balances || portfolioData.balances.length === 0)) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Portfolio Dashboard
            </h2>
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              {activeWallet.label}
            </p>
          </div>
          <button
            onClick={loadPortfolio}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              theme === "dark"
                ? "bg-gray-800 text-gray-300 hover:bg-gray-700"
                : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
            }`}
          >
            🔄 Refresh
          </button>
        </div>

        <div className={`rounded-xl p-16 text-center ${
          theme === "dark" ? "bg-gray-800" : "bg-white border border-gray-200"
        }`}>
          <div className="text-4xl mb-4">💰</div>
          <h3 className={`text-xl font-bold mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            No Tokens Found
          </h3>
          <p className={theme === "dark" ? "text-gray-400" : "text-gray-600"}>
            This wallet doesn't have any token balances yet
          </p>
        </div>
      </div>
    );
  }

  // Portfolio with data
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            Portfolio Dashboard
          </h2>
          <p className={`text-sm mt-1 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
            <span className="font-medium text-blue-500">{activeWallet.label}</span>
            {wallets.length > 1 && (
              <span className="ml-2 text-gray-500">
                ({wallets.length} wallet{wallets.length !== 1 ? "s" : ""} total)
              </span>
            )}
          </p>
        </div>
        <button
          onClick={loadPortfolio}
          disabled={loading}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            theme === "dark"
              ? "bg-gray-800 text-gray-300 hover:bg-gray-700"
              : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
          } disabled:opacity-50`}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <SummaryCards data={portfolioData} />

      {/* Token Balances */}
      {portfolioData?.balances && portfolioData.balances.length > 0 && (
        <div className={`rounded-xl overflow-hidden ${
          theme === "dark" ? "bg-gray-800" : "bg-white border border-gray-200"
        }`}>
          <div className="px-6 py-4 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                  Token Balances
                </h3>
                <p className={`text-sm mt-0.5 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                  Your holdings on Aptos
                </p>
              </div>
              {wallets.length > 1 && (
                <span className={`text-xs px-3 py-1.5 rounded-full font-medium ${
                  theme === "dark"
                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                    : "bg-blue-50 text-blue-600 border border-blue-200"
                }`}>
                  {activeWallet.label}
                </span>
              )}
            </div>
          </div>
          <BalancesTable balances={portfolioData.balances} />
        </div>
      )}

      {/* Transaction History */}
      {activeWallet && (
        <div className={`rounded-xl overflow-hidden ${
          theme === "dark" ? "bg-gray-800" : "bg-white border border-gray-200"
        }`}>
          <div className="px-6 py-4 border-b border-gray-700">
            <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Transaction History
            </h3>
            <p className={`text-sm mt-0.5 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              Recent activity for {activeWallet.label}
            </p>
          </div>
          <div className="p-6">
            <TransactionsTable 
              address={activeWallet.address}
              onLoadTransactions={loadTransactionsWithFilters}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;