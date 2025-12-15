// src/components/WalletBar.tsx - FULLY CONSISTENT BLUE THEME (NO GRADIENTS)
import React, { useState } from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress } from "../utils";
import ManageWalletsModal from "./ManageWalletsModal";

const WALLET_CONFIG: Record<string, { icon: string; color: string; displayName: string }> = {
  petra: { icon: "🔴", color: "from-red-500 to-orange-500", displayName: "Petra" },
  martian: { icon: "🟢", color: "from-green-500 to-emerald-500", displayName: "Martian" },
  pontem: { icon: "🟣", color: "from-purple-500 to-pink-500", displayName: "Pontem" },
  nightly: { icon: "🔵", color: "from-blue-500 to-indigo-500", displayName: "Nightly" },
  rise: { icon: "⚡", color: "from-yellow-500 to-orange-500", displayName: "Rise" },
  fewcha: { icon: "🦊", color: "from-orange-500 to-red-500", displayName: "Fewcha" },
  spika: { icon: "✨", color: "from-cyan-500 to-blue-500", displayName: "Spika" },
  blocto: { icon: "🔷", color: "from-blue-600 to-indigo-600", displayName: "Blocto" },
  manual: { icon: "📝", color: "from-gray-500 to-gray-600", displayName: "Manual" },
  other: { icon: "💼", color: "from-gray-500 to-gray-600", displayName: "Other" },
};

const WalletBar: React.FC = () => {
  const {
    theme,
    toggleTheme,
    wallets,
    activeWallet,
    setActiveWallet,
    addWallet,
    connectWallet,
    availableWallets,
    isWalletConnecting,
    walletError,
    clearWalletError,
  } = useAppContext();

  const [showDropdown, setShowDropdown] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [addWalletAddress, setAddWalletAddress] = useState("");
  const [addWalletName, setAddWalletName] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const getWalletType = (walletName: string): 'petra' | 'martian' | 'pontem' | 'nightly' | 'manual' => {
    const name = walletName.toLowerCase();
    if (name.includes('petra')) return 'petra';
    if (name.includes('martian')) return 'martian';
    if (name.includes('pontem')) return 'pontem';
    if (name.includes('nightly')) return 'nightly';
    return 'manual';
  };

  const getWalletConfig = (source: string) => {
    return WALLET_CONFIG[source] || WALLET_CONFIG.other;
  };

  const handleAddWallet = async () => {
    if (!addWalletAddress.trim()) return;

    setIsAdding(true);
    try {
      await addWallet(
        addWalletAddress.trim(),
        addWalletName.trim() || "Manual Wallet",
        wallets.length === 0,
        'manual'
      );

      setShowAddModal(false);
      setAddWalletAddress("");
      setAddWalletName("");
    } catch (error: any) {
      console.error("[WalletBar] Failed to add wallet:", error);
      alert(error?.message || "Failed to add wallet. Please check the address and try again.");
    } finally {
      setIsAdding(false);
    }
  };

  const handleConnectWallet = async (walletName: string) => {
    clearWalletError();
    try {
      await connectWallet(walletName);
      setShowAddModal(false);
    } catch (error: any) {
      console.error("[WalletBar] Connection failed:", error);
    }
  };

  const handleSelectWallet = (wallet: typeof activeWallet) => {
    setActiveWallet(wallet);
    setShowDropdown(false);
  };

  return (
    <div className="flex items-center gap-3">
      {/* Theme Toggle */}
      <button
        onClick={toggleTheme}
        className={`p-2 rounded-lg transition-colors ${
          theme === "dark"
            ? "bg-slate-800 text-yellow-400 hover:bg-slate-700 border border-slate-700"
            : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-200"
        }`}
        title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      >
        {theme === "dark" ? "☀️" : "🌙"}
      </button>

      {/* Wallet Section */}
      {activeWallet ? (
        <div className="flex items-center gap-2">
          {/* Wallet Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                theme === "dark"
                  ? "bg-slate-800 border-slate-700 hover:bg-slate-700"
                  : "bg-white border-slate-200 hover:bg-slate-50"
              }`}
            >
              <span className="text-sm">{getWalletConfig(activeWallet.type).icon}</span>
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <div className="flex flex-col items-start">
                <span className={`text-xs font-medium ${
                  theme === "dark" ? "text-slate-400" : "text-slate-500"
                }`}>
                  {activeWallet.label}
                </span>
                <span className={`font-mono text-sm ${
                  theme === "dark" ? "text-slate-300" : "text-slate-700"
                }`}>
                  {shortenAddress(activeWallet.address)}
                </span>
              </div>
              <svg
                className={`w-4 h-4 transition-transform ${
                  showDropdown ? "rotate-180" : ""
                } ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {showDropdown && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)} />
                <div className={`absolute right-0 mt-2 w-80 rounded-lg border shadow-lg z-20 ${
                  theme === "dark" ? "bg-slate-800 border-slate-700" : "bg-white border-slate-200"
                }`}>
                  <div className="p-2">
                    <div className={`px-3 py-2 text-xs font-medium ${
                      theme === "dark" ? "text-slate-500" : "text-slate-400"
                    }`}>
                      {wallets.length} {wallets.length === 1 ? 'Wallet' : 'Wallets'}
                    </div>

                    {wallets.map((wallet) => {
                      const config = getWalletConfig(wallet.type);
                      return (
                        <button
                          key={wallet.address}
                          onClick={() => handleSelectWallet(wallet)}
                          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                            activeWallet?.address === wallet.address
                              ? theme === "dark"
                                ? "bg-blue-600 text-white"
                                : "bg-blue-500 text-white"
                              : theme === "dark"
                              ? "hover:bg-slate-700 text-slate-200"
                              : "hover:bg-slate-50 text-slate-900"
                          }`}
                        >
                          <span className="text-lg">{config.icon}</span>
                          <div className={`w-2 h-2 rounded-full ${
                            activeWallet?.address === wallet.address ? "bg-white" : "bg-slate-400"
                          }`} />
                          <div className="flex-1 flex flex-col items-start">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">
                                {wallet.label}
                              </span>
                              {wallet.is_primary && (
                                <span className={`text-xs px-2 py-0.5 rounded-full ${
                                  activeWallet?.address === wallet.address
                                    ? "bg-white/20 text-white"
                                    : theme === "dark"
                                    ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                    : "bg-yellow-50 text-yellow-600 border border-yellow-200"
                                }`}>
                                  Primary
                                </span>
                              )}
                            </div>
                            <span className={`text-xs font-mono ${
                              activeWallet?.address === wallet.address
                                ? "text-white/80"
                                : theme === "dark"
                                ? "text-slate-400"
                                : "text-slate-500"
                            }`}>
                              {shortenAddress(wallet.address)}
                            </span>
                          </div>
                          {activeWallet?.address === wallet.address && (
                            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </button>
                      );
                    })}

                    <button
                      onClick={() => {
                        setShowDropdown(false);
                        setShowAddModal(true);
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-2 mt-2 rounded-lg border-2 border-dashed transition-colors ${
                        theme === "dark"
                          ? "border-slate-700 hover:bg-slate-700 text-slate-400"
                          : "border-slate-300 hover:bg-slate-50 text-slate-600"
                      }`}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span className="text-sm font-medium">Add New Wallet</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* Manage Wallets Button */}
          <button
            onClick={() => setShowManageModal(true)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              theme === "dark"
                ? "bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-200"
            }`}
            title="Manage wallets"
          >
            ⚙️ Manage
          </button>
        </div>
      ) : (
        /* No Wallets - FIXED: Solid Blue Button */
        <button
          onClick={() => setShowAddModal(true)}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          Connect Wallet
        </button>
      )}

      {/* Add Wallet Modal */}
      {showAddModal && (
        <div
          className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex justify-center items-start pt-4 px-4"
          onClick={() => {
            setShowAddModal(false);
            setAddWalletAddress("");
            setAddWalletName("");
            clearWalletError();
          }}
        >
          <div
            className={`w-full max-w-md rounded-xl p-6 shadow-2xl ${
              theme === "dark" ? "bg-slate-800 border border-slate-700" : "bg-white"
            }`}
            onClick={(e) => e.stopPropagation()}
            style={{ maxHeight: "90vh", overflowY: "auto" }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className={`text-xl font-bold ${
                theme === "dark" ? "text-white" : "text-slate-900"
              }`}>
                Add Wallet
              </h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  clearWalletError();
                }}
                className={`p-1 rounded-lg transition-colors ${
                  theme === "dark" ? "hover:bg-slate-700 text-slate-400" : "hover:bg-slate-100 text-slate-600"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {walletError && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2">
                <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-red-400 text-sm">{walletError}</p>
              </div>
            )}

            <div className="space-y-3 mb-6">
              <p className={`text-sm font-medium ${theme === "dark" ? "text-slate-300" : "text-slate-700"}`}>
                Connect via Wallet Extension
              </p>

              <div className="grid grid-cols-2 gap-3">
                {availableWallets && availableWallets.length > 0 ? (
                  availableWallets.map((wallet: any) => {
                    const walletType = getWalletType(wallet.name);
                    const config = getWalletConfig(walletType);
                    
                    return (
                      <button
                        key={wallet.name}
                        onClick={() => handleConnectWallet(wallet.name)}
                        disabled={isWalletConnecting || !wallet.readyState}
                        className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                          isWalletConnecting || !wallet.readyState
                            ? "opacity-50 cursor-not-allowed"
                            : theme === "dark"
                            ? "border-slate-700 hover:border-blue-500 hover:bg-slate-700"
                            : "border-slate-200 hover:border-blue-300 hover:bg-slate-50"
                        }`}
                        title={!wallet.readyState ? `${wallet.name} not installed` : `Connect ${wallet.name}`}
                      >
                        <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${config.color} flex items-center justify-center text-white text-2xl font-bold`}>
                          {config.icon}
                        </div>
                        <span className={`text-sm font-medium ${theme === "dark" ? "text-slate-200" : "text-slate-900"}`}>
                          {wallet.name}
                        </span>
                        {!wallet.readyState && (
                          <span className="text-xs text-red-400">Not Installed</span>
                        )}
                      </button>
                    );
                  })
                ) : (
                  <div className="col-span-2 text-center py-4">
                    <p className={`text-sm ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}>
                      No wallet extensions detected. Please install a wallet first.
                    </p>
                  </div>
                )}
              </div>

              {isWalletConnecting && (
                <div className="flex items-center justify-center gap-2 py-2">
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <span className={`text-sm ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}>
                    Connecting wallet...
                  </span>
                </div>
              )}
            </div>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className={`w-full border-t ${theme === "dark" ? "border-slate-700" : "border-slate-300"}`} />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className={`px-2 ${theme === "dark" ? "bg-slate-800 text-slate-500" : "bg-white text-slate-500"}`}>
                  or enter address manually
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-slate-300" : "text-slate-700"}`}>
                  Wallet Name
                </label>
                <input
                  type="text"
                  placeholder="e.g., Main Wallet, Trading Wallet"
                  value={addWalletName}
                  onChange={(e) => setAddWalletName(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter" && addWalletAddress.trim()) {
                      handleAddWallet();
                    }
                  }}
                  className={`w-full px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    theme === "dark"
                      ? "bg-slate-700 border-slate-600 text-slate-300"
                      : "bg-white border-slate-300 text-slate-900"
                  }`}
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-slate-300" : "text-slate-700"}`}>
                  Wallet Address
                </label>
                <input
                  type="text"
                  placeholder="0x..."
                  value={addWalletAddress}
                  onChange={(e) => setAddWalletAddress(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter" && addWalletAddress.trim()) {
                      handleAddWallet();
                    }
                  }}
                  className={`w-full px-4 py-2 rounded-lg font-mono text-sm border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    theme === "dark"
                      ? "bg-slate-700 border-slate-600 text-slate-300"
                      : "bg-white border-slate-300 text-slate-900"
                  }`}
                />
                <p className={`mt-1 text-xs ${theme === "dark" ? "text-slate-500" : "text-slate-400"}`}>
                  Enter an Aptos wallet address starting with 0x
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setAddWalletAddress("");
                  setAddWalletName("");
                  clearWalletError();
                }}
                disabled={isAdding || isWalletConnecting}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                  theme === "dark"
                    ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                    : "bg-slate-200 text-slate-700 hover:bg-slate-300"
                } disabled:opacity-50`}
              >
                Cancel
              </button>
              {/* FIXED: Solid Blue Button (No Gradient) */}
              <button
                onClick={handleAddWallet}
                disabled={!addWalletAddress.trim() || isAdding || isWalletConnecting}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAdding ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Adding...
                  </span>
                ) : (
                  "Add Manually"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      <ManageWalletsModal isOpen={showManageModal} onClose={() => setShowManageModal(false)} />
    </div>
  );
};

export default WalletBar;