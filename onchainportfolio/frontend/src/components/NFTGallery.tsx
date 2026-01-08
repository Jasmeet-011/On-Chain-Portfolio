// src/components/NFTGallery.tsx - UPDATED: Complete with all props
import React from "react";
import { useAppContext } from "../context/AppContext";

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
  loading = false 
}) => {
  const { theme } = useAppContext();

  // Loading state
  if (loading) {
    return (
      <div className={`rounded-xl p-8 ${
        theme === "dark" ? "bg-zinc-900" : "bg-white"
      }`}>
        <div className="flex items-center justify-center gap-2">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            Loading NFTs...
          </span>
        </div>
      </div>
    );
  }

  // Empty state
  if (!nfts || nfts.length === 0) {
    return (
      <div className={`rounded-xl p-8 text-center ${
        theme === "dark" ? "bg-zinc-900" : "bg-white"
      }`}>
        <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${
          theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
        }`}>
          <span className="text-3xl">🖼️</span>
        </div>
        <h3 className={`text-lg font-semibold mb-2 ${
          theme === "dark" ? "text-white" : "text-gray-900"
        }`}>
          No NFTs Found
        </h3>
        <p className={theme === "dark" ? "text-zinc-500" : "text-gray-500"}>
          Connect a wallet with NFTs to see them here
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      {totalNfts > 0 && (
        <div className={`rounded-xl p-6 ${
          theme === "dark" ? "bg-zinc-900" : "bg-white"
        }`}>
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
            }`}>
              <span className="text-2xl">🖼️</span>
            </div>
            <div>
              <h3 className={`text-lg font-semibold ${
                theme === "dark" ? "text-white" : "text-gray-900"
              }`}>
                Your NFT Collection
              </h3>
              <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
                {totalNfts} NFT{totalNfts !== 1 ? 's' : ''} across {totalCollections} collection{totalCollections !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          {/* Collection Breakdown */}
          {collections.length > 0 && (
            <div className="mt-6 space-y-2">
              <h4 className={`text-sm font-medium mb-3 ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}>
                By Collection
              </h4>
              {collections.map((collection, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between p-3 rounded-lg ${
                    theme === "dark" ? "bg-zinc-800" : "bg-gray-50"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={theme === "dark" ? "text-zinc-300" : "text-gray-700"}>
                      {collection.collection_name}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      collection.chain === "solana"
                        ? theme === "dark" ? "bg-purple-500/20 text-purple-300" : "bg-purple-100 text-purple-700"
                        : theme === "dark" ? "bg-blue-500/20 text-blue-300" : "bg-blue-100 text-blue-700"
                    }`}>
                      {collection.chain === "solana" ? "◎ Solana" : "⬢ Aptos"}
                    </span>
                  </div>
                  <span className={`font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}>
                    {collection.count}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* NFT Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {nfts.map((nft, i) => (
          <div
            key={i}
            className={`rounded-xl overflow-hidden border transition-all duration-200 hover:scale-105 cursor-pointer ${
              theme === "dark"
                ? "bg-zinc-900 border-zinc-800 hover:border-purple-500/50"
                : "bg-white border-gray-200 hover:border-purple-400"
            }`}
          >
            {/* NFT Image */}
            <div className={`relative aspect-square ${
              theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
            }`}>
              {nft.image_url ? (
                <img
                  src={nft.image_url}
                  alt={nft.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    // Fallback if image fails to load
                    e.currentTarget.style.display = 'none';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="text-4xl">🖼️</span>
                </div>
              )}
              
              {/* Chain Badge */}
              <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium ${
                nft.chain === "solana"
                  ? "bg-purple-500 text-white"
                  : "bg-blue-500 text-white"
              }`}>
                {nft.chain === "solana" ? "◎" : "⬢"}
              </div>
            </div>

            {/* NFT Info */}
            <div className="p-3">
              <p className={`text-sm font-semibold truncate ${
                theme === "dark" ? "text-white" : "text-gray-900"
              }`} title={nft.name}>
                {nft.name}
              </p>
              <p className={`text-xs mt-1 truncate ${
                theme === "dark" ? "text-zinc-500" : "text-gray-500"
              }`} title={nft.collection}>
                {nft.collection}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NFTGallery;