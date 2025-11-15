import React from "react";
import { useAppContext } from "../context/AppContext";
import { formatUSD } from "../utils";

interface Props {
  data: any;
}

const SummaryCards: React.FC<Props> = ({ data }) => {
  const { theme } = useAppContext();

  const totalValue =
    data.balances?.reduce((sum: number, bal: any) => {
      const price = data.prices?.[bal.symbol] || 0;
      return sum + bal.display_amount * price;
    }, 0) || 0;

  const tokenCount = data.balances?.length || 0;
  const nftCount = data.nfts?.length || 0;
  const protocolCount =
    new Set(
      data.positions?.map((p: any) => p.protocol)
    ).size || 0;

  const cards = [
    {
      label: "Total Portfolio",
      value: formatUSD(totalValue),
      icon: "💎",
      gradient: "from-blue-500 to-cyan-500",
    },
    {
      label: "Tokens",
      value: tokenCount.toString(),
      icon: "🪙",
      gradient: "from-purple-500 to-pink-500",
    },
    {
      label: "NFTs",
      value: nftCount.toString(),
      icon: "🖼️",
      gradient: "from-orange-500 to-red-500",
    },
    {
      label: "Protocols",
      value: protocolCount.toString(),
      icon: "⚡",
      gradient: "from-green-500 to-emerald-500",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, i) => (
        <div
          key={i}
          className={`rounded-2xl border backdrop-blur-sm p-6 transition-all duration-200 hover:scale-105 ${
            theme === "dark"
              ? "bg-gray-800/50 border-gray-700"
              : "bg-white/50 border-gray-200"
          }`}
        >
          <div className="flex items-start justify-between mb-3">
            <div
              className={`w-12 h-12 rounded-xl bg-gradient-to-br ${card.gradient} flex items-center justify-center text-2xl`}
            >
              {card.icon}
            </div>
          </div>
          <p
            className={`text-sm font-medium mb-1 ${
              theme === "dark" ? "text-gray-400" : "text-gray-600"
            }`}
          >
            {card.label}
          </p>
          <p
            className={`text-2xl font-bold ${
              theme === "dark" ? "text-white" : "text-gray-900"
            }`}
          >
            {card.value}
          </p>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;
