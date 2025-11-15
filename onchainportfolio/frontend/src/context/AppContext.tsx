// src/context/AppContext.tsx
import React, {
  createContext,
  useContext,
  useState,
  useEffect,
} from "react";
import type { ReactNode } from "react";
import { api } from "../api";

export type Theme = "light" | "dark";

export interface WalletState {
  connected: boolean;
  address: string | null;
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
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  portfolioData: any;
  setPortfolioData: (data: any) => void;
  wallet: WalletState & { connect: () => void; disconnect: () => void };
  theme: Theme;
  toggleTheme: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// ---- hooks inside context ----
const useThemeInternal = () => {
  const [theme, setTheme] = useState<Theme>("dark"); // default dark

  const toggleTheme = () =>
    setTheme((prev) => (prev === "light" ? "dark" : "light"));

  return { theme, toggleTheme };
};

const useSimulatedWallet = () => {
  const [wallet, setWallet] = useState<WalletState>({
    connected: false,
    address: null,
  });

  const connect = () => {
    const mockAddress =
      "0x" +
      Math.random().toString(16).slice(2, 66).padEnd(64, "0");
    setWallet({ connected: true, address: mockAddress });
  };

  const disconnect = () => {
    setWallet({ connected: false, address: null });
  };

  return { ...wallet, connect, disconnect };
};

// ---- public hooks / provider ----
export const useAppContext = () => {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useAppContext must be used within AppProvider");
  }
  return ctx;
};

export const AppProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [manualAddress, setManualAddress] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [portfolioData, setPortfolioData] = useState<any>(null);
  const wallet = useSimulatedWallet();
  const { theme, toggleTheme } = useThemeInternal();

  const addMessage = (msg: ChatMessage) => {
    setMessages((prev) => [...prev, msg]);
    if (msg.data) {
      setPortfolioData(msg.data);
    }
  };

  useEffect(() => {
    api.health().then((res) =>
      console.log("Backend health:", res)
    );
  }, []);

  const value: AppContextType = {
    messages,
    addMessage,
    manualAddress,
    setManualAddress,
    isLoading,
    setIsLoading,
    portfolioData,
    setPortfolioData,
    wallet,
    theme,
    toggleTheme,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};
