// src/components/SummaryCards.tsx - PROFESSIONAL with Lucide Icons
import React from "react";
import { useAppContext } from "../context/AppContext";
import { formatUSD } from "../utils";
import { DollarSign, Coins, Image, Lock } from "lucide-react";

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
      icon: DollarSign,
      iconColor: "text-blue-500",
      bgColor: theme === "dark" ? "bg-blue-500/5" : "bg-blue-50",
      borderColor: theme === "dark" ? "border-blue-500/10" : "border-blue-200",
      hoverBorder: theme === "dark" ? "hover:border-blue-500/30" : "hover:border-blue-300",
    },
    {
      label: "Tokens",
      value: balances.length.toString(),
      icon: Coins,
      iconColor: "text-purple-500",
      bgColor: theme === "dark" ? "bg-purple-500/5" : "bg-purple-50",
      borderColor: theme === "dark" ? "border-purple-500/10" : "border-purple-200",
      hoverBorder: theme === "dark" ? "hover:border-purple-500/30" : "hover:border-purple-300",
    },
    {
      label: "NFTs",
      value: nfts.length.toString(),
      icon: Image,
      iconColor: "text-orange-500",
      bgColor: theme === "dark" ? "bg-orange-500/5" : "bg-orange-50",
      borderColor: theme === "dark" ? "border-orange-500/10" : "border-orange-200",
      hoverBorder: theme === "dark" ? "hover:border-orange-500/30" : "hover:border-orange-300",
    },
    {
      label: "Protocols",
      value: positions.length.toString(),
      icon: Lock,
      iconColor: "text-green-500",
      bgColor: theme === "dark" ? "bg-green-500/5" : "bg-green-50",
      borderColor: theme === "dark" ? "border-green-500/10" : "border-green-200",
      hoverBorder: theme === "dark" ? "hover:border-green-500/30" : "hover:border-green-300",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        
        return (
          <div
            key={index}
            className={`group rounded-xl p-6 border transition-all duration-300 cursor-default ${
              card.borderColor
            } ${card.bgColor} ${card.hoverBorder} ${
              theme === "dark" ? "" : "shadow-sm hover:shadow-md"
            } hover:scale-[1.02]`}
          >
            <div className="flex items-start justify-between mb-4">
              {/* Icon */}
              <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                theme === "dark" ? "bg-zinc-900" : "bg-white"
              } ${
                theme === "dark" ? "border border-zinc-800" : "shadow-sm"
              } group-hover:scale-110 transition-transform duration-300`}>
                <Icon className={`w-6 h-6 ${card.iconColor}`} />
              </div>
            </div>
            <div>
              <p className={`text-sm font-medium mb-1 ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}>
                {card.label}
              </p>
              <p className={`text-2xl font-bold ${
                theme === "dark" ? "text-white" : "text-gray-900"
              }`}>
                {card.value}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SummaryCards;