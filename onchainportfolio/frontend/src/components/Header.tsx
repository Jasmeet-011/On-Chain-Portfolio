// src/components/Header.tsx - FIXED: Pass theme to Logo
import React from "react";
import { useAppContext } from "../context/AppContext";
import Logo from "./Logo";
import WalletBar from "./WalletBar";
import { MOCK_MODE } from "../api";

interface HeaderProps {
  onLogout?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLogout }) => {
  const { theme } = useAppContext();

  return (
    <header
      className={`sticky top-0 z-50 backdrop-blur-md border-b shadow-sm ${
        theme === "dark"
          ? "bg-slate-900/95 border-slate-800 shadow-black/20"
          : "bg-white/95 border-slate-200 shadow-slate-200/50"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Logo & Network Badge */}
          <div className="flex items-center gap-4">
            {/* ✅ FIXED: Pass theme prop to Logo */}
            <Logo size="md" theme={theme} />
            
            <div className="hidden sm:flex items-center gap-2">
              <span className={`px-2.5 py-1 text-xs font-semibold rounded-md ${
                theme === "dark"
                  ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                  : "bg-yellow-50 text-yellow-700 border border-yellow-300"
              }`}>
                Testnet
              </span>
              {MOCK_MODE && (
                <span className={`px-2.5 py-1 text-xs font-semibold rounded-md ${
                  theme === "dark"
                    ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                    : "bg-purple-50 text-purple-700 border border-purple-300"
                }`}>
                  Demo Mode
                </span>
              )}
            </div>
          </div>
          
          {/* Right: Wallet & Actions */}
          <div className="flex items-center gap-3">
            <WalletBar />
            
            {onLogout && (
              <button
                onClick={onLogout}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  theme === "dark"
                    ? "text-slate-400 hover:text-white hover:bg-slate-800"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
                title="Logout"
              >
                Logout
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;