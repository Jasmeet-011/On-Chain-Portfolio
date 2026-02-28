// src/components/SummaryCards.tsx
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

  const balances = data?.balances || [];
  const nfts = data?.nfts || [];
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
    {
      label: "Total Value",
      value: formatUSD(totalValue),
      icon: DollarSign,
      accent: "#627EEA",
      glow: true,
    },
    {
      label: "Tokens",
      value: balances.length.toString(),
      icon: Coins,
      accent: "#9945FF",
      glow: false,
    },
    {
      label: "NFTs",
      value: nfts.length.toString(),
      icon: Image,
      accent: "#F59E0B",
      glow: false,
    },
    {
      label: "Protocols",
      value: positions.length.toString(),
      icon: Lock,
      accent: "#10B981",
      glow: false,
    },
  ];

  return (
    <>
      <style>{`
        @keyframes card-glow-pulse {
          0%, 100% { box-shadow: 0 0 0 0 transparent; }
          50% { box-shadow: 0 0 24px 2px rgba(98,126,234,0.15); }
        }
        .glow-card { animation: card-glow-pulse 3s ease-in-out infinite; }
      `}</style>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div
              key={index}
              className={`group rounded-xl p-6 border transition-all duration-300 cursor-default hover:scale-[1.02] ${
                card.glow ? "glow-card" : ""
              } ${
                isDark
                  ? "bg-zinc-900 border-zinc-800 hover:border-zinc-700"
                  : "bg-white border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300"
              }`}
              style={
                card.glow && isDark
                  ? { borderColor: `${card.accent}33` }
                  : {}
              }
            >
              <div className="flex items-start justify-between mb-4">
                <div
                  className="w-11 h-11 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110"
                  style={{
                    background: `${card.accent}18`,
                    border: `1px solid ${card.accent}30`,
                  }}
                >
                  <Icon className="w-5 h-5" style={{ color: card.accent }} />
                </div>

                {card.glow && (
                  <span
                    className="w-2 h-2 rounded-full animate-pulse"
                    style={{ background: card.accent, marginTop: "6px" }}
                  />
                )}
              </div>

              <p className={`text-xs font-semibold uppercase tracking-wider mb-1 ${
                isDark ? "text-zinc-500" : "text-gray-400"
              }`}>
                {card.label}
              </p>
              <p className={`text-2xl font-bold tracking-tight ${
                isDark ? "text-white" : "text-gray-900"
              }`}>
                {card.value}
              </p>
            </div>
          );
        })}
      </div>
    </>
  );
};

export default SummaryCards;
