// src/context/EVMWalletProvider.tsx - EVM Wallet Support (MetaMask, Coinbase, etc.)
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { ReactNode } from 'react';

// EVM Chain configuration
export const EVM_CHAINS = {
  ethereum: { chainId: 1, name: 'Ethereum', symbol: 'ETH', rpcUrl: 'https://eth.llamarpc.com' },
  polygon: { chainId: 137, name: 'Polygon', symbol: 'MATIC', rpcUrl: 'https://polygon.llamarpc.com' },
  base: { chainId: 8453, name: 'Base', symbol: 'ETH', rpcUrl: 'https://mainnet.base.org' },
  // Testnets
  ethereum_sepolia: { chainId: 11155111, name: 'Sepolia', symbol: 'ETH', rpcUrl: 'https://rpc.sepolia.org' },
  polygon_amoy: { chainId: 80002, name: 'Polygon Amoy', symbol: 'MATIC', rpcUrl: 'https://rpc-amoy.polygon.technology' },
  base_sepolia: { chainId: 84532, name: 'Base Sepolia', symbol: 'ETH', rpcUrl: 'https://sepolia.base.org' },
} as const;

// Chain ID to chain name mapping
export const CHAIN_ID_TO_NAME: Record<number, string> = {
  1: 'ethereum',
  137: 'polygon',
  8453: 'base',
  11155111: 'ethereum_sepolia',
  80002: 'polygon_amoy',
  84532: 'base_sepolia',
};

// EIP-1193 Provider interface
interface EthereumProvider {
  isMetaMask?: boolean;
  isCoinbaseWallet?: boolean;
  isRabby?: boolean;
  request: (args: { method: string; params?: any[] }) => Promise<any>;
  on: (event: string, callback: (...args: any[]) => void) => void;
  removeListener: (event: string, callback: (...args: any[]) => void) => void;
  selectedAddress?: string | null;
  chainId?: string;
}

interface EVMWalletContextType {
  connected: boolean;
  address: string | null;
  chainId: number | null;
  chainName: string | null;
  connecting: boolean;
  error: string | null;
  walletType: 'metamask' | 'coinbase' | 'rabby' | 'unknown' | null;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  switchChain: (chainId: number) => Promise<void>;
  clearError: () => void;
  isInstalled: boolean;
}

const EVMWalletContext = createContext<EVMWalletContextType>({
  connected: false,
  address: null,
  chainId: null,
  chainName: null,
  connecting: false,
  error: null,
  walletType: null,
  connect: async () => {},
  disconnect: async () => {},
  switchChain: async () => {},
  clearError: () => {},
  isInstalled: false,
});

export const useEVMWallet = () => useContext(EVMWalletContext);

interface Props {
  children: ReactNode;
}

export const EVMWalletProvider: React.FC<Props> = ({ children }) => {
  const [connected, setConnected] = useState(false);
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [walletType, setWalletType] = useState<'metamask' | 'coinbase' | 'rabby' | 'unknown' | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  // Get EVM provider - prioritize MetaMask over Phantom for EVM connections
  const getProvider = useCallback((): EthereumProvider | null => {
    if (typeof window === 'undefined') {
      return null;
    }

    const ethereum = (window as any).ethereum;

    // Check if there are multiple providers (EIP-5749 / providers array)
    if (ethereum?.providers && Array.isArray(ethereum.providers)) {
      // Find MetaMask provider first
      const metamask = ethereum.providers.find((p: any) => p.isMetaMask && !p.isPhantom);
      if (metamask) {
        console.log('[EVM] Found MetaMask in providers array');
        return metamask;
      }
      // Fall back to first non-Phantom provider
      const nonPhantom = ethereum.providers.find((p: any) => !p.isPhantom);
      if (nonPhantom) {
        return nonPhantom;
      }
    }

    // Single provider - check if it's MetaMask (not Phantom pretending to be MetaMask)
    if (ethereum) {
      // If it's Phantom's EVM provider, skip it (we handle that separately in SolanaWalletProvider)
      if (ethereum.isPhantom && !ethereum.isMetaMask) {
        console.log('[EVM] Skipping Phantom-only EVM provider');
        return null;
      }

      // MetaMask or other EVM wallet
      if (ethereum.isMetaMask || ethereum.isCoinbaseWallet || ethereum.isRabby) {
        console.log('[EVM] Found EVM provider:', {
          isMetaMask: ethereum.isMetaMask,
          isCoinbase: ethereum.isCoinbaseWallet,
          isPhantom: ethereum.isPhantom
        });
        return ethereum;
      }

      // Generic fallback
      return ethereum;
    }

    return null;
  }, []);

  // Detect wallet type - be careful with Phantom which can set isMetaMask
  const detectWalletType = useCallback((provider: EthereumProvider): 'metamask' | 'coinbase' | 'rabby' | 'unknown' => {
    // Phantom sometimes sets isMetaMask=true, so check isPhantom first
    if ((provider as any).isPhantom) return 'unknown'; // Phantom EVM handled separately
    if (provider.isMetaMask) return 'metamask';
    if (provider.isCoinbaseWallet) return 'coinbase';
    if (provider.isRabby) return 'rabby';
    return 'unknown';
  }, []);

  // Get chain name from chain ID
  const getChainName = useCallback((id: number | null): string | null => {
    if (!id) return null;
    return CHAIN_ID_TO_NAME[id] || `chain-${id}`;
  }, []);

  // Clear error
  const clearError = useCallback(() => setError(null), []);

  // Connect to EVM wallet
  const connect = useCallback(async () => {
    setError(null);
    const provider = getProvider();

    if (!provider) {
      const errorMsg = "No EVM wallet found. Please install MetaMask or another EVM wallet.";
      setError(errorMsg);
      console.error('[EVM]', errorMsg);
      window.open('https://metamask.io/', '_blank');
      throw new Error(errorMsg);
    }

    if (connecting) {
      console.log('[EVM] Already connecting, please wait...');
      return;
    }

    try {
      setConnecting(true);
      console.log('[EVM] Connecting to wallet...');

      // Request accounts
      const accounts = await provider.request({ method: 'eth_requestAccounts' });

      if (accounts && accounts.length > 0) {
        const connectedAddress = accounts[0];
        const chainIdHex = await provider.request({ method: 'eth_chainId' });
        const connectedChainId = parseInt(chainIdHex, 16);

        setAddress(connectedAddress);
        setChainId(connectedChainId);
        setConnected(true);
        setWalletType(detectWalletType(provider));

        console.log('[EVM] Connected:', connectedAddress, 'Chain:', connectedChainId);
      }
    } catch (err: any) {
      console.error('[EVM] Connection error:', err);

      let errorMessage = "Failed to connect to EVM wallet";

      if (err?.code === 4001) {
        errorMessage = "Connection rejected. Please approve the connection in your wallet.";
      } else if (err?.code === -32002) {
        errorMessage = "Connection request already pending. Please check your wallet.";
      } else if (err?.message?.includes('User rejected')) {
        errorMessage = "You rejected the connection request.";
      } else if (err?.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setConnecting(false);
    }
  }, [connecting, getProvider, detectWalletType]);

  // Disconnect wallet
  const disconnect = useCallback(async () => {
    console.log('[EVM] Disconnecting...');

    // Note: Most EVM wallets don't have a programmatic disconnect
    // We just clear our local state
    setAddress(null);
    setChainId(null);
    setConnected(false);
    setWalletType(null);
    setError(null);

    console.log('[EVM] Disconnected');
  }, []);

  // Switch chain
  const switchChain = useCallback(async (targetChainId: number) => {
    const provider = getProvider();

    if (!provider) {
      throw new Error("No EVM wallet found");
    }

    const chainIdHex = `0x${targetChainId.toString(16)}`;

    try {
      console.log('[EVM] Switching to chain:', targetChainId);

      await provider.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: chainIdHex }],
      });

      setChainId(targetChainId);
      console.log('[EVM] Switched to chain:', targetChainId);
    } catch (err: any) {
      // Chain not added to wallet - try to add it
      if (err?.code === 4902) {
        const chainName = CHAIN_ID_TO_NAME[targetChainId];
        const chainConfig = Object.values(EVM_CHAINS).find(c => c.chainId === targetChainId);

        if (chainConfig) {
          try {
            await provider.request({
              method: 'wallet_addEthereumChain',
              params: [{
                chainId: chainIdHex,
                chainName: chainConfig.name,
                nativeCurrency: {
                  name: chainConfig.symbol,
                  symbol: chainConfig.symbol,
                  decimals: 18,
                },
                rpcUrls: [chainConfig.rpcUrl],
              }],
            });

            setChainId(targetChainId);
            console.log('[EVM] Added and switched to chain:', targetChainId);
          } catch (addErr) {
            console.error('[EVM] Failed to add chain:', addErr);
            throw addErr;
          }
        }
      } else {
        console.error('[EVM] Failed to switch chain:', err);
        throw err;
      }
    }
  }, [getProvider]);

  // Check if already connected on mount
  useEffect(() => {
    const provider = getProvider();

    if (!provider) {
      console.log('[EVM] No EVM wallet installed');
      setIsInstalled(false);
      return;
    }

    setIsInstalled(true);
    setWalletType(detectWalletType(provider));
    console.log('[EVM] Detected wallet:', detectWalletType(provider));

    // Check if already connected
    const checkConnection = async () => {
      try {
        const accounts = await provider.request({ method: 'eth_accounts' });

        if (accounts && accounts.length > 0) {
          const connectedAddress = accounts[0];
          const chainIdHex = await provider.request({ method: 'eth_chainId' });
          const connectedChainId = parseInt(chainIdHex, 16);

          console.log('[EVM] Already connected:', connectedAddress, 'Chain:', connectedChainId);

          setAddress(connectedAddress);
          setChainId(connectedChainId);
          setConnected(true);
        }
      } catch (err) {
        console.error('[EVM] Error checking connection:', err);
      }
    };

    checkConnection();

    // Listen for account changes
    const handleAccountsChanged = (accounts: string[]) => {
      console.log('[EVM] Accounts changed:', accounts);

      if (accounts.length > 0) {
        setAddress(accounts[0]);
        setConnected(true);
      } else {
        setAddress(null);
        setConnected(false);
      }
    };

    // Listen for chain changes
    const handleChainChanged = (chainIdHex: string) => {
      const newChainId = parseInt(chainIdHex, 16);
      console.log('[EVM] Chain changed:', newChainId);
      setChainId(newChainId);
    };

    // Listen for disconnect
    const handleDisconnect = () => {
      console.log('[EVM] Wallet disconnected');
      setAddress(null);
      setChainId(null);
      setConnected(false);
    };

    provider.on('accountsChanged', handleAccountsChanged);
    provider.on('chainChanged', handleChainChanged);
    provider.on('disconnect', handleDisconnect);

    return () => {
      provider.removeListener('accountsChanged', handleAccountsChanged);
      provider.removeListener('chainChanged', handleChainChanged);
      provider.removeListener('disconnect', handleDisconnect);
    };
  }, [getProvider, detectWalletType]);

  const value: EVMWalletContextType = {
    connected,
    address,
    chainId,
    chainName: getChainName(chainId),
    connecting,
    error,
    walletType,
    connect,
    disconnect,
    switchChain,
    clearError,
    isInstalled,
  };

  return (
    <EVMWalletContext.Provider value={value}>
      {children}
    </EVMWalletContext.Provider>
  );
};
