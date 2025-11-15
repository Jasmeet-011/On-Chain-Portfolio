import React from "react";
import { useAppContext } from "../context/AppContext";

interface Props {
  onAction: (text: string) => void;
}

const QuickActions: React.FC<Props> = ({ onAction }) => {
  const { theme } = useAppContext();

  const actions = [
    { text: "What tokens do I hold?", icon: "💰" },
    { text: "What's my portfolio value in USD?", icon: "💵" },
    { text: "List my NFTs", icon: "🖼️" },
    { text: "How much USDC do I have in lending?", icon: "📊" },
  ];

  return (
    <div
      className={`rounded-2xl border backdrop-blur-sm ${
        theme === "dark"
          ? "bg-gray-800/50 border-gray-700"
          : "bg-white/50 border-gray-200"
      }`}
    >
      <div className="p-5">
        <h3
          className={`font-semibold mb-4 ${
            theme === "dark" ? "text-gray-200" : "text-gray-900"
          }`}
        >
          Quick Actions
        </h3>
        <div className="flex flex-col gap-2">
          {actions.map((action, i) => (
            <button
              key={i}
              onClick={() => onAction(action.text)}
              className={`px-4 py-3 rounded-xl text-sm text-left transition-all duration-200 group ${
                theme === "dark"
                  ? "bg-gray-700/50 hover:bg-gradient-to-r hover:from-blue-500/20 hover:to-purple-500/20 text-gray-300 hover:text-white border border-gray-700 hover:border-blue-500/30"
                  : "bg-gray-50 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 text-gray-700 hover:text-gray-900 border border-gray-200 hover:border-blue-300"
              }`}
            >
              <span className="mr-2">{action.icon}</span>
              {action.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuickActions;
