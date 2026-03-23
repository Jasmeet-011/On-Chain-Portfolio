import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import SummaryCards from "../components/SummaryCards";
import BalancesTable from "../components/BalancesTable";
import NFTGallery from "../components/NFTGallery";
import { SkeletonSummaryCards } from "../components/ui";
import { TrendingUp, TrendingDown, Wallet, RefreshCw } from "lucide-react";
import { getChainColors } from "../utils/tokens";
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

  const isDark = theme === "dark";

  const loadPortfolio = async (showToast: boolean = false) => {
    if (!activeWalletGroup && !activeWallet) return;

    setLoading(true);
    setError(null);

    const toastId = showToast ? toast.loading("Refreshing portfolio...") : null;

    try {
      let balancesWithWallet: any[];
      let totalUsdValue = 0;
      let chainsQueried: string[] = [];

      if (activeWalletGroup && activeWalletGroup.wallets.length > 0) {
        const walletPairs = activeWalletGroup.wallets.map(w => ({
          address: w.address,
          chain: w.chain,
        }));

        const groupData = await api.getGroupPortfolio(walletPairs, true);

        balancesWithWallet = groupData.all_balances.map((bal: any) => ({
          ...bal,
          wallet_name: activeWalletGroup.label,
        }));

        totalUsdValue = groupData.total_usd_value || 0;
        chainsQueried = groupData.chains_queried || [];

      } else if (activeWallet) {
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

      const displayLabel   = activeWalletGroup?.label || activeWallet?.label || "Unknown";
      const displayAddress = activeWallet?.address || activeWalletGroup?.wallets[0]?.address || "";
      const displayChain   = activeWallet?.chain  || activeWalletGroup?.chains[0] || "unknown";

      setPortfolioData({
        balances: balancesWithWallet,
        total_usd_value: totalUsdValue,
        address: displayAddress,
        wallet_name: displayLabel,
        chain: displayChain,
        chains_queried: chainsQueried,
      });

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

      if (toastId) toast.success("Portfolio refreshed!", { id: toastId });

    } catch (error: any) {
      console.error("Failed to load portfolio:", error);
      setError("Failed to load portfolio data");
      if (toastId) toast.error("Failed to refresh portfolio", { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  const fetchNFTs = async (showToast: boolean = false) => {
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

      if (toastId) {
        toast.success(data.total_count > 0 ? `Found ${data.total_count} NFTs!` : "NFTs loaded", { id: toastId });
      }
    } catch (err) {
      console.error("Failed to fetch NFTs:", err);
      setNftData(null);
      if (toastId) toast.error("Failed to load NFTs", { id: toastId });
    } finally {
      setLoadingNfts(false);
    }
  };

  useEffect(() => {
    if (activeWalletGroup && activeWalletGroup.wallets.length > 0) {
      loadPortfolio();
      fetchNFTs();
    } else if (activeWallet) {
      loadPortfolio();
      fetchNFTs();
    } else {
      setPortfolioData(null);
      setNftData(null);
      setError(null);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeWalletGroup?.id, activeWallet?.address]);

  const getChainDisplayName = (chain: string) => {
    if (chain === 'evm') return 'Multi-Chain';
    return chain.charAt(0).toUpperCase() + chain.slice(1).replace('_', ' ');
  };

  // No wallet connected
  if (!activeWalletGroup && !activeWallet) {
    return (
      <div className={`rounded-xl py-20 text-center border ${
        isDark ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200"
      }`}>
        <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5 ${
          isDark ? "bg-blue-500/10 border border-blue-500/20" : "bg-blue-50 border border-blue-100"
        }`}>
          <Wallet className="w-7 h-7 text-blue-500" />
        </div>
        <p className={`text-base font-semibold mb-1.5 ${isDark ? "text-white" : "text-gray-900"}`}>
          Connect Your Wallet
        </p>
        <p className={`text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
          Click "Connect Wallet" in the header to get started
        </p>
      </div>
    );
  }

  // Loading initial data
  if (loading && !portfolioData) {
    return (
      <div className="space-y-6">
        <SkeletonSummaryCards />
        <div className={`rounded-xl p-8 text-center border ${isDark ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200"}`}>
          <div className="flex items-center justify-center gap-2">
            <RefreshCw className={`w-5 h-5 animate-spin ${isDark ? "text-zinc-400" : "text-gray-400"}`} />
            <span className={`text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>Loading portfolio…</span>
          </div>
        </div>
      </div>
    );
  }

  const topGainer = portfolioData?.balances?.slice().sort((a: any, b: any) =>
    (b.price_change_24h || 0) - (a.price_change_24h || 0)
  )[0];

  const topLoser = portfolioData?.balances?.slice().sort((a: any, b: any) =>
    (a.price_change_24h || 0) - (b.price_change_24h || 0)
  )[0];

  const sectionClass = `rounded-xl overflow-hidden border ${
    isDark ? "bg-zinc-900 border-zinc-800/80" : "bg-white border-gray-200 shadow-sm"
  }`;
  const sectionHeaderClass = `px-5 py-4 border-b ${isDark ? "border-zinc-800/80" : "border-gray-200"}`;

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-xl font-bold ${isDark ? "text-white" : "text-gray-900"}`}>
            Portfolio Overview
          </h2>
          <div className={`flex items-center gap-2 mt-1 text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
            <span className="font-medium text-blue-400">
              {activeWalletGroup?.label || activeWallet?.label || "Unknown"}
            </span>
            {(activeWalletGroup?.chains || (activeWallet ? [activeWallet.chain] : [])).map((chain) => {
              const c = getChainColors(chain);
              return (
                <span key={chain} className={`px-2 py-0.5 rounded-md text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}>
                  {getChainDisplayName(chain)}
                </span>
              );
            })}
          </div>
        </div>

        <button
          onClick={() => loadPortfolio(true)}
          disabled={loading}
          className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 disabled:opacity-50 ${
            isDark
              ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border border-zinc-700"
              : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <SummaryCards data={portfolioData} />

      {/* Top Movers + Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Top Movers */}
        <div className={sectionClass}>
          <div className={sectionHeaderClass}>
            <p className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>24h Movers</p>
          </div>
          <div className="p-5 space-y-3">
            {topGainer && topGainer.price_change_24h > 0 && (
              <div className={`p-3 rounded-lg ${isDark ? "bg-emerald-500/5 border border-emerald-500/10" : "bg-emerald-50 border border-emerald-100"}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-emerald-500" />
                      <span className={`text-sm font-medium ${isDark ? "text-white" : "text-gray-900"}`}>
                        {topGainer.symbol}
                      </span>
                    </div>
                    <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>Top Gainer</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-emerald-500 font-numeric">
                      +{topGainer.price_change_24h.toFixed(2)}%
                    </p>
                    <p className={`text-xs font-numeric ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                      ${topGainer.usd_value?.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}
            {topLoser && topLoser.price_change_24h < 0 && (
              <div className={`p-3 rounded-lg ${isDark ? "bg-red-500/5 border border-red-500/10" : "bg-red-50 border border-red-100"}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-red-500" />
                      <span className={`text-sm font-medium ${isDark ? "text-white" : "text-gray-900"}`}>
                        {topLoser.symbol}
                      </span>
                    </div>
                    <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>Top Loser</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-red-500 font-numeric">
                      {topLoser.price_change_24h.toFixed(2)}%
                    </p>
                    <p className={`text-xs font-numeric ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                      ${topLoser.usd_value?.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}
            {(!topGainer?.price_change_24h || topGainer.price_change_24h <= 0) &&
             (!topLoser?.price_change_24h  || topLoser.price_change_24h  >= 0) && (
              <p className={`text-sm text-center py-4 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                No price changes in the last 24h
              </p>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className={sectionClass}>
          <div className={sectionHeaderClass}>
            <p className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Recent Activity</p>
          </div>
          <div className="p-5">
            {recentTxs.length > 0 ? (
              <div className="space-y-1">
                {recentTxs.map((tx: any, idx: number) => (
                  <div
                    key={idx}
                    className={`px-3 py-2.5 rounded-lg text-sm transition-colors ${
                      isDark ? "hover:bg-zinc-800/60" : "hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={isDark ? "text-zinc-300" : "text-gray-700"}>{tx.type}</span>
                      <span className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                        {new Date(tx.timestamp).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className={`text-sm text-center py-4 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                No recent activity
              </p>
            )}
          </div>
        </div>
      </div>

      {/* NFT Collection */}
      {nftData && nftData.total_nfts > 0 && (
        <div className={sectionClass}>
          <div className={sectionHeaderClass}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>NFT Collection</p>
                <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
                  {nftData.total_nfts} NFT{nftData.total_nfts !== 1 ? "s" : ""} · {nftData.total_collections} collection{nftData.total_collections !== 1 ? "s" : ""}
                </p>
              </div>
              <button
                onClick={() => fetchNFTs(true)}
                disabled={loadingNfts}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 disabled:opacity-50 ${
                  isDark ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <RefreshCw className={`w-3 h-3 ${loadingNfts ? "animate-spin" : ""}`} />
                {loadingNfts ? "Loading…" : "Refresh"}
              </button>
            </div>
          </div>
          <div className="p-5">
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
        <div className={sectionClass}>
          <div className={sectionHeaderClass}>
            <p className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>Token Balances</p>
            <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
              {activeWalletGroup && activeWalletGroup.chains.length > 1
                ? `Holdings across ${activeWalletGroup.chains.map(c => getChainDisplayName(c)).join(", ")}`
                : `Holdings on ${getChainDisplayName(activeWallet?.chain || activeWalletGroup?.chains[0] || "unknown")}`}
            </p>
          </div>
          <BalancesTable balances={portfolioData.balances} showWalletColumn={false} />
        </div>
      )}
    </div>
  );
};

export default HomePage;
