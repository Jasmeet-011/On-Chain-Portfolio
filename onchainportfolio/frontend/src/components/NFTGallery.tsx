import React from "react";
import { useAppContext } from "../context/AppContext";
import { Image } from "lucide-react";
import { getChainColors } from "../utils/tokens";

interface NFT {
  name: string;
  collection: string;
  image_url?: string;
  token_id?: string;
  chain: string;
}

interface CollectionSummary {
  collection_name: string;
  count: number;
  chain: string;
}

interface Props {
  nfts?: NFT[];
  collections?: CollectionSummary[];
  totalNfts?: number;
  totalCollections?: number;
  loading?: boolean;
}

const NFTGallery: React.FC<Props> = ({
  nfts = [],
  collections = [],
  totalNfts = 0,
  totalCollections = 0,
  loading = false,
}) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-8">
        <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span className={`text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>Loading NFTs…</span>
      </div>
    );
  }

  if (!nfts || nfts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 ${
          isDark ? "bg-zinc-800 border border-zinc-700/50" : "bg-gray-100 border border-gray-200"
        }`}>
          <Image className={`w-6 h-6 ${isDark ? "text-zinc-400" : "text-gray-400"}`} />
        </div>
        <p className={`text-sm font-semibold mb-1 ${isDark ? "text-white" : "text-gray-900"}`}>No NFTs Found</p>
        <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-500"}`}>Connect a wallet with NFTs to see them here</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Summary + Collection Breakdown */}
      {totalNfts > 0 && collections.length > 0 && (
        <div className="space-y-2">
          <p className={`text-xs font-semibold uppercase tracking-wider ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
            By Collection
          </p>
          {collections.map((col, i) => {
            const c = getChainColors(col.chain);
            return (
              <div
                key={i}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg ${
                  isDark ? "bg-zinc-800/60" : "bg-gray-50"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className={`text-sm ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
                    {col.collection_name}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-md border font-medium ${c.bg} ${c.text} ${c.border}`}>
                    {col.chain.charAt(0).toUpperCase() + col.chain.slice(1)}
                  </span>
                </div>
                <span className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
                  {col.count}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* NFT Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
        {nfts.map((nft, i) => {
          const c = getChainColors(nft.chain);
          return (
            <div
              key={i}
              className={`rounded-xl overflow-hidden border transition-all duration-200 hover:scale-[1.02] cursor-pointer ${
                isDark
                  ? "bg-zinc-800/60 border-zinc-700/50 hover:border-zinc-600"
                  : "bg-white border-gray-200 hover:border-gray-300 shadow-sm"
              }`}
            >
              {/* Image */}
              <div className={`relative aspect-square ${isDark ? "bg-zinc-800" : "bg-gray-100"}`}>
                {nft.image_url ? (
                  <img
                    src={nft.image_url}
                    alt={nft.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                      const parent = e.currentTarget.parentElement;
                      if (parent) {
                        const fallback = parent.querySelector(".nft-fallback") as HTMLElement;
                        if (fallback) fallback.style.display = "flex";
                      }
                    }}
                  />
                ) : null}
                <div
                  className="nft-fallback w-full h-full absolute inset-0 items-center justify-center"
                  style={{ display: nft.image_url ? "none" : "flex" }}
                >
                  <Image className={`w-8 h-8 ${isDark ? "text-zinc-600" : "text-gray-300"}`} />
                </div>
                {/* Chain badge */}
                <span className={`absolute top-1.5 right-1.5 text-xs px-1.5 py-0.5 rounded-md font-medium border ${c.bg} ${c.text} ${c.border}`}>
                  {nft.chain.slice(0, 3).toUpperCase()}
                </span>
              </div>

              {/* Info */}
              <div className="px-3 py-2.5">
                <p className={`text-xs font-semibold truncate ${isDark ? "text-white" : "text-gray-900"}`} title={nft.name}>
                  {nft.name}
                </p>
                <p className={`text-xs mt-0.5 truncate ${isDark ? "text-zinc-500" : "text-gray-400"}`} title={nft.collection}>
                  {nft.collection}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default NFTGallery;
