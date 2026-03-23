import React from "react";
import { useAppContext } from "../context/AppContext";
import { Sun, Moon, LogOut } from "lucide-react";
import Logo from "./Logo";
import WalletBar from "./WalletBar";
import { MOCK_MODE } from "../api";
import toast from "react-hot-toast";

interface HeaderProps {
  onLogout?: () => void;
  onManageWallets?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLogout }) => {
  const { theme, toggleTheme, networkMode, toggleNetwork } = useAppContext();

  const handleNetworkToggle = () => {
    toggleNetwork();
    const next = networkMode === "testnet" ? "Mainnet" : "Testnet";
    toast.success(`Switched to ${next}`, { duration: 2000 });
  };

  return (
    <header
      className={`sticky top-0 z-50 backdrop-blur-md border-b ${
        theme === "dark"
          ? "bg-zinc-950/95 border-zinc-800/80"
          : "bg-white/95 border-gray-200"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Left: Logo & badges */}
          <div className="flex items-center gap-3 shrink-0">
            <Logo size="md" theme={theme} />
            <div className="hidden lg:flex items-center gap-2">
              {/* Clickable network toggle */}
              <button
                onClick={handleNetworkToggle}
                title={`Currently on ${networkMode}. Click to switch.`}
                className={`px-2 py-0.5 text-xs font-medium rounded-md border transition-colors cursor-pointer ${
                  networkMode === "testnet"
                    ? "bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20"
                    : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20"
                }`}
              >
                {networkMode === "testnet" ? "Testnet" : "Mainnet"}
              </button>
              {MOCK_MODE && (
                <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  Demo
                </span>
              )}
            </div>
          </div>

          {/* Right: Wallet + actions */}
          <div className="flex items-center gap-1.5">
            <WalletBar />

            <button
              onClick={toggleTheme}
              className={`p-2 rounded-lg transition-colors ${
                theme === "dark"
                  ? "text-zinc-400 hover:text-white hover:bg-zinc-800 border border-transparent hover:border-zinc-700"
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-100 border border-transparent"
              }`}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            >
              {theme === "dark" ? (
                <Sun className="w-4.5 h-4.5" />
              ) : (
                <Moon className="w-4.5 h-4.5" />
              )}
            </button>

            {onLogout && (
              <button
                onClick={onLogout}
                className={`p-2 rounded-lg transition-colors ${
                  theme === "dark"
                    ? "text-zinc-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20"
                    : "text-gray-500 hover:text-red-600 hover:bg-red-50 border border-transparent"
                }`}
                title="Logout"
              >
                <LogOut className="w-4.5 h-4.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
