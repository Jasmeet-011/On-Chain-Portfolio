// src/context/SolanaWalletProvider.tsx - MULTI-CHAIN PHANTOM SUPPORT
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface PhantomSolanaProvider {
  isPhantom?: boolean;
  connect: () => Promise<{ publicKey: { toString: () => string } }>;
  disconnect: () => Promise<void>;
  publicKey?: { toString: () => string };
  on: (event: string, callback: (...args: any[]) => void) => void;
  off: (event: string, callback: (...args: any[]) => void) => void;
}

interface PhantomEthereumProvider {
  isPhantom?: boolean;
  request: (args: { method: string; params?: any[] }) => Promise<any>;
  on: (event: string, callback: (...args: any[]) => void) => void;
  removeListener: (event: string, callback: (...args: any[]) => void) => void;
}

interface SolanaWalletContextType {
  connected: boolean;
  publicKey: string | null;
  // Phantom multi-chain support
  evmAddress: string | null;
  evmChainId: number | null;
  connecting: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  clearError: () => void;
  // Check if Phantom supports EVM
  hasEvmSupport: boolean;
}

const SolanaWalletContext = createContext<SolanaWalletContextType>({
  connected: false,
  publicKey: null,
  evmAddress: null,
  evmChainId: null,
  connecting: false,
  error: null,
  connect: async () => {},
  disconnect: async () => {},
  clearError: () => {},
  hasEvmSupport: false,
});

export const useSolanaWallet = () => useContext(SolanaWalletContext);

interface Props {
  children: ReactNode;
}

export const SolanaWalletProvider: React.FC<Props> = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [evmAddress, setEvmAddress] = useState<string | null>(null);
  const [evmChainId, setEvmChainId] = useState<number | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasEvmSupport, setHasEvmSupport] = useState(false);

  // Get Phantom Solana provider from window
  const getSolanaProvider = (): PhantomSolanaProvider | null => {
    if (typeof window === 'undefined') {
      return null;
    }

    if ('phantom' in window) {
      const provider = (window as any).phantom?.solana;
      if (provider?.isPhantom) {
        return provider;
      }
    }

    return null;
  };

  // Get Phantom Ethereum provider (multi-chain support)
  // Phantom exposes EVM at window.phantom.ethereum OR window.ethereum (if Phantom is default)
  const getEthereumProvider = (): PhantomEthereumProvider | null => {
    if (typeof window === 'undefined') {
      return null;
    }

    // Debug: Log what's available
    console.log('[Phantom] Checking EVM providers...', {
      hasPhantom: 'phantom' in window,
      hasPhantomEthereum: !!(window as any).phantom?.ethereum,
      hasWindowEthereum: !!(window as any).ethereum,
      windowEthereumIsPhantom: (window as any).ethereum?.isPhantom,
    });

    // First try window.phantom.ethereum (dedicated Phantom EVM)
    if ('phantom' in window) {
      const phantomEth = (window as any).phantom?.ethereum;
      if (phantomEth) {
        console.log('[Phantom] ✅ Found phantom.ethereum provider');
        return phantomEth;
      }
    }

    // Fallback: Check if window.ethereum is Phantom (not MetaMask)
    const globalEth = (window as any).ethereum;
    if (globalEth?.isPhantom && !globalEth?.isMetaMask) {
      console.log('[Phantom] ✅ Found window.ethereum (isPhantom=true, not MetaMask)');
      return globalEth;
    }

    console.log('[Phantom] ❌ No Phantom EVM provider found');
    return null;
  };

  // Clear error
  const clearError = () => setError(null);

  // Try to connect to Phantom's EVM provider and get the address
  const connectPhantomEvm = async (): Promise<{ address: string; chainId: number } | null> => {
    const ethProvider = getEthereumProvider();

    if (!ethProvider) {
      console.log('[Phantom] No EVM provider available');
      return null;
    }

    try {
      console.log('[Phantom] Connecting to EVM...');
      const accounts = await ethProvider.request({ method: 'eth_requestAccounts' });

      if (accounts && accounts.length > 0) {
        const chainIdHex = await ethProvider.request({ method: 'eth_chainId' });
        const chainId = parseInt(chainIdHex, 16);

        console.log('[Phantom] ✅ EVM Connected:', accounts[0], 'Chain:', chainId);
        return { address: accounts[0], chainId };
      }
    } catch (err: any) {
      // User might reject EVM connection - that's OK, we still have Solana
      console.log('[Phantom] EVM connection skipped or rejected:', err?.message);
    }

    return null;
  };

  // Connect to Phantom wallet (Solana + optionally EVM)
  const connect = async () => {
    setError(null);
    const solanaProvider = getSolanaProvider();

    if (!solanaProvider) {
      const errorMsg = "Phantom wallet not found. Please install Phantom from phantom.app";
      setError(errorMsg);
      console.error('[Phantom]', errorMsg);

      // Open Phantom download page
      window.open('https://phantom.app/', '_blank');
      throw new Error(errorMsg);
    }

    // Prevent duplicate connection attempts
    if (connecting) {
      console.log('[Phantom] Already connecting, please wait...');
      return;
    }

    // Check if already connected (Solana)
    if (solanaProvider.publicKey) {
      const address = solanaProvider.publicKey.toString();
      console.log('[Phantom] Already connected (Solana):', address);
      setPublicKey(address);
      setConnected(true);

      // Also try to get EVM address
      const evmResult = await connectPhantomEvm();
      if (evmResult) {
        setEvmAddress(evmResult.address);
        setEvmChainId(evmResult.chainId);
      }
      return;
    }

    try {
      setConnecting(true);
      console.log('[Phantom] Connecting to Solana...');

      // Connect Solana first
      const response = await solanaProvider.connect();
      const solanaAddress = response.publicKey.toString();

      setPublicKey(solanaAddress);
      setConnected(true);
      console.log('[Phantom] ✅ Solana Connected:', solanaAddress);

      // Now try to connect EVM (Phantom multi-chain)
      const evmResult = await connectPhantomEvm();
      if (evmResult) {
        setEvmAddress(evmResult.address);
        setEvmChainId(evmResult.chainId);
        setHasEvmSupport(true);
        console.log('[Phantom] ✅ Multi-chain: Solana + EVM connected');
      }

    } catch (err: any) {
      console.error('[Phantom] ❌ Connection error:', err);

      // Parse error message
      let errorMessage = "Failed to connect to Phantom wallet";

      if (err?.code === 4001) {
        errorMessage = "Connection rejected. Please approve the connection in Phantom.";
      } else if (err?.message?.includes('User rejected')) {
        errorMessage = "You rejected the connection request.";
      } else if (err?.message?.includes('already pending')) {
        errorMessage = "Connection request already pending. Please check Phantom.";
      } else if (err?.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setConnecting(false);
    }
  };

  // Disconnect wallet
  const disconnect = async () => {
    const solanaProvider = getSolanaProvider();

    if (solanaProvider) {
      try {
        console.log('[Phantom] Disconnecting...');
        await solanaProvider.disconnect();
        console.log('[Phantom] ✅ Disconnected');
      } catch (err) {
        console.error('[Phantom] Disconnect error:', err);
      }
    }

    setPublicKey(null);
    setEvmAddress(null);
    setEvmChainId(null);
    setConnected(false);
    setError(null);
  };

  // Check if already connected on mount + detect EVM support
  useEffect(() => {
    const solanaProvider = getSolanaProvider();
    const ethProvider = getEthereumProvider();

    // Check for EVM support
    if (ethProvider) {
      setHasEvmSupport(true);
      console.log('[Phantom] EVM support detected');
    }

    if (!solanaProvider) {
      console.log('[Phantom] Phantom wallet not installed');
      return;
    }

    // Check if already connected (Solana)
    if (solanaProvider.publicKey) {
      const address = solanaProvider.publicKey.toString();
      console.log('[Phantom] Already connected (Solana):', address);
      setPublicKey(address);
      setConnected(true);

      // Also check EVM connection
      if (ethProvider) {
        // First check if already connected
        ethProvider.request({ method: 'eth_accounts' }).then(async (accounts: string[]) => {
          if (accounts && accounts.length > 0) {
            setEvmAddress(accounts[0]);
            const chainIdHex = await ethProvider.request({ method: 'eth_chainId' });
            setEvmChainId(parseInt(chainIdHex, 16));
            setHasEvmSupport(true);
            console.log('[Phantom] Already connected (EVM):', accounts[0]);
          } else {
            // Not connected yet - try to request connection
            console.log('[Phantom] EVM not connected, requesting connection...');
            try {
              const newAccounts = await ethProvider.request({ method: 'eth_requestAccounts' });
              if (newAccounts && newAccounts.length > 0) {
                setEvmAddress(newAccounts[0]);
                const chainIdHex = await ethProvider.request({ method: 'eth_chainId' });
                setEvmChainId(parseInt(chainIdHex, 16));
                setHasEvmSupport(true);
                console.log('[Phantom] ✅ EVM connected:', newAccounts[0]);
              }
            } catch (err: any) {
              console.log('[Phantom] EVM connection skipped:', err?.message);
            }
          }
        }).catch((err: any) => {
          console.log('[Phantom] EVM check failed:', err?.message);
        });
      }
    }

    // Listen for Solana account changes
    const handleAccountChanged = (newPublicKey: any) => {
      console.log('[Phantom] Solana account changed:', newPublicKey);

      if (newPublicKey) {
        const address = newPublicKey.toString();
        setPublicKey(address);
        setConnected(true);
      } else {
        setPublicKey(null);
        setConnected(false);
      }
    };

    // Listen for disconnect events
    const handleDisconnect = () => {
      console.log('[Phantom] Wallet disconnected');
      setPublicKey(null);
      setEvmAddress(null);
      setEvmChainId(null);
      setConnected(false);
    };

    solanaProvider.on('accountChanged', handleAccountChanged);
    solanaProvider.on('disconnect', handleDisconnect);

    // Listen for EVM account/chain changes
    if (ethProvider) {
      const handleEvmAccountsChanged = (accounts: string[]) => {
        console.log('[Phantom] EVM accounts changed:', accounts);
        setEvmAddress(accounts.length > 0 ? accounts[0] : null);
      };

      const handleEvmChainChanged = (chainIdHex: string) => {
        const newChainId = parseInt(chainIdHex, 16);
        console.log('[Phantom] EVM chain changed:', newChainId);
        setEvmChainId(newChainId);
      };

      ethProvider.on('accountsChanged', handleEvmAccountsChanged);
      ethProvider.on('chainChanged', handleEvmChainChanged);

      return () => {
        solanaProvider.off('accountChanged', handleAccountChanged);
        solanaProvider.off('disconnect', handleDisconnect);
        ethProvider.removeListener('accountsChanged', handleEvmAccountsChanged);
        ethProvider.removeListener('chainChanged', handleEvmChainChanged);
      };
    }

    return () => {
      solanaProvider.off('accountChanged', handleAccountChanged);
      solanaProvider.off('disconnect', handleDisconnect);
    };
  }, []);

  const value: SolanaWalletContextType = {
    connected,
    publicKey,
    evmAddress,
    evmChainId,
    connecting,
    error,
    connect,
    disconnect,
    clearError,
    hasEvmSupport,
  };

  return (
    <SolanaWalletContext.Provider value={value}>
      {children}
    </SolanaWalletContext.Provider>
  );
};