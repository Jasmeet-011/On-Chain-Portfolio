// src/components/SummaryCards.tsx - WITH HOVER EFFECT + CONSISTENT THEME
import React from "react";
import { useAppContext } from "../context/AppContext";
import { formatUSD } from "../utils";

interface Props {
  data: any;
}

const SummaryCards: React.FC<Props> = ({ data }) => {
  const { theme } = useAppContext();

  const totalValue = data?.total_usd_value || 0;
  const balances = data?.balances || [];
  const nfts = data?.nfts || [];
  const positions = data?.positions || [];

  const cards = [
    {
      label: "Total Value",
      value: formatUSD(totalValue),
      icon: "💎",
      // Keep gradient for icons (visual distinction is good)
      iconGradient: "from-blue-500 to-cyan-500",
      // Consistent background colors
      bgColor: theme === "dark" ? "bg-blue-500/10" : "bg-blue-50",
      borderColor: theme === "dark" ? "border-blue-500/20" : "border-blue-200",
    },
    {
      label: "Tokens",
      value: balances.length.toString(),
      icon: "🪙",
      iconGradient: "from-purple-500 to-pink-500",
      bgColor: theme === "dark" ? "bg-purple-500/10" : "bg-purple-50",
      borderColor: theme === "dark" ? "border-purple-500/20" : "border-purple-200",
    },
    {
      label: "NFTs",
      value: nfts.length.toString(),
      icon: "🖼️",
      iconGradient: "from-orange-500 to-red-500",
      bgColor: theme === "dark" ? "bg-orange-500/10" : "bg-orange-50",
      borderColor: theme === "dark" ? "border-orange-500/20" : "border-orange-200",
    },
    {
      label: "Protocols",
      value: positions.length.toString(),
      icon: "🔒",
      iconGradient: "from-green-500 to-emerald-500",
      bgColor: theme === "dark" ? "bg-green-500/10" : "bg-green-50",
      borderColor: theme === "dark" ? "border-green-500/20" : "border-green-200",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          // ✅ ADDED BACK: hover:scale-105 for enlarge effect
          className={`rounded-xl p-6 border transition-all duration-200 hover:scale-105 hover:shadow-lg ${
            card.borderColor
          } ${card.bgColor} ${
            theme === "dark" ? "" : "shadow-sm"
          }`}
        >
          <div className="flex items-start justify-between mb-4">
            {/* Icon with gradient (keeps visual distinction) */}
            <div className={`w-12 h-12 rounded-lg bg-gradient-to-br ${card.iconGradient} flex items-center justify-center text-2xl shadow-lg`}>
              {card.icon}
            </div>
          </div>
          <div>
            <p className={`text-sm font-medium mb-1 ${
              theme === "dark" ? "text-slate-400" : "text-slate-600"
            }`}>
              {card.label}
            </p>
            <p className={`text-2xl font-bold ${
              theme === "dark" ? "text-white" : "text-slate-900"
            }`}>
              {card.value}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;