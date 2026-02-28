// src/components/WalletBar.tsx - SIMPLIFIED: 3 Wallets + Manual Add
import React, { useState, useEffect, useRef } from "react";
import { useAppContext } from "../context/AppContext";
import { useSolanaWallet } from "../context/SolanaWalletProvider";
import { useEVMWallet } from "../context/EVMWalletProvider";
import { useWallet as useAptosWallet } from "@aptos-labs/wallet-adapter-react";
import { shortenAddress } from "../utils";
import { Wallet, ChevronDown, Plus, X, Settings, ExternalLink, Check, Loader2 } from "lucide-react";
import ManageWalletsModal from "./ManageWalletsModal";
import toast from "react-hot-toast";
import type { ChainType } from "../api";
import { isENSName, resolveENSName } from "../utils/ens";

// Supported wallets - Simplified to 3 main wallets
const SUPPORTED_WALLETS = {
  petra: {
    name: "Petra",
    icon: "🔴",
    color: "from-red-500 to-orange-500",
    hoverBorder: "hover:border-red-500",
    hoverBg: "hover:bg-red-500/10",
    chain: "aptos" as ChainType,
    downloadUrl: "https://petra.app/",
  },
  phantom: {
    name: "Phantom",
    icon: "👻",
    color: "from-purple-500 to-indigo-500",
    hoverBorder: "hover:border-purple-500",
    hoverBg: "hover:bg-purple-500/10",
    chain: "solana" as ChainType,
    downloadUrl: "https://phantom.app/",
  },
  metamask: {
    name: "MetaMask",
    icon: "🦊",
    color: "from-orange-500 to-amber-500",
    hoverBorder: "hover:border-orange-500",
    hoverBg: "hover:bg-orange-500/10",
    chain: "ethereum" as ChainType,
    downloadUrl: "https://metamask.io/",
  },
};

// Chain configuration for display
const CHAIN_CONFIG: Record<string, { name: string; emoji: string; color: string }> = {
  aptos: { name: "APTOS", emoji: "⬢", color: "bg-blue-500/10 text-blue-400 border-blue-500/20" },
  solana: { name: "SOLANA", emoji: "◎", color: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
  ethereum: { name: "ETHEREUM", emoji: "Ξ", color: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
  polygon: { name: "POLYGON", emoji: "⬡", color: "bg-violet-500/10 text-violet-400 border-violet-500/20" },
  base: { name: "BASE", emoji: "🔵", color: "bg-blue-600/10 text-blue-500 border-blue-600/20" },
  evm: { name: "EVM", emoji: "Ξ", color: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
  ethereum_sepolia: { name: "SEPOLIA", emoji: "Ξ", color: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
  polygon_amoy: { name: "AMOY", emoji: "⬡", color: "bg-violet-500/10 text-violet-400 border-violet-500/20" },
  base_sepolia: { name: "BASE-SEP", emoji: "🔵", color: "bg-blue-600/10 text-blue-500 border-blue-600/20" },
};

const WalletBar: React.FC = () => {
  const {
    theme,
    wallets,
    walletGroups,
    activeWalletGroup,
    setActiveWalletGroup,
    addWallet,
    connectWallet,
    isWalletConnecting,
    walletError,
    clearWalletError,
  } = useAppContext();

  const { connected: phantomConnected, connecting: phantomConnecting } = useSolanaWallet();
  const { connected: evmConnected, connecting: evmConnecting } = useEVMWallet();
  const { connected: aptosConnected } = useAptosWallet();

  // Check if wallets are actually added to our wallet list (not just browser connected)
  const isPhantomAdded = wallets.some(w => w.type === 'phantom');
  const isMetaMaskAdded = wallets.some(w => w.type === 'metamask' || w.type === 'coinbase');
  const isPetraAdded = wallets.some(w => w.type === 'petra');

  const [showDropdown, setShowDropdown] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [addWalletAddress, setAddWalletAddress] = useState("");
  const [addWalletName, setAddWalletName] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  // ENS resolution state
  const [ensResolved, setEnsResolved]     = useState<string | null>(null);
  const [ensResolving, setEnsResolving]   = useState(false);
  const [ensError, setEnsError]           = useState<string | null>(null);
  const ensDebounceRef                    = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Detected wallets state
  const [detectedWallets, setDetectedWallets] = useState({
    petra: false,
    phantom: false,
    metamask: false,
  });

  // Auto-detect wallet extensions
  useEffect(() => {
    const detectWallets = () => {
      const ethereum = (window as any).ethereum;
      setDetectedWallets({
        petra: !!(window as any).petra || !!(window as any).aptos,
        phantom: !!(window as any).phantom?.solana?.isPhantom,
        metamask: !!(ethereum?.isMetaMask),
      });
    };

    detectWallets();
    const timer = setTimeout(detectWallets, 1000);
    return () => clearTimeout(timer);
  }, []);

  // Show error toast
  useEffect(() => {
    if (walletError) {
      toast.error(walletError, { duration: 4000, position: "top-center" });
    }
  }, [walletError]);

  // ENS debounced resolution — triggers whenever the address input changes
  useEffect(() => {
    setEnsResolved(null);
    setEnsError(null);

    if (!isENSName(addWalletAddress)) return;

    if (ensDebounceRef.current) clearTimeout(ensDebounceRef.current);

    ensDebounceRef.current = setTimeout(async () => {
      setEnsResolving(true);
      try {
        const addr = await resolveENSName(addWalletAddress.trim());
        if (addr) {
          setEnsResolved(addr);
          setEnsError(null);
        } else {
          setEnsResolved(null);
          setEnsError("ENS name not found or has no address set");
        }
      } catch {
        setEnsResolved(null);
        setEnsError("Could not resolve ENS name");
      } finally {
        setEnsResolving(false);
      }
    }, 600);

    return () => {
      if (ensDebounceRef.current) clearTimeout(ensDebounceRef.current);
    };
  }, [addWalletAddress]);

  const getChainConfig = (chain?: ChainType) => CHAIN_CONFIG[chain || "aptos"];

  // Auto-detect chain from address format
  const detectChainFromAddress = (address: string): ChainType => {
    const trimmed = address.trim();
    // Solana addresses are base58, typically 32-44 chars, no 0x prefix
    if (!trimmed.startsWith("0x") && /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(trimmed)) {
      return "solana";
    }
    // 0x addresses - could be Aptos (64 hex chars) or EVM (40 hex chars)
    if (trimmed.startsWith("0x")) {
      const hexPart = trimmed.slice(2);
      if (hexPart.length === 64) return "aptos";
      if (hexPart.length === 40) return "ethereum";
    }
    return "aptos"; // default
  };

  // Handle wallet connection
  const handleConnectWallet = async (walletKey: keyof typeof SUPPORTED_WALLETS) => {
    clearWalletError();
    const wallet = SUPPORTED_WALLETS[walletKey];

    if (!detectedWallets[walletKey]) {
      toast.error(`${wallet.name} not detected. Redirecting to download...`);
      window.open(wallet.downloadUrl, "_blank");
      return;
    }

    const toastId = toast.loading(`Connecting to ${wallet.name}...`);

    try {
      await connectWallet(wallet.name, wallet.chain);
      toast.success(`${wallet.name} connected!`, { id: toastId });
      setShowAddModal(false);
    } catch (error: any) {
      if (error?.message?.includes("rejected") || error?.code === 4001) {
        toast.error("Connection rejected. Please approve in your wallet.", { id: toastId });
      } else if (error?.code === -32002) {
        toast.error("Request pending. Check your wallet.", { id: toastId });
      } else {
        toast.error(error?.message || `Failed to connect ${wallet.name}`, { id: toastId });
      }
    }
  };

  // Handle manual wallet add
  const handleAddWallet = async () => {
    const rawInput = addWalletAddress.trim();
    if (!rawInput) {
      toast.error("Please enter a wallet address or ENS name");
      return;
    }

    // If user typed an ENS name, require it to be resolved first
    if (isENSName(rawInput)) {
      if (ensResolving) {
        toast.error("Still resolving ENS name, please wait…");
        return;
      }
      if (!ensResolved) {
        toast.error(ensError || "ENS name could not be resolved");
        return;
      }
    }

    // Use the resolved address if available, otherwise use raw input
    const finalAddress = ensResolved ?? rawInput;
    // Use the ENS name as label if user didn't provide one
    const ensLabel = isENSName(rawInput) ? rawInput.trim().toLowerCase() : null;

    setIsAdding(true);
    const toastId = toast.loading("Adding wallet...");

    try {
      const detectedChain = detectChainFromAddress(finalAddress);
      const chainName = CHAIN_CONFIG[detectedChain].name;

      await addWallet(
        finalAddress,
        addWalletName.trim() || ensLabel || `${chainName} Wallet`,
        wallets.length === 0,
        "manual",
        detectedChain
      );

      const label = ensLabel ? `${ensLabel} (${chainName})` : chainName;
      toast.success(`Wallet added — ${label}!`, { id: toastId });
      setShowAddModal(false);
      setShowManualEntry(false);
      setAddWalletAddress("");
      setAddWalletName("");
      setEnsResolved(null);
      setEnsError(null);
    } catch (error: any) {
      toast.error(error?.message || "Failed to add wallet", { id: toastId });
    } finally {
      setIsAdding(false);
    }
  };

  // Handle wallet group selection (shows all chains for that provider)
  const handleSelectWalletGroup = (group: typeof activeWalletGroup) => {
    if (group) {
      setActiveWalletGroup(group);
      setShowDropdown(false);
      const chainNames = group.chains.map(c => CHAIN_CONFIG[c]?.name || c).join(" + ");
      toast.success(`Switched to ${group.label} (${chainNames})`);
    }
  };

  // Get chain badges for a wallet group
  const getChainBadges = (chains: ChainType[]) => {
    return chains.map(chain => {
      const config = CHAIN_CONFIG[chain] || { name: chain.toUpperCase(), emoji: "•", color: "bg-gray-500/10 text-gray-400" };
      return { chain, ...config };
    });
  };

  // Render wallet icon
  const renderWalletIcon = (walletType: string, size: "sm" | "md" = "md") => {
    const sizeClass = size === "sm" ? "w-6 h-6 text-sm" : "w-10 h-10 text-lg";
    const wallet = Object.values(SUPPORTED_WALLETS).find(
      (w) => w.name.toLowerCase() === walletType?.toLowerCase()
    );
    const icon = wallet?.icon || "💼";
    const color = wallet?.color || "from-gray-500 to-gray-600";

    return (
      <div className={`${sizeClass} rounded-full bg-gradient-to-br ${color} flex items-center justify-center`}>
        <span>{icon}</span>
      </div>
    );
  };

  return (
    <>
      {/* Wallet Section */}
      {activeWalletGroup ? (
        <div className="relative">
          {/* Wallet Group Selector Button */}
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors ${
              theme === "dark"
                ? "bg-zinc-900 border-zinc-800 hover:bg-zinc-800"
                : "bg-white border-gray-200 hover:bg-gray-50"
            }`}
          >
            {renderWalletIcon(activeWalletGroup.type, "sm")}
            <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-200" : "text-gray-700"}`}>
              {activeWalletGroup.label}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded-md ${
              theme === "dark" ? "bg-zinc-800 text-zinc-400" : "bg-gray-100 text-gray-500"
            }`}>
              {activeWalletGroup.wallets.length} {activeWalletGroup.wallets.length === 1 ? "addr" : "addrs"}
            </span>
            <ChevronDown
              className={`w-4 h-4 transition-transform ${showDropdown ? "rotate-180" : ""} ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}
            />
          </button>

          {/* Dropdown Menu - Shows Wallet Groups */}
          {showDropdown && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowDropdown(false)} />
              <div
                className={`absolute right-0 mt-2 w-80 rounded-xl border shadow-xl z-20 ${
                  theme === "dark" ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200"
                }`}
              >
                <div className="p-2">
                  <div className={`px-3 py-2 text-xs font-medium ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                    {walletGroups.length} {walletGroups.length === 1 ? "Wallet" : "Wallets"} ({wallets.length} addresses)
                  </div>

                  {/* Wallet Group List */}
                  {walletGroups.map((group) => {
                    const isActive = activeWalletGroup?.id === group.id;
                    const badges = getChainBadges(group.chains);

                    return (
                      <button
                        key={group.id}
                        onClick={() => handleSelectWalletGroup(group)}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                          isActive
                            ? "bg-blue-600 text-white"
                            : theme === "dark"
                            ? "hover:bg-zinc-800 text-zinc-200"
                            : "hover:bg-gray-50 text-gray-900"
                        }`}
                      >
                        {renderWalletIcon(group.type, "sm")}
                        <div className="flex-1 flex flex-col items-start min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-medium truncate">{group.label}</span>
                            {badges.map(({ chain, name, color }) => (
                              <span
                                key={chain}
                                className={`text-[10px] px-1.5 py-0.5 rounded border shrink-0 ${
                                  isActive
                                    ? "bg-white/20 text-white border-white/30"
                                    : theme === "dark"
                                    ? color
                                    : "bg-blue-50 text-blue-600 border-blue-200"
                                }`}
                              >
                                {name}
                              </span>
                            ))}
                          </div>
                          {/* Show addresses for each chain */}
                          <div className="flex flex-col gap-0.5 mt-0.5">
                            {group.wallets.map((w) => (
                              <span
                                key={w.address}
                                className={`text-xs font-mono truncate max-w-full ${
                                  isActive ? "text-white/70" : theme === "dark" ? "text-zinc-500" : "text-gray-400"
                                }`}
                              >
                                {shortenAddress(w.address)}
                              </span>
                            ))}
                          </div>
                        </div>
                        {isActive && <Check className="w-4 h-4 shrink-0" />}
                      </button>
                    );
                  })}

                  <div className={`my-2 border-t ${theme === "dark" ? "border-zinc-800" : "border-gray-200"}`} />

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

      {/* Add Wallet Modal - SIMPLIFIED */}
      {showAddModal && (
        <div
          className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex justify-center items-start pt-8 px-4"
          onClick={() => {
            setShowAddModal(false);
            setShowManualEntry(false);
            setAddWalletAddress("");
            setAddWalletName("");
            clearWalletError();
          }}
        >
          <div
            className={`w-full max-w-sm rounded-2xl p-6 shadow-2xl ${
              theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white"
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                {showManualEntry ? "Add Wallet Manually" : "Connect Wallet"}
              </h3>
              <button
                onClick={() => {
                  if (showManualEntry) {
                    setShowManualEntry(false);
                    setAddWalletAddress("");
                    setAddWalletName("");
                  } else {
                    setShowAddModal(false);
                  }
                  clearWalletError();
                }}
                className={`p-1 rounded-lg transition-colors ${
                  theme === "dark" ? "hover:bg-zinc-800 text-zinc-400" : "hover:bg-gray-100 text-gray-600"
                }`}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {!showManualEntry ? (
              <>
                {/* 3 Wallet Buttons */}
                <div className="space-y-3 mb-6">
                  {/* Petra */}
                  <button
                    onClick={() => handleConnectWallet("petra")}
                    disabled={isWalletConnecting}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                      isWalletConnecting
                        ? "opacity-50 cursor-not-allowed"
                        : theme === "dark"
                        ? `border-zinc-700 ${SUPPORTED_WALLETS.petra.hoverBorder} ${SUPPORTED_WALLETS.petra.hoverBg}`
                        : `border-gray-200 ${SUPPORTED_WALLETS.petra.hoverBorder} hover:bg-red-50`
                    }`}
                  >
                    <div
                      className={`w-12 h-12 rounded-full bg-gradient-to-br ${SUPPORTED_WALLETS.petra.color} flex items-center justify-center`}
                    >
                      <span className="text-2xl">{SUPPORTED_WALLETS.petra.icon}</span>
                    </div>
                    <div className="flex-1 text-left">
                      <div className={`font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                        Petra
                      </div>
                      <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                        Aptos Chain (APT tokens)
                      </div>
                    </div>
                    {detectedWallets.petra ? (
                      isPetraAdded ? (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Added
                        </span>
                      ) : aptosConnected ? (
                        <span className="text-xs text-blue-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Click to Add
                        </span>
                      ) : (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Ready
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-zinc-500">
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    )}
                  </button>

                  {/* Phantom */}
                  <button
                    onClick={() => handleConnectWallet("phantom")}
                    disabled={isWalletConnecting || phantomConnecting}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                      isWalletConnecting || phantomConnecting
                        ? "opacity-50 cursor-not-allowed"
                        : theme === "dark"
                        ? `border-zinc-700 ${SUPPORTED_WALLETS.phantom.hoverBorder} ${SUPPORTED_WALLETS.phantom.hoverBg}`
                        : `border-gray-200 ${SUPPORTED_WALLETS.phantom.hoverBorder} hover:bg-purple-50`
                    }`}
                  >
                    <div
                      className={`w-12 h-12 rounded-full bg-gradient-to-br ${SUPPORTED_WALLETS.phantom.color} flex items-center justify-center`}
                    >
                      <span className="text-2xl">{SUPPORTED_WALLETS.phantom.icon}</span>
                    </div>
                    <div className="flex-1 text-left">
                      <div className={`font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                        Phantom
                      </div>
                      <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                        Solana + EVM (Multi-chain)
                      </div>
                    </div>
                    {detectedWallets.phantom ? (
                      isPhantomAdded ? (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Added
                        </span>
                      ) : phantomConnected ? (
                        <span className="text-xs text-blue-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Click to Add
                        </span>
                      ) : (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Ready
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-zinc-500">
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    )}
                    {phantomConnecting && <Loader2 className="w-4 h-4 animate-spin text-purple-500" />}
                  </button>

                  {/* MetaMask */}
                  <button
                    onClick={() => handleConnectWallet("metamask")}
                    disabled={isWalletConnecting || evmConnecting}
                    className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                      isWalletConnecting || evmConnecting
                        ? "opacity-50 cursor-not-allowed"
                        : theme === "dark"
                        ? `border-zinc-700 ${SUPPORTED_WALLETS.metamask.hoverBorder} ${SUPPORTED_WALLETS.metamask.hoverBg}`
                        : `border-gray-200 ${SUPPORTED_WALLETS.metamask.hoverBorder} hover:bg-orange-50`
                    }`}
                  >
                    <div
                      className={`w-12 h-12 rounded-full bg-gradient-to-br ${SUPPORTED_WALLETS.metamask.color} flex items-center justify-center`}
                    >
                      <span className="text-2xl">{SUPPORTED_WALLETS.metamask.icon}</span>
                    </div>
                    <div className="flex-1 text-left">
                      <div className={`font-semibold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                        MetaMask
                      </div>
                      <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                        EVM Chains (ETH, Sepolia, Polygon)
                      </div>
                    </div>
                    {detectedWallets.metamask ? (
                      isMetaMaskAdded ? (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Added
                        </span>
                      ) : evmConnected ? (
                        <span className="text-xs text-blue-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Click to Add
                        </span>
                      ) : (
                        <span className="text-xs text-green-500 flex items-center gap-1">
                          <Check className="w-3 h-3" /> Ready
                        </span>
                      )
                    ) : (
                      <span className="text-xs text-zinc-500">
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    )}
                    {evmConnecting && <Loader2 className="w-4 h-4 animate-spin text-orange-500" />}
                  </button>
                </div>

                {/* Loading indicator */}
                {isWalletConnecting && (
                  <div className="flex items-center justify-center gap-2 py-2 mb-4">
                    <Loader2 className={`w-4 h-4 animate-spin ${theme === "dark" ? "text-white" : "text-black"}`} />
                    <span className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                      Connecting...
                    </span>
                  </div>
                )}

                {/* Divider */}
                <div className="relative mb-4">
                  <div className="absolute inset-0 flex items-center">
                    <div className={`w-full border-t ${theme === "dark" ? "border-zinc-700" : "border-gray-200"}`} />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className={`px-3 ${theme === "dark" ? "bg-zinc-900 text-zinc-500" : "bg-white text-gray-500"}`}>
                      or
                    </span>
                  </div>
                </div>

                {/* Manual Add Button */}
                <button
                  onClick={() => setShowManualEntry(true)}
                  className={`w-full flex items-center justify-center gap-2 p-3 rounded-xl border-2 border-dashed transition-colors ${
                    theme === "dark"
                      ? "border-zinc-700 hover:border-zinc-600 text-zinc-400 hover:text-zinc-300"
                      : "border-gray-300 hover:border-gray-400 text-gray-600 hover:text-gray-700"
                  }`}
                >
                  <Plus className="w-5 h-5" />
                  <span className="font-medium">Add Wallet Manually</span>
                </button>

                <p className={`text-xs text-center mt-3 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                  Enter any wallet address to track its portfolio
                </p>
              </>
            ) : (
              /* Manual Entry Form */
              <div className="space-y-4">
                <div>
                  <label
                    className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}
                  >
                    Wallet Name (optional)
                  </label>
                  <input
                    type="text"
                    placeholder={isENSName(addWalletAddress) ? addWalletAddress.trim().toLowerCase() : "My Wallet"}
                    value={addWalletName}
                    onChange={(e) => setAddWalletName(e.target.value)}
                    className={`w-full px-4 py-2.5 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      theme === "dark"
                        ? "bg-zinc-800 border-zinc-700 text-zinc-300"
                        : "bg-white border-gray-300 text-gray-900"
                    }`}
                  />
                </div>

                <div>
                  <label
                    className={`block text-sm font-medium mb-2 ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}
                  >
                    Wallet Address or ENS Name
                  </label>
                  <input
                    type="text"
                    placeholder="0x…, Solana address, or vitalik.eth"
                    value={addWalletAddress}
                    onChange={(e) => setAddWalletAddress(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addWalletAddress.trim() && handleAddWallet()}
                    className={`w-full px-4 py-2.5 rounded-lg font-mono text-sm border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                      theme === "dark"
                        ? "bg-zinc-800 border-zinc-700 text-zinc-300"
                        : "bg-white border-gray-300 text-gray-900"
                    }`}
                  />
                  <p className={`mt-2 text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                    Enter an address (0x… / Solana) or an ENS name (e.g. vitalik.eth)
                  </p>
                </div>

                {/* ENS resolution status */}
                {addWalletAddress.trim() && isENSName(addWalletAddress) && (
                  <div className={`flex items-start gap-2 px-3 py-2.5 rounded-lg text-xs ${
                    ensResolving
                      ? theme === "dark" ? "bg-zinc-800 text-zinc-400" : "bg-gray-100 text-gray-500"
                      : ensResolved
                      ? "bg-emerald-500/10 border border-emerald-500/20 text-emerald-400"
                      : "bg-red-500/10 border border-red-500/20 text-red-400"
                  }`}>
                    {ensResolving ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0 mt-0.5" />
                        <span>Resolving ENS name…</span>
                      </>
                    ) : ensResolved ? (
                      <>
                        <Check className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        <div>
                          <p className="font-semibold">ENS resolved</p>
                          <p className="font-mono mt-0.5 break-all">{ensResolved}</p>
                        </div>
                      </>
                    ) : (
                      <span>{ensError || "ENS name not found"}</span>
                    )}
                  </div>
                )}

                {/* Detected chain preview (only shown for raw addresses) */}
                {addWalletAddress.trim() && !isENSName(addWalletAddress) && (
                  <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                    theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
                  }`}>
                    <span className={`text-xs ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                      Detected chain:
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${
                      getChainConfig(detectChainFromAddress(addWalletAddress)).color
                    }`}>
                      {getChainConfig(detectChainFromAddress(addWalletAddress)).emoji}{" "}
                      {getChainConfig(detectChainFromAddress(addWalletAddress)).name}
                    </span>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3 pt-2">
                  <button
                    onClick={() => {
                      setShowManualEntry(false);
                      setAddWalletAddress("");
                      setAddWalletName("");
                      setEnsResolved(null);
                      setEnsError(null);
                    }}
                    disabled={isAdding}
                    className={`flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors ${
                      theme === "dark"
                        ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                    } disabled:opacity-50`}
                  >
                    Back
                  </button>
                  <button
                    onClick={handleAddWallet}
                    disabled={
                      !addWalletAddress.trim() ||
                      isAdding ||
                      ensResolving ||
                      (isENSName(addWalletAddress) && !ensResolved)
                    }
                    className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isAdding ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Adding...
                      </span>
                    ) : (
                      "Add Wallet"
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <ManageWalletsModal isOpen={showManageModal} onClose={() => setShowManageModal(false)} />
    </>
  );
};

export default WalletBar;
