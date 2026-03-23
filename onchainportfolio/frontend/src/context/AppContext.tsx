// src/context/AppContext.tsx - MULTI-CHAIN SUPPORT (Aptos, Solana, EVM)
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import type { ReactNode } from "react";
import { useWallet } from "@aptos-labs/wallet-adapter-react";
import { useSolanaWallet } from "./SolanaWalletProvider";
import { useEVMWallet } from "./EVMWalletProvider";
import { api } from "../api";
import type { WalletResponse } from "../api";
import type { ChainType, WalletType } from "../api";

export type Theme = "light" | "dark";
export type NetworkMode = "testnet" | "mainnet";

// ✅ UPDATED: Extended WalletInfo with multi-chain support (Aptos, Solana, EVM)
export interface ExtendedWalletInfo {
  id: string;
  address: string;
  label: string;
  type: WalletType;
  chain: ChainType;
  is_primary: boolean;
  created_at: string;
  publicKey?: string;
}

// Grouped wallet - represents a wallet provider with potentially multiple chain addresses
export interface WalletGroup {
  id: string;                    // Unique group ID (e.g., "phantom", "metamask", "petra")
  type: WalletType;              // Provider type
  label: string;                 // Display name (e.g., "Phantom", "MetaMask")
  icon: string;                  // Emoji icon
  wallets: ExtendedWalletInfo[]; // All wallets belonging to this provider
  chains: ChainType[];           // All chains this provider supports
  is_primary: boolean;           // Whether this group contains the primary wallet
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  data?: any;
}

export interface AppContextType {
  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  manualAddress: string;
  setManualAddress: (addr: string) => void;
  // Individual wallets (raw list)
  wallets: ExtendedWalletInfo[];
  setWallets: (wallets: ExtendedWalletInfo[]) => void;
  // Grouped wallets by provider (for UI display)
  walletGroups: WalletGroup[];
  activeWalletGroup: WalletGroup | null;
  setActiveWalletGroup: (group: WalletGroup | null) => void;
  // Legacy single wallet selection (for backward compatibility)
  activeWallet: ExtendedWalletInfo | null;
  setActiveWallet: (wallet: ExtendedWalletInfo | null) => void;
  // Wallet management
  addWallet: (address: string, label: string, isPrimary?: boolean, type?: WalletType, chain?: ChainType, publicKey?: string) => Promise<void>;
  removeWallet: (address: string) => Promise<void>;
  removeWalletGroup: (groupType: WalletType) => Promise<void>;
  updateWalletName: (address: string, label: string) => Promise<void>;
  setPrimaryWallet: (address: string) => Promise<void>;
  connectWallet: (walletName: string, chain: ChainType) => Promise<void>;
  disconnectConnectedWallet: (address: string) => Promise<void>;
  availableWallets: readonly any[];
  isWalletConnecting: boolean;
  walletError: string | null;
  clearWalletError: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  portfolioData: any;
  setPortfolioData: (data: any) => void;
  theme: Theme;
  toggleTheme: () => void;
  networkMode: NetworkMode;
  toggleNetwork: () => void;
  clearPortfolio: () => void;
  currentUser: { id: string; name: string; email: string } | null;
  setCurrentUser: (user: { id: string; name: string; email: string } | null) => void;
  logout: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

const useThemeInternal = () => {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("theme");
    return (saved === "light" || saved === "dark") ? saved : "dark";
  });

  const toggleTheme = () => {
    setTheme((prev) => {
      const newTheme = prev === "light" ? "dark" : "light";
      localStorage.setItem("theme", newTheme);
      return newTheme;
    });
  };

  return { theme, toggleTheme };
};

export const useAppContext = () => {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return ctx;
};

// ✅ UPDATED: Helper to convert backend wallet to ExtendedWalletInfo (now includes chain)
function toExtendedWallet(wallet: WalletResponse, publicKey?: string): ExtendedWalletInfo {
  return {
    id: wallet.id,
    address: wallet.address,
    label: wallet.label,
    type: wallet.type,
    chain: wallet.chain, // ✅ NEW: Chain from backend
    is_primary: wallet.is_primary,
    created_at: wallet.created_at,
    publicKey,
  };
}

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [manualAddress, setManualAddressInternal] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const [currentUser, setCurrentUserInternal] = useState<{ id: string; name: string; email: string } | null>(null);
  
  // Wrapper to clear state when user changes
  const setCurrentUser = useCallback((user: { id: string; name: string; email: string } | null) => {
    // Clear all user-specific state when logging out or switching users
    if (!user || user.id !== currentUser?.id) {
      console.log("[AppContext] User changed, clearing wallet state");
      setWallets([]);
      setActiveWalletInternal(null);
      setActiveWalletGroupInternal(null);
      setPortfolioData(null);
      setMessages([]);
    }
    setCurrentUserInternal(user);
  }, [currentUser?.id]);
  
  const { theme, toggleTheme } = useThemeInternal();

  const [networkMode, setNetworkMode] = useState<NetworkMode>(() => {
    const saved = localStorage.getItem("networkMode");
    return saved === "mainnet" ? "mainnet" : "testnet";
  });

  const toggleNetwork = () => {
    setNetworkMode((prev) => {
      const next: NetworkMode = prev === "testnet" ? "mainnet" : "testnet";
      localStorage.setItem("networkMode", next);
      return next;
    });
  };

  const [wallets, setWallets] = useState<ExtendedWalletInfo[]>([]);
  const [activeWallet, setActiveWalletInternal] = useState<ExtendedWalletInfo | null>(null);
  const [activeWalletGroup, setActiveWalletGroupInternal] = useState<WalletGroup | null>(null);

  // Wallet provider configuration for grouping
  const WALLET_PROVIDER_CONFIG: Record<string, { label: string; icon: string }> = {
    petra: { label: "Petra", icon: "🔴" },
    phantom: { label: "Phantom", icon: "👻" },
    metamask: { label: "MetaMask", icon: "🦊" },
    coinbase: { label: "Coinbase", icon: "🔵" },
    manual: { label: "Manual Wallet", icon: "💼" },
  };

  // Compute wallet groups from wallets array
  const walletGroups: WalletGroup[] = React.useMemo(() => {
    const groupMap = new Map<string, WalletGroup>();

    wallets.forEach((wallet) => {
      const providerType = wallet.type;
      const config = WALLET_PROVIDER_CONFIG[providerType] || { label: providerType, icon: "💼" };

      if (!groupMap.has(providerType)) {
        groupMap.set(providerType, {
          id: providerType,
          type: providerType as WalletType,
          label: config.label,
          icon: config.icon,
          wallets: [],
          chains: [],
          is_primary: false,
        });
      }

      const group = groupMap.get(providerType)!;
      group.wallets.push(wallet);

      if (!group.chains.includes(wallet.chain)) {
        group.chains.push(wallet.chain);
      }

      if (wallet.is_primary) {
        group.is_primary = true;
      }
    });

    return Array.from(groupMap.values());
  }, [wallets]);

  // Set active wallet group (and set first wallet as activeWallet for compatibility)
  const setActiveWalletGroup = useCallback((group: WalletGroup | null) => {
    setActiveWalletGroupInternal(group);
    if (group && group.wallets.length > 0) {
      // Set the first wallet in the group as active for backward compatibility
      const primaryWallet = group.wallets.find(w => w.is_primary) || group.wallets[0];
      setActiveWalletInternal(primaryWallet);
      setManualAddressInternal(primaryWallet.address);
      localStorage.setItem("activeWalletGroup", group.id);
    } else {
      setActiveWalletInternal(null);
      setManualAddressInternal("");
      localStorage.removeItem("activeWalletGroup");
    }
  }, []);

  // Remove all wallets belonging to a provider group
  const removeWalletGroup = async (groupType: WalletType) => {
    const walletsToRemove = wallets.filter(w => w.type === groupType);

    for (const wallet of walletsToRemove) {
      await removeWallet(wallet.address);
    }

    // If we removed the active group, select another one
    if (activeWalletGroup?.type === groupType) {
      const remainingGroups = walletGroups.filter(g => g.type !== groupType);
      setActiveWalletGroup(remainingGroups[0] || null);
    }
  };

  // Wallet adapter state
  const [isWalletConnecting, setIsWalletConnecting] = useState(false);
  const [walletError, setWalletError] = useState<string | null>(null);

  // Track wallets being added to prevent duplicates
  const addingWalletsRef = React.useRef<Set<string>>(new Set());

  // ✅ Get Aptos wallet adapter hooks
  const {
    connect: aptosConnect,
    disconnect: aptosDisconnect,
    account: aptosAccount,
    connected: aptosConnected,
    wallet: aptosConnectedWallet,
    wallets: aptosWallets,
  } = useWallet();

  // Get Solana wallet hooks (with Phantom multi-chain EVM support)
  const {
    connect: solanaConnect,
    disconnect: solanaDisconnect,
    publicKey: solanaPublicKey,
    connected: solanaConnected,
    evmAddress: phantomEvmAddress,
    hasEvmSupport: phantomHasEvmSupport,
  } = useSolanaWallet();

  // ✅ NEW: Get EVM wallet hooks
  const {
    connect: evmConnect,
    disconnect: evmDisconnect,
    address: evmAddress,
    chainId: evmChainId,
    connected: evmConnected,
    walletType: evmWalletType,
  } = useEVMWallet();

  const clearWalletError = useCallback(() => setWalletError(null), []);

  const setManualAddress = async (addr: string) => {
    setManualAddressInternal(addr);
    if (addr) {
      localStorage.setItem("walletAddress", addr);
    } else {
      localStorage.removeItem("walletAddress");
    }
  };

  const setActiveWallet = (wallet: ExtendedWalletInfo | null) => {
    setActiveWalletInternal(wallet);
    if (wallet) {
      setManualAddressInternal(wallet.address);
      localStorage.setItem("activeWalletAddress", wallet.address);
    } else {
      setManualAddressInternal("");
      localStorage.removeItem("activeWalletAddress");
    }
  };

  // ✅ UPDATED: Connect wallet with chain parameter (supports EVM chains)
  const connectWallet = async (walletName: string, chain: ChainType) => {
    setIsWalletConnecting(true);
    setWalletError(null);

    try {
      if (chain === 'aptos') {
        // Connect Aptos wallet (Petra, etc.)
        await aptosConnect(walletName as any);
      } else if (chain === 'solana') {
        // Connect Solana wallet (Phantom)
        await solanaConnect();
      } else if (chain === 'evm' || ['ethereum', 'polygon', 'base', 'ethereum_sepolia', 'polygon_amoy', 'base_sepolia'].includes(chain)) {
        // Connect EVM wallet (MetaMask, Coinbase, etc.) - works on all EVM chains
        await evmConnect();
      }
    } catch (error: any) {
      console.error("[AppContext] Failed to connect wallet:", error);

      if (error?.message?.includes('User rejected') || error?.code === 4001) {
        setWalletError("Connection rejected. Please approve the connection in your wallet.");
      } else if (error?.message?.includes('not installed')) {
        setWalletError(`${walletName} is not installed. Please install it first.`);
      } else {
        setWalletError(error?.message || "Failed to connect wallet");
      }
    } finally {
      setIsWalletConnecting(false);
    }
  };

  // Handle Aptos wallet connection (Petra)
  useEffect(() => {
    if (!currentUser) {
      console.log("[AppContext] User not logged in, skipping Aptos wallet auto-add");
      return;
    }

    if (aptosConnected && aptosAccount?.address && aptosConnectedWallet) {
      const addressStr = aptosAccount.address.toString();

      let publicKeyStr: string | undefined;
      if (aptosAccount.publicKey) {
        if (Array.isArray(aptosAccount.publicKey)) {
          publicKeyStr = aptosAccount.publicKey[0]?.toString();
        } else {
          publicKeyStr = aptosAccount.publicKey.toString();
        }
      }

      // Add Aptos wallet via API (addWallet handles duplicates internally)
      const timer = setTimeout(() => {
        addWallet(
          addressStr,
          `${aptosConnectedWallet.name} Wallet`,
          true, // Make primary
          'petra',
          'aptos',
          publicKeyStr
        ).catch(err => {
          // Only log, don't show error (duplicate prevention may trigger this)
          console.log("[AppContext] Aptos wallet add result:", err?.message || 'success');
        });
      }, 100);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aptosConnected, aptosAccount?.address, aptosConnectedWallet?.name, currentUser?.id]);

  // ✅ Handle Solana wallet connection (with Phantom multi-chain EVM support)
  useEffect(() => {
    if (!currentUser) {
      console.log("[AppContext] User not logged in, skipping Solana wallet auto-add");
      return;
    }

    if (solanaConnected && solanaPublicKey) {
      const addressStr = solanaPublicKey;

      // Add Solana wallet via API (addWallet handles duplicates internally)
      const timer = setTimeout(() => {
        addWallet(
          addressStr,
          "Phantom (Solana)",
          true, // Make primary
          'phantom',
          'solana',
          solanaPublicKey
        ).catch(err => {
          // Only log, don't show error (duplicate prevention may trigger this)
          console.log("[AppContext] Solana wallet add result:", err?.message || 'success');
        });
      }, 100);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [solanaConnected, solanaPublicKey, currentUser?.id]);

  // ✅ Handle Phantom's EVM wallet (multi-chain support)
  useEffect(() => {
    if (!currentUser) {
      return;
    }

    // Only add if Phantom has EVM support and we have an EVM address from Phantom
    if (phantomHasEvmSupport && phantomEvmAddress && solanaConnected) {
      console.log("[AppContext] Adding Phantom EVM wallet:", phantomEvmAddress);

      const timer = setTimeout(() => {
        addWallet(
          phantomEvmAddress,
          "Phantom (EVM)",
          false, // Not primary, Solana wallet is primary
          'phantom',
          'evm',
          phantomEvmAddress
        ).catch(err => {
          // Only log, don't show error (duplicate prevention may trigger this)
          console.log("[AppContext] Phantom EVM wallet add result:", err?.message || 'success');
        });
      }, 300); // Slightly longer delay to ensure Solana wallet is added first
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phantomHasEvmSupport, phantomEvmAddress, solanaConnected, currentUser?.id]);

  // ✅ Handle EVM wallet connection (MetaMask, Coinbase, etc.)
  useEffect(() => {
    if (!currentUser) {
      console.log("[AppContext] User not logged in, skipping EVM wallet auto-add");
      return;
    }

    if (evmConnected && evmAddress) {
      // Determine wallet type and label
      const walletTypeMap: Record<string, WalletType> = {
        'metamask': 'metamask',
        'coinbase': 'coinbase',
        'unknown': 'metamask',
      };
      const walletType = walletTypeMap[evmWalletType || 'unknown'] || 'metamask';
      const walletLabel = evmWalletType === 'metamask' ? 'MetaMask Wallet' :
                          evmWalletType === 'coinbase' ? 'Coinbase Wallet' : 'EVM Wallet';

      // Add EVM wallet (addWallet handles duplicates internally)
      const timer = setTimeout(() => {
        addWallet(
          evmAddress,
          walletLabel,
          true, // Make primary if first wallet
          walletType,
          'evm',
          evmAddress
        ).catch(err => {
          // Only log, don't show error (duplicate prevention may trigger this)
          console.log("[AppContext] EVM wallet add result:", err?.message || 'success');
        });
      }, 100);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evmConnected, evmAddress, evmWalletType, currentUser?.id]);

  // Disconnect a connected wallet (supports Aptos, Solana, and EVM)
  const disconnectConnectedWallet = async (address: string) => {
    const walletToDisconnect = wallets.find(w => w.address === address);

    if (walletToDisconnect) {
      // Disconnect from appropriate adapter
      if (walletToDisconnect.chain === 'aptos' && walletToDisconnect.type === 'petra') {
        const currentAddress = aptosAccount?.address?.toString();
        if (currentAddress?.toLowerCase() === address.toLowerCase()) {
          try {
            await aptosDisconnect();
          } catch (error) {
            console.error("[AppContext] Error disconnecting from Aptos adapter:", error);
          }
        }
      } else if (walletToDisconnect.chain === 'solana' && walletToDisconnect.type === 'phantom') {
        if (solanaPublicKey?.toLowerCase() === address.toLowerCase()) {
          try {
            await solanaDisconnect();
          } catch (error) {
            console.error("[AppContext] Error disconnecting from Solana adapter:", error);
          }
        }
      } else if (
        (walletToDisconnect.chain === 'evm' || ['ethereum', 'polygon', 'base', 'ethereum_sepolia', 'polygon_amoy', 'base_sepolia'].includes(walletToDisconnect.chain)) &&
        ['metamask', 'coinbase', 'walletconnect'].includes(walletToDisconnect.type)
      ) {
        // EVM wallet disconnect
        if (evmAddress?.toLowerCase() === address.toLowerCase()) {
          try {
            await evmDisconnect();
          } catch (error) {
            console.error("[AppContext] Error disconnecting from EVM adapter:", error);
          }
        }
      }
    }

    await removeWallet(address);
  };

  // ✅ UPDATED: Add wallet with chain parameter (supports EVM chains)
  const addWallet = async (
    address: string,
    label: string,
    isPrimary: boolean = false,
    type: WalletType = 'manual',
    chain: ChainType = 'aptos',
    publicKey?: string
  ) => {
    // Create unique key for this wallet
    const walletKey = `${chain}:${address.toLowerCase()}`;

    // Check if already being added (prevent race conditions)
    if (addingWalletsRef.current.has(walletKey)) {
      console.log("[AppContext] Wallet already being added, skipping:", walletKey);
      return;
    }

    // Check if wallet already exists (same address AND same chain)
    if (wallets.some(w =>
      w.address.toLowerCase() === address.toLowerCase() &&
      w.chain === chain
    )) {
      console.log("[AppContext] Wallet already exists, skipping:", walletKey);
      return;
    }

    // Mark as being added
    addingWalletsRef.current.add(walletKey);

    // If not logged in, store locally (for backward compatibility)
    if (!currentUser) {
      try {
        const localWallet: ExtendedWalletInfo = {
          id: `local_${Date.now()}`,
          address,
          label,
          type,
          chain,
          is_primary: isPrimary || wallets.length === 0,
          created_at: new Date().toISOString(),
          publicKey,
        };

        const updatedWallets = [...wallets];
        if (localWallet.is_primary) {
          updatedWallets.forEach(w => w.is_primary = false);
        }
        updatedWallets.push(localWallet);
        setWallets(updatedWallets);

        if (updatedWallets.length === 1 || localWallet.is_primary) {
          setActiveWallet(localWallet);
        }

        localStorage.setItem("wallets", JSON.stringify(updatedWallets));
      } finally {
        addingWalletsRef.current.delete(walletKey);
      }
      return;
    }

    // Add to backend
    try {
      console.log("[AppContext] Adding wallet to backend:", { address, label, type, chain });
      await api.addWallet(address, label, type, isPrimary, chain);

      // Reload all wallets to get updated state
      await loadWallets();

      console.log("[AppContext] Wallet added successfully");
    } catch (error) {
      console.error("[AppContext] Failed to add wallet:", error);
      throw error;
    } finally {
      // Always clear the adding flag
      addingWalletsRef.current.delete(walletKey);
    }
  };

  const removeWallet = async (address: string) => {
    if (!currentUser) {
      const updatedWallets = wallets.filter(w => w.address !== address);
      setWallets(updatedWallets);

      if (activeWallet?.address === address) {
        setActiveWallet(updatedWallets[0] || null);
      }

      localStorage.setItem("wallets", JSON.stringify(updatedWallets));
      return;
    }

    try {
      console.log("[AppContext] Removing wallet from backend...");
      await api.removeWallet(address);

      // Reload wallets
      await loadWallets();

      console.log("[AppContext] Wallet removed successfully");
    } catch (error) {
      console.error("[AppContext] Failed to remove wallet:", error);
      throw error;
    }
  };

  const updateWalletName = async (address: string, label: string) => {
    if (!currentUser) {
      const updatedWallets = wallets.map(w =>
        w.address === address ? { ...w, label } : w
      );
      setWallets(updatedWallets);

      if (activeWallet?.address === address) {
        setActiveWallet({ ...activeWallet, label });
      }

      localStorage.setItem("wallets", JSON.stringify(updatedWallets));
      return;
    }

    try {
      console.log("[AppContext] Updating wallet label...");
      await api.updateWalletLabel(address, label);
      
      // Reload wallets
      await loadWallets();

      console.log("[AppContext] Wallet label updated successfully");
    } catch (error) {
      console.error("[AppContext] Failed to update wallet label:", error);
      throw error;
    }
  };

  const setPrimaryWallet = async (address: string) => {
    if (!currentUser) {
      const updatedWallets = wallets.map(w => ({
        ...w,
        is_primary: w.address === address,
      }));
      setWallets(updatedWallets);

      const primary = updatedWallets.find(w => w.address === address);
      if (primary) {
        setActiveWallet(primary);
      }

      localStorage.setItem("wallets", JSON.stringify(updatedWallets));
      return;
    }

    try {
      console.log("[AppContext] Setting primary wallet...");
      await api.setPrimaryWallet(address);
      
      // Reload wallets
      await loadWallets();

      console.log("[AppContext] Primary wallet set successfully");
    } catch (error) {
      console.error("[AppContext] Failed to set primary wallet:", error);
      throw error;
    }
  };

  // ✅ Load wallets from backend (now includes chain field)
  const loadWallets = async () => {
    if (!currentUser) return;

    try {
      const backendWallets = await api.getWallets();
      
      // Convert to ExtendedWalletInfo, preserving publicKey from local state
      const extendedWallets: ExtendedWalletInfo[] = backendWallets.map(w => {
        const existing = wallets.find(ew => ew.address === w.address);
        return toExtendedWallet(w, existing?.publicKey);
      });
      
      setWallets(extendedWallets);

      // Set active wallet to primary or first
      const primary = extendedWallets.find(w => w.is_primary);
      const newActive = primary || extendedWallets[0] || null;

      // Only update active wallet if address changed
      if (!activeWallet || activeWallet.address !== newActive?.address) {
        setActiveWallet(newActive);
      }
    } catch (error) {
      console.error("[AppContext] Failed to load wallets:", error);
    }
  };

  const addMessage = (msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
    if (msg.data) {
      setPortfolioData(msg.data);
    }
  };

  const clearPortfolio = () => {
    setPortfolioData(null);
    setMessages([]);
  };

  // Logout function - Proper async handling (supports all wallet types)
  const logout = useCallback(() => {
    console.log("[AppContext] Logging out user");

    // Disconnect wallet adapters FIRST (before clearing state)
    if (aptosConnected) {
      try {
        Promise.resolve(aptosDisconnect()).catch(err =>
          console.error("[AppContext] Error disconnecting Aptos adapter:", err)
        );
      } catch (err) {
        console.error("[AppContext] Error disconnecting Aptos adapter:", err);
      }
    }

    if (solanaConnected) {
      try {
        Promise.resolve(solanaDisconnect()).catch(err =>
          console.error("[AppContext] Error disconnecting Solana adapter:", err)
        );
      } catch (err) {
        console.error("[AppContext] Error disconnecting Solana adapter:", err);
      }
    }

    // ✅ NEW: Disconnect EVM wallets
    if (evmConnected) {
      try {
        Promise.resolve(evmDisconnect()).catch(err =>
          console.error("[AppContext] Error disconnecting EVM adapter:", err)
        );
      } catch (err) {
        console.error("[AppContext] Error disconnecting EVM adapter:", err);
      }
    }

    // Clear user from context (this triggers state cleanup via setCurrentUser wrapper)
    setCurrentUser(null);

    // Clear localStorage
    localStorage.removeItem("user");
    localStorage.removeItem("wallets");
    localStorage.removeItem("activeWalletAddress");
    localStorage.removeItem("walletAddress");

    console.log("[AppContext] Logout complete");
  }, [aptosConnected, solanaConnected, evmConnected, aptosDisconnect, solanaDisconnect, evmDisconnect, setCurrentUser]);

  // Load wallets on mount or when user changes
  useEffect(() => {
    const initWallets = async () => {
      if (currentUser) {
        console.log("[AppContext] Loading wallets for user:", currentUser.id);
        await loadWallets();
      } else {
        console.log("[AppContext] No user logged in, loading from localStorage");
        // Not logged in - load from localStorage
        const stored = localStorage.getItem("wallets");
        if (stored) {
          try {
            // ✅ FIX: Migrate old wallets without chain field
            const parsedWallets: ExtendedWalletInfo[] = JSON.parse(stored).map((w: any) => ({
              ...w,
              chain: w.chain || 'aptos', // Default to aptos if missing
              type: w.type || 'manual' // Default to manual if missing
            }));
            
            setWallets(parsedWallets);

            const activeAddr = localStorage.getItem("activeWalletAddress");
            if (activeAddr) {
              const active = parsedWallets.find(w => w.address === activeAddr);
              if (active) {
                setActiveWallet(active);
              }
            } else if (parsedWallets.length > 0) {
              setActiveWallet(parsedWallets[0]);
            }
            
            // ✅ Save migrated wallets back to localStorage
            localStorage.setItem("wallets", JSON.stringify(parsedWallets));
          } catch (error) {
            console.error("[AppContext] Failed to parse stored wallets:", error);
          }
        }
      }
    };

    initWallets();
  }, [currentUser?.id]);

  // Auto-select wallet group when walletGroups changes
  useEffect(() => {
    if (walletGroups.length > 0 && !activeWalletGroup) {
      // Try to restore from localStorage
      const savedGroupId = localStorage.getItem("activeWalletGroup");
      if (savedGroupId) {
        const savedGroup = walletGroups.find(g => g.id === savedGroupId);
        if (savedGroup) {
          setActiveWalletGroup(savedGroup);
          return;
        }
      }

      // Otherwise select the primary group or first group
      const primaryGroup = walletGroups.find(g => g.is_primary);
      setActiveWalletGroup(primaryGroup || walletGroups[0]);
    } else if (walletGroups.length === 0 && activeWalletGroup) {
      setActiveWalletGroup(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [walletGroups]);

  useEffect(() => {
    api.health().then((res) => console.log("Backend health:", res));
  }, []);

  const value: AppContextType = {
    messages,
    addMessage,
    manualAddress,
    setManualAddress,
    wallets,
    setWallets,
    // Grouped wallets
    walletGroups,
    activeWalletGroup,
    setActiveWalletGroup,
    // Legacy single wallet
    activeWallet,
    setActiveWallet,
    // Wallet management
    addWallet,
    removeWallet,
    removeWalletGroup,
    updateWalletName,
    setPrimaryWallet,
    connectWallet,
    disconnectConnectedWallet,
    availableWallets: aptosWallets || [],
    isWalletConnecting,
    walletError,
    clearWalletError,
    isLoading,
    setIsLoading,
    portfolioData,
    setPortfolioData,
    theme,
    toggleTheme,
    networkMode,
    toggleNetwork,
    clearPortfolio,
    currentUser,
    setCurrentUser,
    logout,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};