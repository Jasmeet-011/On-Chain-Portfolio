// src/components/Header.tsx - PROFESSIONAL: Black/White/Gray Theme
import React from "react";
import { useAppContext } from "../context/AppContext";
import { Sun, Moon, LogOut, Settings } from "lucide-react";
import Logo from "./Logo";
import WalletBar from "./WalletBar";
import { MOCK_MODE } from "../api";

interface HeaderProps {
  onLogout?: () => void;
  onManageWallets?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLogout, onManageWallets }) => {
  const { theme, toggleTheme, wallets } = useAppContext();

  return (
    <header
      className={`sticky top-0 z-50 backdrop-blur-md border-b ${
        theme === "dark"
          ? "bg-zinc-950/95 border-zinc-800"
          : "bg-white/95 border-gray-200"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Logo & Badges */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <Logo size="md" theme={theme} />
            
            <div className="hidden lg:flex items-center gap-2">
              <span className={`px-2 py-1 text-xs font-medium rounded ${
                theme === "dark"
                  ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                  : "bg-yellow-50 text-yellow-600 border border-yellow-200"
              }`}>
                Testnet
              </span>
              {MOCK_MODE && (
                <span className={`px-2 py-1 text-xs font-medium rounded ${
                  theme === "dark"
                    ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                    : "bg-purple-50 text-purple-600 border border-purple-200"
                }`}>
                  Demo
                </span>
              )}
            </div>
          </div>

          {/* Right: Wallet + Theme + Logout */}
          <div className="flex items-center gap-2">
            {/* Wallet Bar */}
            <WalletBar />

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className={`p-2.5 rounded-lg transition-all hover:scale-105 ${
                theme === "dark"
                  ? "bg-zinc-900 hover:bg-zinc-800 border border-zinc-800"
                  : "bg-gray-100 hover:bg-gray-200 border border-gray-200"
              }`}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <Sun className="w-5 h-5 text-yellow-400" />
              ) : (
                <Moon className="w-5 h-5 text-gray-700" />
              )}
            </button>

            {/* Logout Button */}
            {onLogout && (
              <button
                onClick={onLogout}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  theme === "dark"
                    ? "text-zinc-400 hover:text-red-400 hover:bg-red-500/10 border border-zinc-800 hover:border-red-500/20"
                    : "text-gray-600 hover:text-red-600 hover:bg-red-50 border border-gray-200 hover:border-red-200"
                }`}
                title="Logout"
              >
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;