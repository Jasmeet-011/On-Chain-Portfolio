// src/components/ManageWalletsModal.tsx - FIXED POSITIONING
import React, { useState } from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress } from "../utils";
import type { ExtendedWalletInfo } from "../context/AppContext";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const SOURCE_LABELS: Record<'petra' | 'manual', { label: string; icon: string; color: string }> = {
  petra: { label: "Petra", icon: "🔴", color: "from-red-500 to-orange-500" },
  manual: { label: "Manual", icon: "📝", color: "from-gray-500 to-gray-600" },
};

const ManageWalletsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const {
    theme,
    wallets,
    activeWallet,
    removeWallet,
    updateWalletName,
    setPrimaryWallet,
    disconnectConnectedWallet,
  } = useAppContext();

  const [editingWallet, setEditingWallet] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);

  if (!isOpen) return null;

  const handleStartEdit = (address: string, currentLabel: string) => {
    setEditingWallet(address);
    setEditName(currentLabel);
  };

  const handleSaveEdit = async (address: string) => {
    if (!editName.trim()) return;

    setIsUpdating(true);
    try {
      await updateWalletName(address, editName.trim());
      setEditingWallet(null);
    } catch (error) {
      console.error("Failed to update wallet name:", error);
      alert("Failed to update wallet name");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRemove = async (wallet: ExtendedWalletInfo) => {
    const isConnected = wallet.type === 'petra';
    
    let confirmMessage;
    if (wallets.length === 1) {
      confirmMessage = "⚠️ This is your last wallet. Removing it will leave you with no wallets. Are you sure?";
    } else if (isConnected) {
      confirmMessage = "This will disconnect and remove this wallet. Continue?";
    } else {
      confirmMessage = "Are you sure you want to remove this wallet?";
    }

    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      if (isConnected) {
        await disconnectConnectedWallet(wallet.address);
      } else {
        await removeWallet(wallet.address);
      }
    } catch (error) {
      console.error("Failed to remove wallet:", error);
      alert("Failed to remove wallet");
    }
  };

  const handleSetPrimary = async (address: string) => {
    try {
      await setPrimaryWallet(address);
    } catch (error) {
      console.error("Failed to set primary wallet:", error);
      alert("Failed to set primary wallet");
    }
  };

  const getSourceInfo = (type: ExtendedWalletInfo['type']) => {
    return SOURCE_LABELS[type] || { label: "Manual", icon: "📝", color: "from-gray-500 to-gray-600" };
  };

  return (
    // ✅ FIXED: Proper modal overlay with centering
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center items-start pt-4 px-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      {/* ✅ FIXED: Modal container with proper constraints */}
      <div
        className={`w-full max-w-3xl max-h-[90vh] rounded-2xl overflow-hidden shadow-2xl ${
          theme === "dark" ? "bg-gray-800" : "bg-white"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className={`flex items-center justify-between p-6 border-b ${
            theme === "dark" ? "border-gray-700" : "border-gray-200"
          }`}
        >
          <div>
            <h3 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Manage Wallets
            </h3>
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              {wallets.length} wallet{wallets.length !== 1 ? "s" : ""} connected
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors ${
              theme === "dark" ? "hover:bg-gray-700 text-gray-400" : "hover:bg-gray-100 text-gray-600"
            }`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* ✅ FIXED: Scrollable content area */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
          <div className="space-y-4">
            {wallets.map((wallet) => {
              const sourceInfo = getSourceInfo(wallet.type);
              const isConnectedWallet = wallet.type === 'petra';

              return (
                <div
                  key={wallet.address}
                  className={`p-4 rounded-xl border transition-all ${
                    activeWallet?.address === wallet.address
                      ? theme === "dark"
                        ? "border-blue-500/50 bg-blue-500/5"
                        : "border-blue-300 bg-blue-50"
                      : theme === "dark"
                      ? "border-gray-700 bg-gray-900/50"
                      : "border-gray-200 bg-gray-50"
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      {/* Wallet Header with Source Icon */}
                      <div className="flex items-center gap-3 mb-2">
                        <div
                          className={`w-10 h-10 rounded-full bg-gradient-to-br ${sourceInfo.color} flex items-center justify-center text-white text-lg`}
                        >
                          {sourceInfo.icon}
                        </div>
                        <div className="flex-1">
                          {editingWallet === wallet.address ? (
                            <input
                              type="text"
                              value={editName}
                              onChange={(e) => setEditName(e.target.value)}
                              onKeyPress={(e) => {
                                if (e.key === "Enter") {
                                  handleSaveEdit(wallet.address);
                                }
                              }}
                              className={`w-full px-3 py-1 rounded-lg border font-semibold ${
                                theme === "dark"
                                  ? "bg-gray-800 border-gray-600 text-white"
                                  : "bg-white border-gray-300 text-gray-900"
                              }`}
                              autoFocus
                            />
                          ) : (
                            <div className="flex items-center gap-2 flex-wrap">
                              <h4 className={`text-lg font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                                {wallet.label}
                              </h4>
                              {wallet.is_primary && (
                                <span
                                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                                    theme === "dark"
                                      ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                      : "bg-yellow-100 text-yellow-700 border border-yellow-300"
                                  }`}
                                >
                                  Primary
                                </span>
                              )}
                              {activeWallet?.address === wallet.address && (
                                <span
                                  className={`text-xs px-2 py-1 rounded-full font-medium ${
                                    theme === "dark"
                                      ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                      : "bg-green-100 text-green-700 border border-green-300"
                                  }`}
                                >
                                  Active
                                </span>
                              )}
                            </div>
                          )}

                          {/* Source Badge */}
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                isConnectedWallet
                                  ? theme === "dark"
                                    ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                    : "bg-blue-50 text-blue-600 border border-blue-200"
                                  : theme === "dark"
                                  ? "bg-gray-700 text-gray-400"
                                  : "bg-gray-200 text-gray-600"
                              }`}
                            >
                              {isConnectedWallet ? `Connected via ${sourceInfo.label}` : "Manual Entry"}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Wallet Address */}
                      <p className={`text-sm font-mono mt-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                        {wallet.address}
                      </p>

                      {/* Public Key (if available) */}
                      {wallet.publicKey && (
                        <p className={`text-xs font-mono mt-1 ${theme === "dark" ? "text-gray-500" : "text-gray-500"}`}>
                          Public Key: {shortenAddress(wallet.publicKey)}
                        </p>
                      )}

                      {/* Added Date */}
                      {wallet.created_at && (
                        <p className={`text-xs mt-2 ${theme === "dark" ? "text-gray-500" : "text-gray-500"}`}>
                          Added {new Date(wallet.created_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col gap-2">
                      {editingWallet === wallet.address ? (
                        <>
                          <button
                            onClick={() => handleSaveEdit(wallet.address)}
                            disabled={isUpdating}
                            className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 disabled:opacity-50"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingWallet(null)}
                            disabled={isUpdating}
                            className={`px-3 py-1 rounded-lg text-sm font-medium ${
                              theme === "dark"
                                ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                            }`}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          {!wallet.is_primary && (
                            <button
                              onClick={() => handleSetPrimary(wallet.address)}
                              className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                                theme === "dark"
                                  ? "bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20 border border-yellow-500/20"
                                  : "bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-300"
                              }`}
                            >
                              Set Primary
                            </button>
                          )}
                          <button
                            onClick={() => handleStartEdit(wallet.address, wallet.label)}
                            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                              theme === "dark"
                                ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                            }`}
                          >
                            Rename
                          </button>
                          <button
                            onClick={() => handleRemove(wallet)}
                            className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                              theme === "dark"
                                ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20"
                                : "bg-red-50 text-red-600 hover:bg-red-100 border border-red-200"
                            }`}
                          >
                            {isConnectedWallet ? "Disconnect" : "Remove"}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div
          className={`flex items-center justify-end p-6 border-t ${
            theme === "dark" ? "border-gray-700" : "border-gray-200"
          }`}
        >
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManageWalletsModal;
