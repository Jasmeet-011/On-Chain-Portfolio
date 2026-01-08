// src/context/SolanaWalletProvider.tsx - ENHANCED ERROR HANDLING
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface PhantomProvider {
  isPhantom?: boolean;
  connect: () => Promise<{ publicKey: { toString: () => string } }>;
  disconnect: () => Promise<void>;
  publicKey?: { toString: () => string };
  on: (event: string, callback: (...args: any[]) => void) => void;
  off: (event: string, callback: (...args: any[]) => void) => void;
}

interface SolanaWalletContextType {
  connected: boolean;
  publicKey: string | null;
  connecting: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  clearError: () => void;
}

const SolanaWalletContext = createContext<SolanaWalletContextType>({
  connected: false,
  publicKey: null,
  connecting: false,
  error: null,
  connect: async () => {},
  disconnect: async () => {},
  clearError: () => {},
});

export const useSolanaWallet = () => useContext(SolanaWalletContext);

interface Props {
  children: ReactNode;
}

export const SolanaWalletProvider: React.FC<Props> = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get Phantom provider from window
  const getProvider = (): PhantomProvider | null => {
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

  // Clear error
  const clearError = () => setError(null);

  // Connect to Phantom wallet
  const connect = async () => {
    setError(null);
    const provider = getProvider();
    
    if (!provider) {
      const errorMsg = "Phantom wallet not found. Please install Phantom from phantom.app";
      setError(errorMsg);
      console.error('[Solana]', errorMsg);
      
      // Open Phantom download page
      window.open('https://phantom.app/', '_blank');
      throw new Error(errorMsg);
    }

    // ✅ FIX: Prevent duplicate connection attempts
    if (connecting) {
      console.log('[Solana] Already connecting, please wait...');
      return;
    }

    // ✅ FIX: Check if already connected
    if (provider.publicKey) {
      const address = provider.publicKey.toString();
      console.log('[Solana] Already connected:', address);
      setPublicKey(address);
      setConnected(true);
      return;
    }

    try {
      setConnecting(true);
      console.log('[Solana] Connecting to Phantom...');
      
      const response = await provider.connect();
      const address = response.publicKey.toString();
      
      setPublicKey(address);
      setConnected(true);
      
      console.log('[Solana] ✅ Connected:', address);
    } catch (err: any) {
      console.error('[Solana] ❌ Connection error:', err);
      
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
    const provider = getProvider();
    
    if (provider) {
      try {
        console.log('[Solana] Disconnecting...');
        await provider.disconnect();
        console.log('[Solana] ✅ Disconnected');
      } catch (err) {
        console.error('[Solana] Disconnect error:', err);
      }
    }
    
    setPublicKey(null);
    setConnected(false);
    setError(null);
  };

  // Check if already connected on mount
  useEffect(() => {
    const provider = getProvider();
    
    if (!provider) {
      console.log('[Solana] Phantom wallet not installed');
      return;
    }

    // Check if already connected
    if (provider.publicKey) {
      const address = provider.publicKey.toString();
      console.log('[Solana] Already connected:', address);
      setPublicKey(address);
      setConnected(true);
    }

    // Listen for account changes
    const handleAccountChanged = (publicKey: any) => {
      console.log('[Solana] Account changed:', publicKey);
      
      if (publicKey) {
        const address = publicKey.toString();
        setPublicKey(address);
        setConnected(true);
      } else {
        setPublicKey(null);
        setConnected(false);
      }
    };

    // Listen for disconnect events
    const handleDisconnect = () => {
      console.log('[Solana] Wallet disconnected');
      setPublicKey(null);
      setConnected(false);
    };

    provider.on('accountChanged', handleAccountChanged);
    provider.on('disconnect', handleDisconnect);
    
    return () => {
      provider.off('accountChanged', handleAccountChanged);
      provider.off('disconnect', handleDisconnect);
    };
  }, []);

  const value: SolanaWalletContextType = {
    connected,
    publicKey,
    connecting,
    error,
    connect,
    disconnect,
    clearError,
  };

  return (
    <SolanaWalletContext.Provider value={value}>
      {children}
    </SolanaWalletContext.Provider>
  );
};