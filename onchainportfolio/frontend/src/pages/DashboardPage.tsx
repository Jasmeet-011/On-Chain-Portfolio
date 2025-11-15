import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import SummaryCards from "../components/SummaryCards";
import BalancesTable from "../components/BalancesTable";
import NFTGallery from "../components/NFTGallery";
import PositionsTable from "../components/PositionsTable";

const DashboardPage: React.FC = () => {
  const {
    wallet,
    portfolioData,
    setPortfolioData,
    manualAddress,
    theme,
  } = useAppContext();
  const [loading, setLoading] = useState(false);

  const loadPortfolio = async () => {
    const walletAddr =
      wallet.connected && wallet.address
        ? wallet.address
        : manualAddress;
    if (!walletAddr) return;

    setLoading(true);
    try {
      const response = await api.chat(
        "get portfolio snapshot",
        walletAddr,
      );
      setPortfolioData(response.data);
    } catch (error) {
      console.error("Failed to load portfolio:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (
      (wallet.connected && wallet.address) ||
      manualAddress
    ) {
      loadPortfolio();
    }
  }, [wallet.connected, wallet.address, manualAddress]);

  if (!portfolioData && !loading) {
    return (
      <div
        className={`rounded-2xl border backdrop-blur-sm p-16 text-center ${
          theme === "dark"
            ? "bg-gray-800/50 border-gray-700"
            : "bg-white/50 border-gray-200"
        }`}
      >
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-6">
          <span className="text-4xl">📊</span>
        </div>
        <h3
          className={`text-2xl font-bold mb-3 ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}
        >
          No Portfolio Data
        </h3>
        <p
          className={`max-w-md mx-auto mb-6 ${
            theme === "dark" ? "text-gray-400" : "text-gray-600"
          }`}
        >
          Connect your wallet or enter a Testnet address in the
          Chat tab to view your portfolio analytics
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div
        className={`rounded-2xl border backdrop-blur-sm p-16 text-center ${
          theme === "dark"
            ? "bg-gray-800/50 border-gray-700"
            : "bg-white/50 border-gray-200"
        }`}
      >
        <div className="flex items-center justify-center gap-2">
          <div
            className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"
            style={{ animationDelay: "0ms" }}
          ></div>
          <div
            className="w-3 h-3 bg-purple-500 rounded-full animate-bounce"
            style={{ animationDelay: "150ms" }}
          ></div>
          <div
            className="w-3 h-3 bg-blue-500 rounded-full animate-bounce"
            style={{ animationDelay: "300ms" }}
          ></div>
        </div>
        <p
          className={`mt-4 ${
            theme === "dark" ? "text-gray-400" : "text-gray-600"
          }`}
        >
          Loading portfolio...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2
            className={`text-3xl font-bold mb-1 ${
              theme === "dark" ? "text-white" : "text-gray-900"
            }`}
          >
            Portfolio Dashboard
          </h2>
          <p
            className={`text-sm ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}
          >
            Real-time overview of your on-chain assets
          </p>
        </div>
        <button
          onClick={loadPortfolio}
          disabled={loading}
          className={`px-5 py-2.5 rounded-xl font-medium transition-all duration-200 ${
            theme === "dark"
              ? "bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700"
              : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
          } disabled:opacity-50`}
        >
          🔄 Refresh
        </button>
      </div>

      <SummaryCards data={portfolioData || {}} />

      {portfolioData?.balances &&
        portfolioData.balances.length > 0 && (
          <div
            className={`rounded-2xl border backdrop-blur-sm ${
              theme === "dark"
                ? "bg-gray-800/50 border-gray-700"
                : "bg-white/50 border-gray-200"
            }`}
          >
            <div className="p-6">
              <h3
                className={`text-xl font-bold mb-1 ${
                  theme === "dark"
                    ? "text-white"
                    : "text-gray-900"
                }`}
              >
                Token Balances
              </h3>
              <p
                className={`text-sm mb-4 ${
                  theme === "dark"
                    ? "text-gray-400"
                    : "text-gray-600"
                }`}
              >
                Your token holdings across Aptos
              </p>
              <BalancesTable
                balances={portfolioData.balances}
                prices={portfolioData.prices}
              />
            </div>
          </div>
        )}

      {portfolioData?.nfts &&
        portfolioData.nfts.length > 0 && (
          <div
            className={`rounded-2xl border backdrop-blur-sm ${
              theme === "dark"
                ? "bg-gray-800/50 border-gray-700"
                : "bg-white/50 border-gray-200"
            }`}
          >
            <div className="p-6">
              <h3
                className={`text-xl font-bold mb-1 ${
                  theme === "dark"
                    ? "text-white"
                    : "text-gray-900"
                }`}
              >
                NFT Collection
              </h3>
              <p
                className={`text-sm mb-4 ${
                  theme === "dark"
                    ? "text-gray-400"
                    : "text-gray-600"
                }`}
              >
                Digital collectibles in your wallet
              </p>
              <NFTGallery nfts={portfolioData.nfts} />
            </div>
          </div>
        )}

      {portfolioData?.positions &&
        portfolioData.positions.length > 0 && (
          <div
            className={`rounded-2xl border backdrop-blur-sm ${
              theme === "dark"
                ? "bg-gray-800/50 border-gray-700"
                : "bg-white/50 border-gray-200"
            }`}
          >
            <div className="p-6">
              <h3
                className={`text-xl font-bold mb-1 ${
                  theme === "dark"
                    ? "text-white"
                    : "text-gray-900"
                }`}
              >
                DeFi Positions
              </h3>
              <p
                className={`text-sm mb-4 ${
                  theme === "dark"
                    ? "text-gray-400"
                    : "text-gray-600"
                }`}
              >
                Your lending and borrowing activities
              </p>
              <PositionsTable
                positions={portfolioData.positions}
              />
            </div>
          </div>
        )}
    </div>
  );
};

export default DashboardPage;
