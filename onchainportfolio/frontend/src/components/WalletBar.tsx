import React from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress } from "../utils";

const WalletBar: React.FC = () => {
  const { wallet, theme, toggleTheme } = useAppContext();

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={toggleTheme}
        className={`p-2.5 rounded-xl transition-all duration-200 ${
          theme === "dark"
            ? "bg-gray-800 text-yellow-400 hover:bg-gray-700 border border-gray-700"
            : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
        }`}
        title={`Switch to ${
          theme === "dark" ? "light" : "dark"
        } mode`}
      >
        {theme === "dark" ? "☀️" : "🌙"}
      </button>

      {wallet.connected && wallet.address ? (
        <>
          <div
            className={`px-4 py-2 rounded-xl font-mono text-sm border ${
              theme === "dark"
                ? "bg-gray-800 border-gray-700 text-gray-300"
                : "bg-white border-gray-200 text-gray-700"
            }`}
          >
            {shortenAddress(wallet.address)}
          </div>
          <button
            onClick={wallet.disconnect}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
              theme === "dark"
                ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20"
                : "bg-red-50 text-red-600 hover:bg-red-100 border border-red-200"
            }`}
          >
            Disconnect
          </button>
        </>
      ) : (
        <button
          onClick={wallet.connect}
          className="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/50 transition-all duration-200"
        >
          Connect Wallet
        </button>
      )}
    </div>
  );
};

export default WalletBar;
