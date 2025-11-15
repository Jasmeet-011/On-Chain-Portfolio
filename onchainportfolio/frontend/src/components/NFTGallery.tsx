import React from "react";
import { useAppContext } from "../context/AppContext";

interface Props {
  nfts: any[];
}

const NFTGallery: React.FC<Props> = ({ nfts }) => {
  const { theme } = useAppContext();

  if (!nfts || nfts.length === 0) return null;

  return (
    <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
      {nfts.map((nft, i) => (
        <div
          key={i}
          className={`rounded-xl overflow-hidden border transition-all duration-200 hover:scale-105 ${
            theme === "dark"
              ? "bg-gray-800 border-gray-700 hover:border-purple-500/50"
              : "bg-white border-gray-200 hover:border-purple-400"
          }`}
        >
          <img
            src={
              nft.media_url ||
              "https://via.placeholder.com/200/CCCCCC/666666?text=NFT"
            }
            alt={nft.name}
            className="w-full h-40 object-cover"
          />
          <div className="p-3">
            <p
              className={`text-sm font-semibold ${
                theme === "dark" ? "text-gray-200" : "text-gray-900"
              }`}
            >
              {nft.name}
            </p>
            <p
              className={`text-xs mt-1 ${
                theme === "dark" ? "text-gray-500" : "text-gray-500"
              }`}
            >
              {nft.collection}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default NFTGallery;
