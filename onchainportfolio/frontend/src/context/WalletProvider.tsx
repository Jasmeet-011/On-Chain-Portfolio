// src/context/WalletProvider.tsx
import { AptosWalletAdapterProvider } from "@aptos-labs/wallet-adapter-react";
import { Network } from "@aptos-labs/ts-sdk";
import type { PropsWithChildren } from "react";

export const WalletProvider = ({ children }: PropsWithChildren) => {
  return (
    <AptosWalletAdapterProvider
      autoConnect={false}  // ✅ CHANGED: Don't auto-connect
      dappConfig={{
        network: Network.TESTNET, // Change to MAINNET for production
        // Optional: Add your app name
        // aptosConnectDappId: "your-app-name"
      }}
      onError={(error) => {
        console.error("[WalletAdapter] Error:", error);
        
        // ✅ ADDED: Better error handling
        if (error.message?.includes('already connected')) {
          console.log("[WalletAdapter] Wallet already connected, will use existing connection");
        }
      }}
    >
      {children}
    </AptosWalletAdapterProvider>
  );
};