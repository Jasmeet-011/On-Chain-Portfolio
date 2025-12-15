// src/context/AppContext.tsx
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import type { ReactNode } from "react";
import { useWallet } from "@aptos-labs/wallet-adapter-react";
import { api } from "../api";
import type { WalletResponse } from "../api";

export type Theme = "light" | "dark";

// Extended WalletInfo to track source
export interface ExtendedWalletInfo {
  id: string;
  address: string;
  label: string;
  type: 'manual' | 'petra';
  is_primary: boolean;
  created_at: string;
  publicKey?: string; // For locally tracking connected wallet keys
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
  wallets: ExtendedWalletInfo[];
  setWallets: (wallets: ExtendedWalletInfo[]) => void;
  activeWallet: ExtendedWalletInfo | null;
  setActiveWallet: (wallet: ExtendedWalletInfo | null) => void;
  addWallet: (address: string, label: string, isPrimary?: boolean, type?: 'manual' | 'petra', publicKey?: string) => Promise<void>;
  removeWallet: (address: string) => Promise<void>;
  updateWalletName: (address: string, label: string) => Promise<void>;
  setPrimaryWallet: (address: string) => Promise<void>;
  connectWallet: (walletName: string) => Promise<void>;
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

// Helper to convert backend wallet to ExtendedWalletInfo
function toExtendedWallet(wallet: WalletResponse, publicKey?: string): ExtendedWalletInfo {
  return {
    id: wallet.id,
    address: wallet.address,
    label: wallet.label,
    type: wallet.type,
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
      setActiveWallet(null);
      setPortfolioData(null);
      setMessages([]);
    }
    setCurrentUserInternal(user);
  }, [currentUser?.id]);
  
  const { theme, toggleTheme } = useThemeInternal();

  const [wallets, setWallets] = useState<ExtendedWalletInfo[]>([]);
  const [activeWallet, setActiveWalletInternal] = useState<ExtendedWalletInfo | null>(null);
  
  // Wallet adapter state
  const [isWalletConnecting, setIsWalletConnecting] = useState(false);
  const [walletError, setWalletError] = useState<string | null>(null);

  // Get wallet adapter hooks
  const {
    connect: adapterConnect,
    disconnect: adapterDisconnect,
    account,
    connected,
    wallet: connectedWallet,
    wallets: adapterWallets,
  } = useWallet();

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

  // Connect wallet using adapter
  const connectWallet = async (walletName: string) => {
    setIsWalletConnecting(true);
    setWalletError(null);

    try {
      await adapterConnect(walletName as any);
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

  // Handle wallet connection state changes - ONLY if user is logged in
  useEffect(() => {
    // IMPORTANT: Don't auto-add wallets if user is not logged in
    if (!currentUser) {
      console.log("[AppContext] User not logged in, skipping wallet auto-add");
      return;
    }

    if (connected && account?.address && connectedWallet) {
      const addressStr = account.address.toString();
      const existingWallet = wallets.find(w => 
        w.address.toLowerCase() === addressStr.toLowerCase()
      );

      if (!existingWallet) {
        let publicKeyStr: string | undefined;
        if (account.publicKey) {
          if (Array.isArray(account.publicKey)) {
            publicKeyStr = account.publicKey[0]?.toString();
          } else {
            publicKeyStr = account.publicKey.toString();
          }
        }

        // Add wallet via API
        addWallet(
          addressStr,
          `${connectedWallet.name} Wallet`,
          wallets.length === 0,
          'petra',
          publicKeyStr
        ).catch(err => {
          console.error("[AppContext] Failed to add connected wallet:", err);
          setWalletError("Failed to save wallet to account");
        });
      } else if (!activeWallet || activeWallet.address !== addressStr) {
        setActiveWallet(existingWallet);
      }
    }
  }, [connected, account, connectedWallet, currentUser]);

  // Disconnect a connected wallet
  const disconnectConnectedWallet = async (address: string) => {
    const walletToDisconnect = wallets.find(w => w.address === address);
    
    if (walletToDisconnect && walletToDisconnect.type === 'petra') {
      const currentAddress = account?.address?.toString();
      if (currentAddress?.toLowerCase() === address.toLowerCase()) {
        try {
          await adapterDisconnect();
        } catch (error) {
          console.error("[AppContext] Error disconnecting from adapter:", error);
        }
      }
    }

    await removeWallet(address);
  };

  const addWallet = async (
    address: string, 
    label: string, 
    isPrimary: boolean = false,
    type: 'manual' | 'petra' = 'manual',
    publicKey?: string
  ) => {
    // Check if wallet already exists
    if (wallets.some(w => w.address.toLowerCase() === address.toLowerCase())) {
      throw new Error("Wallet already exists");
    }

    // If not logged in, store locally (for backward compatibility)
    if (!currentUser) {
      const newWallet: ExtendedWalletInfo = {
        id: `local_${Date.now()}`,
        address,
        label,
        type,
        is_primary: isPrimary || wallets.length === 0,
        created_at: new Date().toISOString(),
        publicKey,
      };

      const updatedWallets = [...wallets];
      if (newWallet.is_primary) {
        updatedWallets.forEach(w => w.is_primary = false);
      }
      updatedWallets.push(newWallet);
      setWallets(updatedWallets);

      if (updatedWallets.length === 1 || newWallet.is_primary) {
        setActiveWallet(newWallet);
      }

      localStorage.setItem("wallets", JSON.stringify(updatedWallets));
      return;
    }

    // Add to backend
    try {
      console.log("[AppContext] Adding wallet to backend:", { address, label, type });
      const newWallet = await api.addWallet(address, label, type, isPrimary);
      
      // Reload all wallets to get updated state
      await loadWallets();
      
      console.log("[AppContext] Wallet added successfully");
    } catch (error) {
      console.error("[AppContext] Failed to add wallet:", error);
      throw error;
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

  // Load wallets from backend
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

  // Logout function - ✅ FIXED: Proper async handling
  const logout = useCallback(() => {
    console.log("[AppContext] Logging out user");
    
    // Disconnect wallet adapter FIRST (before clearing state)
    if (connected) {
      try {
        // Wrap in Promise.resolve to handle both sync and async disconnect
        Promise.resolve(adapterDisconnect()).catch(err => 
          console.error("[AppContext] Error disconnecting adapter:", err)
        );
      } catch (err) {
        console.error("[AppContext] Error disconnecting adapter:", err);
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
  }, [connected, adapterDisconnect, setCurrentUser]);

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
            const parsedWallets: ExtendedWalletInfo[] = JSON.parse(stored);
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
          } catch (error) {
            console.error("[AppContext] Failed to parse stored wallets:", error);
          }
        }
      }
    };

    initWallets();
  }, [currentUser?.id]);

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
    activeWallet,
    setActiveWallet,
    addWallet,
    removeWallet,
    updateWalletName,
    setPrimaryWallet,
    connectWallet,
    disconnectConnectedWallet,
    availableWallets: adapterWallets || [],
    isWalletConnecting,
    walletError,
    clearWalletError,
    isLoading,
    setIsLoading,
    portfolioData,
    setPortfolioData,
    theme,
    toggleTheme,
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