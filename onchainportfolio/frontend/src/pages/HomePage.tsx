// src/pages/HomePage.tsx - Portfolio Home Page (Wallet Group Support)
import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import SummaryCards from "../components/SummaryCards";
import BalancesTable from "../components/BalancesTable";
import NFTGallery from "../components/NFTGallery";
import { TrendingUp, TrendingDown, Wallet, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";

interface HomePageProps {
  onNavigateToAnalytics?: () => void;
}

const HomePage: React.FC<HomePageProps> = () => {
  const {
    activeWallet,
    activeWalletGroup,
    portfolioData,
    setPortfolioData,
    theme,
  } = useAppContext();

  const [loading, setLoading] = useState(false);
  const [_error, setError] = useState<string | null>(null);
  const [recentTxs, setRecentTxs] = useState<any[]>([]);
  const [nftData, setNftData] = useState<any>(null);
  const [loadingNfts, setLoadingNfts] = useState(false);

  const loadPortfolio = async (showToast: boolean = false) => {
    // Use wallet group if available, fall back to single wallet
    if (!activeWalletGroup && !activeWallet) return;

    setLoading(true);
    setError(null);

    const toastId = showToast ? toast.loading("Refreshing portfolio...") : null;

    try {
      let balancesWithWallet: any[];
      let totalUsdValue = 0;
      let chainsQueried: string[] = [];

      if (activeWalletGroup && activeWalletGroup.wallets.length > 0) {
        // Build wallet pairs from the group
        const walletPairs = activeWalletGroup.wallets.map(w => ({
          address: w.address,
          chain: w.chain,
        }));

        console.log("[HomePage] Loading group portfolio for:", activeWalletGroup.label, walletPairs);

        const groupData = await api.getGroupPortfolio(walletPairs, true);

        balancesWithWallet = groupData.all_balances.map((bal: any) => ({
          ...bal,
          wallet_name: activeWalletGroup.label,
        }));

        totalUsdValue = groupData.total_usd_value || 0;
        chainsQueried = groupData.chains_queried || [];

      } else if (activeWallet) {
        // Fallback: single wallet (backward compatibility)
        if (activeWallet.chain === 'evm') {
          const multiChainData = await api.getMultiChainPortfolio(activeWallet.address, true);
          balancesWithWallet = multiChainData.all_balances.map((bal: any) => ({
            ...bal,
            wallet_name: activeWallet.label,
            wallet_address: activeWallet.address,
          }));
          totalUsdValue = multiChainData.total_usd_value || 0;
          chainsQueried = multiChainData.chains_queried || [];
        } else {
          const portfolio = await api.getPortfolio(activeWallet.address, activeWallet.chain);
          balancesWithWallet = portfolio.balances.map((bal: any) => ({
            ...bal,
            wallet_name: activeWallet.label,
            wallet_address: activeWallet.address,
            chain: bal.chain || activeWallet.chain,
          }));
          totalUsdValue = portfolio.total_usd_value || 0;
          chainsQueried = [activeWallet.chain];
        }
      } else {
        return;
      }

      const displayLabel = activeWalletGroup?.label || activeWallet?.label || "Unknown";
      const displayAddress = activeWallet?.address || activeWalletGroup?.wallets[0]?.address || "";
      const displayChain = activeWallet?.chain || activeWalletGroup?.chains[0] || "unknown";

      setPortfolioData({
        balances: balancesWithWallet,
        total_usd_value: totalUsdValue,
        address: displayAddress,
        wallet_name: displayLabel,
        chain: displayChain,
        chains_queried: chainsQueried,
      });

      // Load recent transactions from the first wallet in the group
      try {
        const txWallet = activeWalletGroup?.wallets[0] || activeWallet;
        if (txWallet) {
          const txChain = txWallet.chain === 'evm' ? 'ethereum_sepolia' : txWallet.chain;
          const txs = await api.getTransactions(txWallet.address, txChain);
          setRecentTxs(txs.slice(0, 5));
        }
      } catch (txErr) {
        console.error("Failed to load transactions:", txErr);
      }

      if (toastId) {
        toast.success("Portfolio refreshed!", { id: toastId });
      }

    } catch (error: any) {
      console.error("Failed to load portfolio:", error);
      setError("Failed to load portfolio data");

      if (toastId) {
        toast.error("Failed to refresh portfolio", { id: toastId });
      }
    } finally {
      setLoading(false);
    }
  };

  // Fetch NFTs for active wallet group (non-EVM wallets only)
  const fetchNFTs = async (showToast: boolean = false) => {
    // Find a non-EVM wallet in the group to fetch NFTs for
    const nftWallet = activeWalletGroup?.wallets.find(w => w.chain !== 'evm') || activeWallet;
    if (!nftWallet || nftWallet.chain === 'evm') {
      setNftData(null);
      return;
    }

    setLoadingNfts(true);

    const toastId = showToast ? toast.loading("Loading NFTs...") : null;

    try {
      const data = await api.getWalletNFTs(nftWallet.address, nftWallet.chain);

      setNftData({
        all_nfts: data.nfts,
        collections: data.collections,
        total_nfts: data.total_count,
        total_collections: data.collections?.length || 0,
      });

      if (toastId && data.total_count > 0) {
        toast.success(`Found ${data.total_count} NFTs!`, { id: toastId });
      } else if (toastId) {
        toast.success("NFTs loaded", { id: toastId });
      }
    } catch (err) {
      console.error("Failed to fetch NFTs:", err);
      setNftData(null);
      if (toastId) {
        toast.error("Failed to load NFTs", { id: toastId });
      }
    } finally {
      setLoadingNfts(false);
    }
  };

  // Reload when active wallet group changes
  useEffect(() => {
    if (activeWalletGroup && activeWalletGroup.wallets.length > 0) {
      loadPortfolio();
      fetchNFTs();
    } else if (activeWallet) {
      // Fallback for legacy single wallet
      loadPortfolio();
      fetchNFTs();
    } else {
      setPortfolioData(null);
      setNftData(null);
      setError(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeWalletGroup?.id, activeWallet?.address]);

  // Loading state
  if (loading && !portfolioData) {
    return (
      <div className={`rounded-xl p-12 text-center ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200"
      }`}>
        <div className="flex justify-center mb-4">
          <RefreshCw className={`w-8 h-8 animate-spin ${theme === "dark" ? "text-white" : "text-black"}`} />
        </div>
        <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
          Loading portfolio...
        </p>
      </div>
    );
  }

  // No wallet connected
  if (!activeWalletGroup && !activeWallet) {
    return (
      <div className={`rounded-xl p-16 text-center ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200"
      }`}>
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 ${
          theme === "dark" ? "bg-blue-500/10" : "bg-blue-50"
        }`}>
          <Wallet className="w-8 h-8 text-blue-500" />
        </div>
        <h3 className={`text-2xl font-bold mb-3 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          Connect Your Wallet
        </h3>
        <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
          Click "Connect Wallet" in the header to get started
        </p>
      </div>
    );
  }

  // Get chain emoji
  const getChainEmoji = (chain: string) => {
    const emojis: Record<string, string> = {
      aptos: '⬢',
      solana: '◎',
      ethereum: 'Ξ',
      ethereum_sepolia: 'Ξ',
      polygon: '⬡',
      polygon_amoy: '⬡',
      base: '🔵',
      base_sepolia: '🔵',
      evm: '🔗', // Multi-chain EVM
    };
    return emojis[chain] || '⬢';
  };

  // Get chain display name
  const getChainDisplayName = (chain: string) => {
    if (chain === 'evm') return 'Multi-Chain';
    return chain.charAt(0).toUpperCase() + chain.slice(1).replace('_', ' ');
  };

  // Get chain badge style
  const getChainBadgeStyle = (chain: string) => {
    const styles: Record<string, { dark: string; light: string }> = {
      aptos: {
        dark: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
        light: "bg-blue-50 text-blue-600 border border-blue-200"
      },
      solana: {
        dark: "bg-purple-500/10 text-purple-400 border border-purple-500/20",
        light: "bg-purple-50 text-purple-600 border border-purple-200"
      },
      ethereum: {
        dark: "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20",
        light: "bg-gray-50 text-gray-600 border border-gray-200"
      },
      ethereum_sepolia: {
        dark: "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20",
        light: "bg-gray-50 text-gray-600 border border-gray-200"
      },
      polygon: {
        dark: "bg-violet-500/10 text-violet-400 border border-violet-500/20",
        light: "bg-violet-50 text-violet-600 border border-violet-200"
      },
      polygon_amoy: {
        dark: "bg-violet-500/10 text-violet-400 border border-violet-500/20",
        light: "bg-violet-50 text-violet-600 border border-violet-200"
      },
      base: {
        dark: "bg-blue-600/10 text-blue-500 border border-blue-600/20",
        light: "bg-blue-50 text-blue-600 border border-blue-200"
      },
      base_sepolia: {
        dark: "bg-blue-600/10 text-blue-500 border border-blue-600/20",
        light: "bg-blue-50 text-blue-600 border border-blue-200"
      },
      evm: {
        dark: "bg-gradient-to-r from-blue-500/10 to-purple-500/10 text-blue-400 border border-blue-500/20",
        light: "bg-gradient-to-r from-blue-50 to-purple-50 text-blue-600 border border-blue-200"
      },
    };
    const style = styles[chain] || styles.aptos;
    return theme === "dark" ? style.dark : style.light;
  };

  // Get top movers
  const topGainer = portfolioData?.balances?.sort((a: any, b: any) =>
    (b.price_change_24h || 0) - (a.price_change_24h || 0)
  )[0];

  const topLoser = portfolioData?.balances?.sort((a: any, b: any) =>
    (a.price_change_24h || 0) - (b.price_change_24h || 0)
  )[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold flex items-center gap-2 ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}>
            Portfolio Overview
            {activeWalletGroup ? (
              <span className="text-lg">{activeWalletGroup.icon}</span>
            ) : activeWallet ? (
              <span className="text-lg">{getChainEmoji(activeWallet.chain)}</span>
            ) : null}
          </h2>
          <p className={`text-sm mt-1 flex items-center gap-2 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            <span className="font-medium text-blue-500">
              {activeWalletGroup?.label || activeWallet?.label || "Unknown"}
            </span>
            {activeWalletGroup ? (
              <span className="flex items-center gap-1">
                {activeWalletGroup.chains.map((chain) => (
                  <span
                    key={chain}
                    className={`px-2 py-0.5 rounded text-xs font-medium ${getChainBadgeStyle(chain)}`}
                  >
                    {getChainDisplayName(chain)}
                  </span>
                ))}
              </span>
            ) : activeWallet ? (
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${getChainBadgeStyle(activeWallet.chain)}`}>
                {getChainDisplayName(activeWallet.chain)}
              </span>
            ) : null}
          </p>
        </div>
        <button
          onClick={() => loadPortfolio(true)}
          disabled={loading}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
            theme === "dark"
              ? "bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border border-zinc-800"
              : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
          } disabled:opacity-50`}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <SummaryCards data={portfolioData} />

      {/* Top Movers & Recent Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Movers */}
        <div className={`rounded-xl p-6 ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <h3 className={`text-lg font-bold mb-4 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            24h Movers
          </h3>
          <div className="space-y-3">
            {topGainer && topGainer.price_change_24h > 0 && (
              <div className={`p-3 rounded-lg ${
                theme === "dark" ? "bg-green-500/5" : "bg-green-50"
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                        {topGainer.symbol}
                      </span>
                    </div>
                    <p className={`text-xs mt-1 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                      Top Gainer
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-green-500 font-semibold">
                      +{topGainer.price_change_24h.toFixed(2)}%
                    </div>
                    <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                      ${topGainer.usd_value?.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            )}
            {topLoser && topLoser.price_change_24h < 0 && (
              <div className={`p-3 rounded-lg ${
                theme === "dark" ? "bg-red-500/5" : "bg-red-50"
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-red-500" />
                      <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                        {topLoser.symbol}
                      </span>
                    </div>
                    <p className={`text-xs mt-1 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                      Top Loser
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-red-500 font-semibold">
                      {topLoser.price_change_24h.toFixed(2)}%
                    </div>
                    <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                      ${topLoser.usd_value?.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            )}
            {(!topGainer?.price_change_24h || topGainer.price_change_24h <= 0) &&
             (!topLoser?.price_change_24h || topLoser.price_change_24h >= 0) && (
              <p className={`text-sm text-center py-4 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                No price changes in the last 24h
              </p>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className={`rounded-xl p-6 ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <h3 className={`text-lg font-bold mb-4 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            Recent Activity
          </h3>
          {recentTxs.length > 0 ? (
            <div className="space-y-2">
              {recentTxs.map((tx: any, idx: number) => (
                <div key={idx} className={`p-2 rounded text-sm ${
                  theme === "dark" ? "hover:bg-zinc-800" : "hover:bg-gray-50"
                } transition-colors cursor-pointer`}>
                  <div className="flex items-center justify-between">
                    <span className={theme === "dark" ? "text-zinc-300" : "text-gray-700"}>
                      {tx.type}
                    </span>
                    <span className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                      {new Date(tx.timestamp).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className={`text-sm ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
              No recent activity
            </p>
          )}
        </div>
      </div>


      {/* NFT Collection Section */}
      {nftData && nftData.total_nfts > 0 && (
        <div className={`rounded-xl overflow-hidden ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <div className={`px-6 py-4 border-b ${
            theme === "dark" ? "border-zinc-800" : "border-gray-200"
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                  NFT Collection
                </h3>
                <p className={`text-sm mt-0.5 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                  Digital collectibles in this wallet
                </p>
              </div>
              <button
                onClick={() => fetchNFTs(true)}
                disabled={loadingNfts}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 ${
                  theme === "dark"
                    ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                } disabled:opacity-50`}
              >
                {loadingNfts ? (
                  <>
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-3 h-3" />
                    Refresh
                  </>
                )}
              </button>
            </div>
          </div>
          <div className="p-6">
            <NFTGallery
              nfts={nftData.all_nfts}
              collections={nftData.collections}
              totalNfts={nftData.total_nfts}
              totalCollections={nftData.total_collections}
              loading={loadingNfts}
            />
          </div>
        </div>
      )}

      {/* Token Balances */}
      {portfolioData?.balances && portfolioData.balances.length > 0 && (
        <div className={`rounded-xl overflow-hidden ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <div className={`px-6 py-4 border-b ${
            theme === "dark" ? "border-zinc-800" : "border-gray-200"
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                  Token Balances
                </h3>
                <p className={`text-sm mt-0.5 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                  {activeWalletGroup && activeWalletGroup.chains.length > 1
                    ? `Your holdings across ${activeWalletGroup.chains.map(c => getChainDisplayName(c)).join(', ')}`
                    : `Your holdings on ${getChainDisplayName(activeWallet?.chain || activeWalletGroup?.chains[0] || 'unknown')}`}
                </p>
              </div>
            </div>
          </div>
          <BalancesTable balances={portfolioData.balances} showWalletColumn={false} />
        </div>
      )}
    </div>
  );
};

export default HomePage;
