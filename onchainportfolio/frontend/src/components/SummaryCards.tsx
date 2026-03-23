import React from "react";
import { useAppContext } from "../context/AppContext";
import { formatUSD } from "../utils";
import { DollarSign, Coins, Image, Lock } from "lucide-react";

interface Props {
  data: any;
}

const SummaryCards: React.FC<Props> = ({ data }) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";

  const balances  = data?.balances  || [];
  const nfts      = data?.nfts      || [];
  const positions = data?.positions || [];

  const calculatedTotal = balances.reduce((sum: number, b: any) => {
    const value = b.usd_value || 0;
    return sum + (typeof value === "number" ? value : 0);
  }, 0);

  const totalValue =
    data?.total_usd_value && data.total_usd_value > 0
      ? data.total_usd_value
      : calculatedTotal;

  const cards = [
    { label: "Total Value", value: formatUSD(totalValue),          icon: DollarSign, accent: "#627EEA" },
    { label: "Tokens",      value: balances.length.toString(),     icon: Coins,      accent: "#9945FF" },
    { label: "NFTs",        value: nfts.length.toString(),         icon: Image,      accent: "#F59E0B" },
    { label: "Protocols",   value: positions.length.toString(),    icon: Lock,       accent: "#10B981" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div
            key={index}
            className={`group rounded-xl p-5 border transition-all duration-200 cursor-default ${
              isDark
                ? "bg-zinc-900 border-zinc-800/80 hover:border-zinc-700 hover:shadow-lg hover:shadow-black/20"
                : "bg-white border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300"
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center transition-transform duration-200 group-hover:scale-110"
                style={{
                  background: `${card.accent}18`,
                  border: `1px solid ${card.accent}30`,
                }}
              >
                <Icon className="w-5 h-5" style={{ color: card.accent }} />
              </div>
            </div>

            <p className={`text-xs font-semibold uppercase tracking-wider mb-1.5 ${
              isDark ? "text-zinc-500" : "text-gray-400"
            }`}>
              {card.label}
            </p>
            <p className={`text-2xl font-bold tracking-tight font-numeric ${
              isDark ? "text-white" : "text-gray-900"
            }`}>
              {card.value}
            </p>
          </div>
        );
      })}
    </div>
  );
};

export default SummaryCards;
