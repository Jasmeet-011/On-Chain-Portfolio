import React from "react";
import { useAppContext } from "../context/AppContext";
import Logo from "./Logo";
import WalletBar from "./WalletBar";
import { MOCK_MODE } from "../api";

const Header: React.FC = () => {
  const { theme } = useAppContext();

  return (
    <header
      className={`sticky top-0 z-50 backdrop-blur-xl border-b ${
        theme === "dark"
          ? "bg-gray-900/80 border-gray-800"
          : "bg-white/80 border-gray-200"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Logo />
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 bg-yellow-500/10 text-yellow-400 text-xs font-semibold rounded-full border border-yellow-500/20">
                Testnet
              </span>
              {MOCK_MODE && (
                <span className="px-3 py-1 bg-purple-500/10 text-purple-400 text-xs font-semibold rounded-full border border-purple-500/20">
                  Demo
                </span>
              )}
            </div>
          </div>
          <WalletBar />
        </div>
      </div>
    </header>
  );
};

export default Header;
