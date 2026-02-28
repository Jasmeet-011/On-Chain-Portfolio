import React from "react";
import { useAppContext } from "../context/AppContext";
import { TrendingUp, DollarSign, Image, BarChart3 } from "lucide-react";

interface Props {
  onAction: (text: string) => void;
}

const actions = [
  { text: "What tokens do I hold?",               icon: TrendingUp, accent: "text-blue-400",   ring: "group-hover:bg-blue-500/10"   },
  { text: "What's my portfolio value in USD?",    icon: DollarSign, accent: "text-emerald-400", ring: "group-hover:bg-emerald-500/10" },
  { text: "List my NFTs",                         icon: Image,      accent: "text-purple-400",  ring: "group-hover:bg-purple-500/10"  },
  { text: "How much USDC do I have in lending?",  icon: BarChart3,  accent: "text-amber-400",   ring: "group-hover:bg-amber-500/10"   },
];

const QuickActions: React.FC<Props> = ({ onAction }) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";

  return (
    <div className={`rounded-2xl border ${
      isDark
        ? "bg-zinc-900 border-zinc-700/60"
        : "bg-white border-gray-200 shadow-sm"
    }`}>
      <div className="p-5">
        <h3 className={`text-sm font-semibold mb-4 ${isDark ? "text-zinc-200" : "text-gray-800"}`}>
          Quick Actions
        </h3>
        <div className="flex flex-col gap-2">
          {actions.map((action, i) => {
            const Icon = action.icon;
            return (
              <button
                key={i}
                onClick={() => onAction(action.text)}
                className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-left transition-all duration-200 ${
                  isDark
                    ? "bg-zinc-800/50 hover:bg-zinc-800 text-zinc-300 hover:text-zinc-100 border border-zinc-700/50 hover:border-zinc-600"
                    : "bg-gray-50 hover:bg-gray-100 text-gray-700 hover:text-gray-900 border border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                  isDark ? "bg-zinc-700/60" : "bg-white border border-gray-200"
                } ${action.ring}`}>
                  <Icon className={`w-3.5 h-3.5 ${action.accent}`} />
                </div>
                <span>{action.text}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default QuickActions;
