// src/components/ManageWalletsModal.tsx - UPDATED: Toast Notifications
import React, { useState } from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress } from "../utils";
import { X, Edit2, Save, Trash2, Star, Check, Loader2 } from "lucide-react";
import type { ExtendedWalletInfo } from "../context/AppContext";
import toast from "react-hot-toast";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const SOURCE_LABELS: Record<'petra' | 'phantom' | 'manual', { label: string; icon: string; color: string }> = {
  petra: { label: "Petra", icon: "🔴", color: "from-red-500 to-orange-500" },
  phantom: { label: "Phantom", icon: "👻", color: "from-purple-500 to-indigo-500" },
  manual: { label: "Manual", icon: "📝", color: "from-gray-500 to-gray-600" },
};

const CHAIN_CONFIG = {
  aptos: { name: "APTOS", emoji: "⬢", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  solana: { name: "SOLANA", emoji: "◎", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
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
  const [deletingWallet, setDeletingWallet] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleStartEdit = (address: string, currentLabel: string) => {
    setEditingWallet(address);
    setEditName(currentLabel);
  };

  const handleSaveEdit = async (address: string) => {
    if (!editName.trim()) {
      toast.error("Wallet name cannot be empty");
      return;
    }

    setIsUpdating(true);
    const toastId = toast.loading("Updating wallet name...");
    
    try {
      await updateWalletName(address, editName.trim());
      toast.success("Wallet name updated!", { id: toastId });
      setEditingWallet(null);
    } catch (error: any) {
      console.error("Failed to update wallet name:", error);
      toast.error(error?.message || "Failed to update wallet name", { id: toastId });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRemove = async (wallet: ExtendedWalletInfo) => {
    const isConnected = wallet.type === 'petra' || wallet.type === 'phantom';
    
    // Confirmation
    const confirmMessage = wallets.length === 1
      ? "This is your last wallet. Are you sure you want to remove it?"
      : isConnected
        ? `Disconnect and remove "${wallet.label}"?`
        : `Remove "${wallet.label}"?`;
    
    // Use a custom toast for confirmation
    toast((t) => (
      <div className="flex flex-col gap-3">
        <p className="font-medium">{confirmMessage}</p>
        <div className="flex gap-2">
          <button
            onClick={() => {
              toast.dismiss(t.id);
              performRemove(wallet, isConnected);
            }}
            className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600"
          >
            {isConnected ? "Disconnect" : "Remove"}
          </button>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    ), {
      duration: 10000,
      position: 'top-center',
    });
  };

  const performRemove = async (wallet: ExtendedWalletInfo, isConnected: boolean) => {
    setDeletingWallet(wallet.address);
    const toastId = toast.loading(isConnected ? "Disconnecting wallet..." : "Removing wallet...");
    
    try {
      if (isConnected) {
        await disconnectConnectedWallet(wallet.address);
        toast.success("Wallet disconnected!", { id: toastId });
      } else {
        await removeWallet(wallet.address);
        toast.success("Wallet removed!", { id: toastId });
      }
    } catch (error: any) {
      console.error("Failed to remove wallet:", error);
      toast.error(error?.message || "Failed to remove wallet", { id: toastId });
    } finally {
      setDeletingWallet(null);
    }
  };

  const handleSetPrimary = async (address: string, label: string) => {
    const toastId = toast.loading("Setting as primary wallet...");
    
    try {
      await setPrimaryWallet(address);
      toast.success(`${label} is now your primary wallet`, { id: toastId });
    } catch (error: any) {
      console.error("Failed to set primary wallet:", error);
      toast.error(error?.message || "Failed to set primary wallet", { id: toastId });
    }
  };

  const getSourceInfo = (type: ExtendedWalletInfo['type']) => {
    return SOURCE_LABELS[type] || { label: "Manual", icon: "📝", color: "from-gray-500 to-gray-600" };
  };

  const getChainBadge = (chain: 'aptos' | 'solana') => {
    const config = CHAIN_CONFIG[chain];
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${
        theme === "dark" 
          ? config.color
          : chain === 'aptos'
            ? "bg-blue-50 text-blue-600 border-blue-200"
            : "bg-purple-50 text-purple-600 border-purple-200"
      }`}>
        <span>{config.emoji}</span>
        {config.name}
      </span>
    );
  };

  const aptosCount = wallets.filter(w => w.chain === 'aptos').length;
  const solanaCount = wallets.filter(w => w.chain === 'solana').length;

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center items-start pt-4 px-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className={`w-full max-w-3xl max-h-[90vh] rounded-2xl overflow-hidden shadow-2xl ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-6 border-b ${
          theme === "dark" ? "border-zinc-800" : "border-gray-200"
        }`}>
          <div>
            <h3 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Manage Wallets
            </h3>
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
              {wallets.length} wallet{wallets.length !== 1 ? "s" : ""} connected
              {(aptosCount > 0 && solanaCount > 0) && (
                <span className="ml-2">
                  ({aptosCount} Aptos, {solanaCount} Solana)
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors ${
              theme === "dark" ? "hover:bg-zinc-800 text-zinc-400" : "hover:bg-gray-100 text-gray-600"
            }`}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Scrollable content */}
        <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 140px)' }}>
          {wallets.length === 0 ? (
            <div className="text-center py-12">
              <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
                No wallets connected yet
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {wallets.map((wallet) => {
                const sourceInfo = getSourceInfo(wallet.type);
                const isConnectedWallet = wallet.type === 'petra' || wallet.type === 'phantom';
                const isActive = activeWallet?.address === wallet.address && activeWallet?.chain === wallet.chain;
                const isDeleting = deletingWallet === wallet.address;

                return (
                  <div
                    key={`${wallet.chain}-${wallet.address}`}
                    className={`p-4 rounded-xl border transition-all ${
                      isActive
                        ? theme === "dark"
                          ? "border-blue-500/50 bg-blue-500/5"
                          : "border-blue-300 bg-blue-50"
                        : theme === "dark"
                        ? "border-zinc-800 bg-zinc-900/50"
                        : "border-gray-200 bg-gray-50"
                    } ${isDeleting ? "opacity-50" : ""}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${sourceInfo.color} flex items-center justify-center text-lg`}>
                            {sourceInfo.icon}
                          </div>
                          <div className="flex-1">
                            {editingWallet === wallet.address ? (
                              <input
                                type="text"
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                onKeyPress={(e) => e.key === "Enter" && handleSaveEdit(wallet.address)}
                                className={`w-full px-3 py-1 rounded-lg border font-semibold ${
                                  theme === "dark"
                                    ? "bg-zinc-800 border-zinc-700 text-white"
                                    : "bg-white border-gray-300 text-gray-900"
                                }`}
                                autoFocus
                              />
                            ) : (
                              <div className="flex items-center gap-2 flex-wrap">
                                <h4 className={`text-lg font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                                  {wallet.label}
                                </h4>
                                {getChainBadge(wallet.chain)}
                                {wallet.is_primary && (
                                  <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full font-medium ${
                                    theme === "dark"
                                      ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                                      : "bg-yellow-100 text-yellow-700 border border-yellow-300"
                                  }`}>
                                    <Star className="w-3 h-3 fill-current" />
                                    Primary
                                  </span>
                                )}
                                {isActive && (
                                  <span className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full font-medium ${
                                    theme === "dark"
                                      ? "bg-green-500/10 text-green-400 border border-green-500/20"
                                      : "bg-green-100 text-green-700 border border-green-300"
                                  }`}>
                                    <Check className="w-3 h-3" />
                                    Active
                                  </span>
                                )}
                              </div>
                            )}

                            <span className={`text-xs px-2 py-0.5 rounded-full inline-block mt-1 ${
                              isConnectedWallet
                                ? theme === "dark"
                                  ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                  : "bg-blue-50 text-blue-600 border border-blue-200"
                                : theme === "dark"
                                ? "bg-zinc-800 text-zinc-400"
                                : "bg-gray-200 text-gray-600"
                            }`}>
                              {isConnectedWallet ? `Connected via ${sourceInfo.label}` : "Manual Entry"}
                            </span>
                          </div>
                        </div>

                        <p className={`text-sm font-mono mt-2 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                          {wallet.address}
                        </p>

                        {wallet.created_at && (
                          <p className={`text-xs mt-2 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
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
                              className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center gap-1"
                            >
                              {isUpdating ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Save className="w-4 h-4" />
                              )}
                              Save
                            </button>
                            <button
                              onClick={() => setEditingWallet(null)}
                              disabled={isUpdating}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                                theme === "dark"
                                  ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
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
                                onClick={() => handleSetPrimary(wallet.address, wallet.label)}
                                disabled={isDeleting}
                                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                                  theme === "dark"
                                    ? "bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20 border border-yellow-500/20"
                                    : "bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-300"
                                } disabled:opacity-50`}
                              >
                                <Star className="w-4 h-4" />
                                Set Primary
                              </button>
                            )}
                            <button
                              onClick={() => handleStartEdit(wallet.address, wallet.label)}
                              disabled={isDeleting}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                                theme === "dark"
                                  ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                              } disabled:opacity-50`}
                            >
                              <Edit2 className="w-4 h-4" />
                              Rename
                            </button>
                            <button
                              onClick={() => handleRemove(wallet)}
                              disabled={isDeleting}
                              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                                theme === "dark"
                                  ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20"
                                  : "bg-red-50 text-red-600 hover:bg-red-100 border border-red-200"
                              } disabled:opacity-50`}
                            >
                              {isDeleting ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Trash2 className="w-4 h-4" />
                              )}
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
          )}
        </div>

        {/* Footer */}
        <div className={`flex items-center justify-end p-6 border-t ${
          theme === "dark" ? "border-zinc-800" : "border-gray-200"
        }`}>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManageWalletsModal;