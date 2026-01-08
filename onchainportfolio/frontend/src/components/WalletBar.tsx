// src/components/WalletBar.tsx - ENHANCED: Actual Wallet Icons + Toast Notifications
import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import { useSolanaWallet } from "../context/SolanaWalletProvider";
import { shortenAddress } from "../utils";
import { Wallet, ChevronDown, Plus, X, AlertCircle, Settings, ExternalLink, Check, Loader2 } from "lucide-react";
import ManageWalletsModal from "./ManageWalletsModal";
import toast from "react-hot-toast";

// ✅ Wallet configurations with actual logos/icons
const WALLET_CONFIG: Record<string, { 
  icon: string; 
  logo?: string;
  color: string; 
  displayName: string;
  downloadUrl: string;
}> = {
  petra: { 
    icon: "🔴", 
    logo: "https://raw.githubusercontent.com/AptosLabs/wallet-adapter/main/packages/wallet-adapter-react/public/petra.png",
    color: "from-red-500 to-orange-500", 
    displayName: "Petra",
    downloadUrl: "https://petra.app/"
  },
  phantom: { 
    icon: "👻", 
    logo: "https://phantom.app/img/phantom-logo.svg",
    color: "from-purple-500 to-indigo-500", 
    displayName: "Phantom",
    downloadUrl: "https://phantom.app/"
  },
  martian: { 
    icon: "🟢", 
    logo: "https://raw.githubusercontent.com/AptosLabs/wallet-adapter/main/packages/wallet-adapter-react/public/martian.png",
    color: "from-green-500 to-emerald-500", 
    displayName: "Martian",
    downloadUrl: "https://martianwallet.xyz/"
  },
  pontem: { 
    icon: "🟣", 
    color: "from-purple-500 to-pink-500", 
    displayName: "Pontem",
    downloadUrl: "https://pontem.network/"
  },
  manual: { 
    icon: "📝", 
    color: "from-gray-500 to-gray-600", 
    displayName: "Manual",
    downloadUrl: ""
  },
  other: { 
    icon: "💼", 
    color: "from-gray-500 to-gray-600", 
    displayName: "Other",
    downloadUrl: ""
  },
};

const CHAIN_CONFIG = {
  aptos: { name: "APTOS", emoji: "⬢", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  solana: { name: "SOLANA", emoji: "◎", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
};

const WalletBar: React.FC = () => {
  const {
    theme,
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

  const { 
    connected: phantomConnected, 
    publicKey: phantomPublicKey,
    connecting: phantomConnecting 
  } = useSolanaWallet();

  const [showDropdown, setShowDropdown] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [selectedChain, setSelectedChain] = useState<'aptos' | 'solana'>('aptos');
  const [addWalletAddress, setAddWalletAddress] = useState("");
  const [addWalletName, setAddWalletName] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  
  // Track detected wallets
  const [detectedWallets, setDetectedWallets] = useState<{
    petra: boolean;
    phantom: boolean;
    martian: boolean;
  }>({
    petra: false,
    phantom: false,
    martian: false,
  });

  // ✅ Auto-detect wallet extensions on mount
  useEffect(() => {
    const detectWallets = () => {
      const detected = {
        petra: !!(window as any).petra || !!(window as any).aptos,
        phantom: !!(window as any).phantom?.solana?.isPhantom,
        martian: !!(window as any).martian,
      };
      
      setDetectedWallets(detected);
      
      console.log("[WalletBar] Detected wallet extensions:", detected);
    };

    // Initial detection
    detectWallets();
    
    // Re-detect after a short delay (some wallets inject late)
    const timer = setTimeout(detectWallets, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  // ✅ Show error toast when wallet error occurs
  useEffect(() => {
    if (walletError) {
      toast.error(walletError, {
        duration: 4000,
        position: 'top-center',
      });
    }
  }, [walletError]);

  const getChainConfig = (chain?: 'aptos' | 'solana') => {
    return CHAIN_CONFIG[chain || 'aptos'];
  };

  const getWalletConfig = (source: string) => {
    return WALLET_CONFIG[source] || WALLET_CONFIG.other;
  };

  const handleAddWallet = async () => {
    if (!addWalletAddress.trim()) {
      toast.error("Please enter a wallet address");
      return;
    }

    setIsAdding(true);
    
    const toastId = toast.loading("Adding wallet...");
    
    try {
      await addWallet(
        addWalletAddress.trim(),
        addWalletName.trim() || `${selectedChain === 'aptos' ? 'Aptos' : 'Solana'} Wallet`,
        wallets.length === 0,
        'manual',
        selectedChain
      );

      toast.success("Wallet added successfully!", { id: toastId });
      
      setShowAddModal(false);
      setAddWalletAddress("");
      setAddWalletName("");
    } catch (error: any) {
      console.error("[WalletBar] Failed to add wallet:", error);
      toast.error(error?.message || "Failed to add wallet", { id: toastId });
    } finally {
      setIsAdding(false);
    }
  };

  // ✅ Connect Aptos wallet (Petra, Martian, etc.)
  const handleConnectAptosWallet = async (walletName: string) => {
    clearWalletError();
    
    const toastId = toast.loading(`Connecting to ${walletName}...`);
    
    try {
      await connectWallet(walletName, 'aptos');
      toast.success(`${walletName} connected successfully!`, { id: toastId });
      setShowAddModal(false);
    } catch (error: any) {
      console.error("[WalletBar] Aptos connection failed:", error);
      
      if (error?.message?.includes('rejected') || error?.code === 4001) {
        toast.error("Connection rejected. Please approve in your wallet.", { id: toastId });
      } else {
        toast.error(error?.message || "Failed to connect wallet", { id: toastId });
      }
    }
  };

  // ✅ Connect Phantom wallet
  const handleConnectPhantom = async () => {
    clearWalletError();
    
    if (!detectedWallets.phantom) {
      toast.error("Phantom wallet not detected. Redirecting to download...");
      window.open('https://phantom.app/', '_blank');
      return;
    }

    const toastId = toast.loading("Connecting to Phantom...");
    
    try {
      await connectWallet('Phantom', 'solana');
      toast.success("Phantom connected successfully!", { id: toastId });
      setShowAddModal(false);
    } catch (error: any) {
      console.error("[WalletBar] Phantom connection failed:", error);
      
      if (error?.message?.includes('rejected') || error?.code === 4001) {
        toast.error("Connection rejected. Please approve in Phantom.", { id: toastId });
      } else {
        toast.error(error?.message || "Failed to connect Phantom", { id: toastId });
      }
    }
  };

  const handleSelectWallet = (wallet: typeof activeWallet) => {
    setActiveWallet(wallet);
    setShowDropdown(false);
    toast.success(`Switched to ${wallet?.label}`);
  };

  // ✅ Render wallet icon with actual logo
  const renderWalletIcon = (walletType: string, size: "sm" | "md" | "lg" = "md") => {
    const config = getWalletConfig(walletType);
    const sizeClasses = {
      sm: "w-6 h-6",
      md: "w-10 h-10",
      lg: "w-12 h-12",
    };
    
    if (config.logo) {
      return (
        <div className={`${sizeClasses[size]} rounded-full overflow-hidden bg-gradient-to-br ${config.color} flex items-center justify-center`}>
          <img 
            src={config.logo} 
            alt={config.displayName}
            className="w-3/4 h-3/4 object-contain"
            onError={(e) => {
              // Fallback to emoji if image fails
              e.currentTarget.style.display = 'none';
              e.currentTarget.parentElement!.innerHTML = `<span class="text-lg">${config.icon}</span>`;
            }}
          />
        </div>
      );
    }
    
    return (
      <div className={`${sizeClasses[size]} rounded-full bg-gradient-to-br ${config.color} flex items-center justify-center`}>
        <span className={size === "lg" ? "text-2xl" : size === "md" ? "text-lg" : "text-sm"}>
          {config.icon}
        </span>
      </div>
    );
  };

  // ✅ Render available Aptos wallets with detection status
  const renderAptosWallets = () => {
    // Combine adapter wallets with detected wallets
    const walletList = availableWallets && availableWallets.length > 0 
      ? availableWallets 
      : [];
    
    // Always show Petra if detected (even if not in adapter list)
    const showPetra = detectedWallets.petra || walletList.some(w => 
      w.name.toLowerCase().includes('petra')
    );
    
    const showMartian = detectedWallets.martian || walletList.some(w => 
      w.name.toLowerCase().includes('martian')
    );

    if (!showPetra && !showMartian && walletList.length === 0) {
      return (
        <div className={`text-center py-6 px-4 rounded-lg ${
          theme === "dark" ? "bg-zinc-800/50" : "bg-gray-50"
        }`}>
          <p className={`text-sm mb-3 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            No Aptos wallet extensions detected
          </p>
          <div className="flex gap-2 justify-center">
            <a
              href="https://petra.app/"
              target="_blank"
              rel="noopener noreferrer"
              className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                theme === "dark"
                  ? "bg-zinc-700 text-zinc-200 hover:bg-zinc-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Install Petra
              <ExternalLink className="w-3 h-3" />
            </a>
            <a
              href="https://martianwallet.xyz/"
              target="_blank"
              rel="noopener noreferrer"
              className={`px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                theme === "dark"
                  ? "bg-zinc-700 text-zinc-200 hover:bg-zinc-600"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
            >
              Install Martian
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 gap-3">
        {/* Petra Wallet */}
        {showPetra && (
          <button
            onClick={() => handleConnectAptosWallet('Petra')}
            disabled={isWalletConnecting}
            className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
              isWalletConnecting
                ? "opacity-50 cursor-not-allowed"
                : theme === "dark"
                ? "border-zinc-700 hover:border-red-500 hover:bg-zinc-800"
                : "border-gray-200 hover:border-red-400 hover:bg-red-50"
            }`}
          >
            {/* Petra Logo */}
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center overflow-hidden">
              <img 
                src="https://petra.app/favicon.ico"
                alt="Petra"
                className="w-8 h-8"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
              <span className="text-2xl" style={{ display: 'none' }}>🔴</span>
            </div>
            <span className={`text-sm font-semibold ${theme === "dark" ? "text-zinc-200" : "text-gray-900"}`}>
              Petra
            </span>
            {detectedWallets.petra ? (
              <span className="text-xs text-green-500 flex items-center gap-1">
                <Check className="w-3 h-3" /> Detected
              </span>
            ) : (
              <span className="text-xs text-yellow-500">Not Installed</span>
            )}
          </button>
        )}

        {/* Martian Wallet */}
        {showMartian && (
          <button
            onClick={() => handleConnectAptosWallet('Martian')}
            disabled={isWalletConnecting}
            className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
              isWalletConnecting
                ? "opacity-50 cursor-not-allowed"
                : theme === "dark"
                ? "border-zinc-700 hover:border-green-500 hover:bg-zinc-800"
                : "border-gray-200 hover:border-green-400 hover:bg-green-50"
            }`}
          >
            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center">
              <span className="text-2xl">🟢</span>
            </div>
            <span className={`text-sm font-semibold ${theme === "dark" ? "text-zinc-200" : "text-gray-900"}`}>
              Martian
            </span>
            {detectedWallets.martian ? (
              <span className="text-xs text-green-500 flex items-center gap-1">
                <Check className="w-3 h-3" /> Detected
              </span>
            ) : (
              <span className="text-xs text-yellow-500">Not Installed</span>
            )}
          </button>
        )}

        {/* Other wallets from adapter */}
        {walletList
          .filter(w => !w.name.toLowerCase().includes('petra') && !w.name.toLowerCase().includes('martian'))
          .map((wallet: any) => (
            <button
              key={wallet.name}
              onClick={() => handleConnectAptosWallet(wallet.name)}
              disabled={isWalletConnecting || !wallet.readyState}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                isWalletConnecting || !wallet.readyState
                  ? "opacity-50 cursor-not-allowed"
                  : theme === "dark"
                  ? "border-zinc-700 hover:border-blue-500 hover:bg-zinc-800"
                  : "border-gray-200 hover:border-blue-300 hover:bg-blue-50"
              }`}
            >
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center overflow-hidden">
                {wallet.icon ? (
                  <img src={wallet.icon} alt={wallet.name} className="w-8 h-8" />
                ) : (
                  <span className="text-2xl">💼</span>
                )}
              </div>
              <span className={`text-sm font-semibold ${theme === "dark" ? "text-zinc-200" : "text-gray-900"}`}>
                {wallet.name}
              </span>
              {wallet.readyState ? (
                <span className="text-xs text-green-500 flex items-center gap-1">
                  <Check className="w-3 h-3" /> Ready
                </span>
              ) : (
                <span className="text-xs text-yellow-500">Not Ready</span>
              )}
            </button>
          ))}
      </div>
    );
  };

  return (
    <>
      {/* Wallet Section */}
      {activeWallet ? (
        <div className="relative">
          {/* Wallet Selector Button */}
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
              theme === "dark"
                ? "bg-zinc-900 border-zinc-800 hover:bg-zinc-800"
                : "bg-white border-gray-200 hover:bg-gray-50"
            }`}
          >
            {renderWalletIcon(activeWallet.type, "sm")}
            
            <span className={`text-sm font-medium ${
              theme === "dark" ? "text-zinc-200" : "text-gray-700"
            }`}>
              {activeWallet.label}
            </span>
            
            <span className={`text-[10px] px-1.5 py-0.5 rounded border ${
              theme === "dark" 
                ? getChainConfig(activeWallet.chain).color
                : (activeWallet.chain || 'aptos') === 'aptos' 
                  ? "bg-blue-50 text-blue-600 border-blue-200"
                  : "bg-purple-50 text-purple-600 border-purple-200"
            }`}>
              {getChainConfig(activeWallet.chain).name}
            </span>
            
            <ChevronDown className={`w-4 h-4 transition-transform ${
              showDropdown ? "rotate-180" : ""
            } ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
          </button>

          {/* Dropdown Menu */}
          {showDropdown && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)} />
              <div className={`absolute right-0 mt-2 w-80 rounded-xl border shadow-xl z-20 ${
                theme === "dark" ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200"
              }`}>
                <div className="p-2">
                  {/* Header */}
                  <div className={`px-3 py-2 text-xs font-medium ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-500"
                  }`}>
                    {wallets.length} {wallets.length === 1 ? 'Wallet' : 'Wallets'}
                  </div>

                  {/* Wallet List */}
                  {wallets.map((wallet) => {
                    const walletChain = wallet.chain || 'aptos';
                    const isActive = activeWallet?.address === wallet.address && 
                                    (activeWallet?.chain || 'aptos') === walletChain;
                    
                    return (
                      <button
                        key={`${walletChain}-${wallet.address}`}
                        onClick={() => handleSelectWallet(wallet)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                          isActive
                            ? "bg-blue-600 text-white"
                            : theme === "dark"
                            ? "hover:bg-zinc-800 text-zinc-200"
                            : "hover:bg-gray-50 text-gray-900"
                        }`}
                      >
                        {renderWalletIcon(wallet.type, "sm")}
                        <div className="flex-1 flex flex-col items-start min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium truncate">
                              {wallet.label}
                            </span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded border flex-shrink-0 ${
                              isActive
                                ? "bg-white/20 text-white border-white/30"
                                : theme === "dark"
                                ? getChainConfig(wallet.chain).color
                                : walletChain === 'aptos'
                                  ? "bg-blue-50 text-blue-600 border-blue-200"
                                  : "bg-purple-50 text-purple-600 border-purple-200"
                            }`}>
                              {getChainConfig(wallet.chain).name}
                            </span>
                          </div>
                          <span className={`text-xs font-mono truncate max-w-full ${
                            isActive
                              ? "text-white/80"
                              : theme === "dark"
                              ? "text-zinc-400"
                              : "text-gray-500"
                          }`}>
                            {shortenAddress(wallet.address)}
                          </span>
                        </div>
                        {isActive && <Check className="w-4 h-4" />}
                      </button>
                    );
                  })}

                  {/* Divider */}
                  <div className={`my-2 border-t ${
                    theme === "dark" ? "border-zinc-800" : "border-gray-200"
                  }`} />

                  {/* Action Buttons */}
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => {
                        setShowDropdown(false);
                        setShowAddModal(true);
                      }}
                      className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                        theme === "dark"
                          ? "hover:bg-zinc-800 text-blue-400 border border-zinc-800"
                          : "hover:bg-blue-50 text-blue-600 border border-blue-200"
                      }`}
                    >
                      <Plus className="w-4 h-4" />
                      <span className="text-sm font-medium">Add</span>
                    </button>

                    <button
                      onClick={() => {
                        setShowDropdown(false);
                        setShowManageModal(true);
                      }}
                      className={`flex items-center justify-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                        theme === "dark"
                          ? "hover:bg-zinc-800 text-zinc-400 border border-zinc-800"
                          : "hover:bg-gray-100 text-gray-600 border border-gray-200"
                      }`}
                    >
                      <Settings className="w-4 h-4" />
                      <span className="text-sm font-medium">Manage</span>
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      ) : (
        /* No Wallets - Connect Button */
        <button
          onClick={() => setShowAddModal(true)}
          className="px-5 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Wallet className="w-5 h-5" />
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
              theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white"
            }`}
            onClick={(e) => e.stopPropagation()}
            style={{ maxHeight: "90vh", overflowY: "auto" }}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-xl font-bold ${
                theme === "dark" ? "text-white" : "text-gray-900"
              }`}>
                Connect Wallet
              </h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  clearWalletError();
                }}
                className={`p-1 rounded-lg transition-colors ${
                  theme === "dark" ? "hover:bg-zinc-800 text-zinc-400" : "hover:bg-gray-100 text-gray-600"
                }`}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chain Selection */}
            <div className="mb-6">
              <label className={`block text-sm font-medium mb-3 ${
                theme === "dark" ? "text-zinc-300" : "text-gray-700"
              }`}>
                Select Blockchain
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => setSelectedChain('aptos')}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    selectedChain === 'aptos'
                      ? "border-blue-500 bg-blue-500/10"
                      : theme === "dark"
                      ? "border-zinc-700 hover:border-zinc-600"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="text-3xl mb-2">⬢</div>
                  <div className={`text-sm font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}>
                    Aptos
                  </div>
                  <div className={`text-xs mt-1 ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-500"
                  }`}>
                    Petra, Martian
                  </div>
                </button>
                <button
                  onClick={() => setSelectedChain('solana')}
                  className={`p-4 rounded-xl border-2 transition-all ${
                    selectedChain === 'solana'
                      ? "border-purple-500 bg-purple-500/10"
                      : theme === "dark"
                      ? "border-zinc-700 hover:border-zinc-600"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="text-3xl mb-2">◎</div>
                  <div className={`text-sm font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}>
                    Solana
                  </div>
                  <div className={`text-xs mt-1 ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-500"
                  }`}>
                    Phantom
                  </div>
                </button>
              </div>
            </div>

            {/* Wallet Extension Connection */}
            <div className="mb-6">
              <p className={`text-sm font-medium mb-3 ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                Connect via Wallet Extension
              </p>

              {selectedChain === 'aptos' ? (
                renderAptosWallets()
              ) : (
                /* Phantom Wallet Button */
                <button
                  onClick={handleConnectPhantom}
                  disabled={isWalletConnecting || phantomConnecting}
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                    isWalletConnecting || phantomConnecting
                      ? "opacity-50 cursor-not-allowed"
                      : theme === "dark"
                      ? "border-zinc-700 hover:border-purple-500 hover:bg-zinc-800"
                      : "border-gray-200 hover:border-purple-400 hover:bg-purple-50"
                  }`}
                >
                  {/* Phantom Logo */}
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center overflow-hidden">
                    <img 
                      src="https://phantom.app/favicon.ico"
                      alt="Phantom"
                      className="w-8 h-8"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                    <span className="text-2xl" style={{ display: 'block' }}>👻</span>
                  </div>
                  
                  <div className="flex-1 text-left">
                    <div className={`font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                      Phantom
                    </div>
                    {detectedWallets.phantom ? (
                      phantomConnected ? (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Connected
                        </span>
                      ) : (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Detected - Click to connect
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-yellow-500 flex items-center gap-1">
                        <ExternalLink className="w-3 h-3" /> Not installed - Click to download
                      </span>
                    )}
                  </div>

                  {(isWalletConnecting || phantomConnecting) && (
                    <Loader2 className="w-5 h-5 animate-spin text-purple-500" />
                  )}
                </button>
              )}

              {/* Loading State */}
              {isWalletConnecting && (
                <div className="flex items-center justify-center gap-2 py-3 mt-3">
                  <Loader2 className={`w-5 h-5 animate-spin ${
                    theme === "dark" ? "text-white" : "text-black"
                  }`} />
                  <span className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Connecting wallet...
                  </span>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className={`w-full border-t ${theme === "dark" ? "border-zinc-700" : "border-gray-300"}`} />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className={`px-2 ${theme === "dark" ? "bg-zinc-900 text-zinc-500" : "bg-white text-gray-500"}`}>
                  or enter address manually
                </span>
              </div>
            </div>

            {/* Manual Entry */}
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                  Wallet Name (optional)
                </label>
                <input
                  type="text"
                  placeholder={`e.g., My ${selectedChain === 'aptos' ? 'Aptos' : 'Solana'} Wallet`}
                  value={addWalletName}
                  onChange={(e) => setAddWalletName(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addWalletAddress.trim() && handleAddWallet()}
                  className={`w-full px-4 py-2.5 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    theme === "dark"
                      ? "bg-zinc-800 border-zinc-700 text-zinc-300"
                      : "bg-white border-gray-300 text-gray-900"
                  }`}
                />
              </div>

              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                  Wallet Address
                </label>
                <input
                  type="text"
                  placeholder={selectedChain === 'aptos' ? "0x..." : "Base58 address..."}
                  value={addWalletAddress}
                  onChange={(e) => setAddWalletAddress(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addWalletAddress.trim() && handleAddWallet()}
                  className={`w-full px-4 py-2.5 rounded-lg font-mono text-sm border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    theme === "dark"
                      ? "bg-zinc-800 border-zinc-700 text-zinc-300"
                      : "bg-white border-gray-300 text-gray-900"
                  }`}
                />
                <p className={`mt-1.5 text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                  {selectedChain === 'aptos' 
                    ? "Enter an Aptos wallet address starting with 0x"
                    : "Enter a Solana wallet address (base58 format)"
                  }
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setAddWalletAddress("");
                  setAddWalletName("");
                  clearWalletError();
                }}
                disabled={isAdding || isWalletConnecting}
                className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                  theme === "dark"
                    ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                    : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                } disabled:opacity-50`}
              >
                Cancel
              </button>
              <button
                onClick={handleAddWallet}
                disabled={!addWalletAddress.trim() || isAdding || isWalletConnecting}
                className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isAdding ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
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
    </>
  );
};

export default WalletBar;