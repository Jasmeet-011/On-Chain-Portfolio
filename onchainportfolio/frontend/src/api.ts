// src/api.ts

// Toggle this to switch between mock and real backend
export const MOCK_MODE = false;

// Backend URL - adjust if your backend runs on a different port
// const API_BASE_URL = "http://localhost:8000/v1";
// const AUTH_BASE_URL = "http://localhost:8000/auth";
const API_ORIGIN = import.meta.env.VITE_API_ORIGIN || "http://localhost:8000";

const API_BASE_URL = `${API_ORIGIN}/v1`;
const AUTH_BASE_URL = `${API_ORIGIN}/auth`;


// ============================================================
// Auth Token Helper
// ============================================================

/**
 * Get the stored auth token from localStorage
 */
function getAuthToken(): string | null {
  const userStr = localStorage.getItem("user");
  if (!userStr) return null;
  
  try {
    const user = JSON.parse(userStr);
    return user.access_token || null;
  } catch {
    return null;
  }
}

/**
 * Get auth headers with Bearer token
 */
function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// Mock data (keep for testing)
const MOCK_RESPONSE = {
  answer: "You hold 12.345 APT and 150.00 USDC. You also have 2 NFTs in your wallet.",
  portfolio: {
    total_usd_value: 87.91,
    wallets: [
      {
        address: "0x...",
        data: {
          balances: [
            {
              symbol: "APT",
              address: "0x1::aptos_coin::AptosCoin",
              decimals: 8,
              raw: "1234500000",
              amount: 12.345,
              usd_price: 7.12,
              usd_value: 87.91,
            },
          ],
          total_usd_value: 87.91,
        },
      },
    ],
  },
};

const MOCK_TRANSACTIONS = [
  {
    hash: "0xabc123def456...",
    version: "123456",
    success: true,
    timestamp: new Date().getTime() * 1000 + "",
    gas_used: 15,
    sender: "0xe037e246dfd66661c6162e0dff968d64753eea38af08b1da2695e8464dbfce6a",
    sequence_number: 1,
    type: "Transfer",
    function: "0x1::aptos_account::transfer",
  },
];

// API Client
export const api = {
  /**
   * Health check endpoint
   */
  async health() {
    if (MOCK_MODE) return { status: "ok (mock)" };
    
    try {
      const res = await fetch(`${API_BASE_URL.replace('/v1', '')}/health`);
      return res.json();
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  },

  /**
   * Get token balances for a wallet
   */
  async getBalances(address: string) {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return MOCK_RESPONSE.portfolio.wallets[0].data.balances;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}/balances`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch balances:", error);
      throw error;
    }
  },

  /**
   * Get token prices
   */
  async getPrices(symbols: string[]) {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      return { APT: 7.12, USDC: 1.0 };
    }

    try {
      const symbolsParam = symbols.join(",");
      const res = await fetch(`${API_BASE_URL}/prices?symbols=${symbolsParam}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      return data.prices;
    } catch (error) {
      console.error("Failed to fetch prices:", error);
      throw error;
    }
  },

  /**
   * Get complete portfolio for a wallet
   */
  async getPortfolio(address: string) {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_RESPONSE.portfolio.wallets[0].data;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}/portfolio`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch portfolio:", error);
      throw error;
    }
  },

  /**
   * Chat with AI about portfolio
   * NEW: Now supports scope parameter
   */
  async chat(question: string, scope: string = "all") {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return MOCK_RESPONSE;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          question: question,
          scope: scope,
        }),
      });
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Chat API failed:", error);
      throw error;
    }
  },

  /**
   * Get transaction history for a wallet
   */
  async getTransactions(address: string, limit: number = 20): Promise<Transaction[]> {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return MOCK_TRANSACTIONS;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}/transactions?limit=${limit}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch transactions:", error);
      throw error;
    }
  },

  /**
   * Get transactions with filters and pagination
   */
  async getTransactionsFiltered(
    address: string,
    params: {
      limit?: number;
      offset?: number;
      type_filter?: string;
      status_filter?: string;
      search?: string;
      date_from?: string;
      date_to?: string;
    }
  ) {
    const queryParams = new URLSearchParams();
    
    if (params.limit) queryParams.append("limit", params.limit.toString());
    if (params.offset) queryParams.append("offset", params.offset.toString());
    if (params.type_filter) queryParams.append("type_filter", params.type_filter);
    if (params.status_filter) queryParams.append("status_filter", params.status_filter);
    if (params.search) queryParams.append("search", params.search);
    if (params.date_from) queryParams.append("date_from", params.date_from);
    if (params.date_to) queryParams.append("date_to", params.date_to);

    try {
      const res = await fetch(
        `${API_BASE_URL}/wallets/${address}/transactions?${queryParams}`,
        { headers: getAuthHeaders() }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch transactions:", error);
      throw error;
    }
  },

  /**
   * Get transaction detail
   */
  async getTransactionDetail(address: string, hash: string) {
    try {
      const res = await fetch(
        `${API_BASE_URL}/wallets/${address}/transactions/${hash}`,
        { headers: getAuthHeaders() }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch transaction detail:", error);
      throw error;
    }
  },

  // ============================================================
  // Authentication Endpoints
  // ============================================================

  /**
   * Sign up a new user
   */
  async signup(name: string, email: string, password: string): Promise<AuthResponse> {
    if (MOCK_MODE) {
      return {
        user: {
          id: "mock123",
          name,
          email,
          wallet_address: null,
          wallets: [],
        },
        access_token: "mock_token_123",
        token_type: "bearer",
      };
    }

    try {
      const res = await fetch(`${AUTH_BASE_URL}/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Signup failed");
      }

      return res.json();
    } catch (error) {
      console.error("Signup failed:", error);
      throw error;
    }
  },

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    if (MOCK_MODE) {
      return {
        user: {
          id: "mock123",
          name: "Mock User",
          email,
          wallet_address: null,
          wallets: [],
        },
        access_token: "mock_token_123",
        token_type: "bearer",
      };
    }

    try {
      const res = await fetch(`${AUTH_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Login failed");
      }

      return res.json();
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<UserResponse> {
    if (MOCK_MODE) {
      return {
        id: "mock123",
        name: "Mock User",
        email: "mock@example.com",
        wallet_address: null,
        wallets: [],
      };
    }

    try {
      const res = await fetch(`${AUTH_BASE_URL}/me`, {
        headers: getAuthHeaders(),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to get current user:", error);
      throw error;
    }
  },

  // ============================================================
  // NEW: Wallet Management Endpoints (Using /v1/wallets)
  // ============================================================

  /**
   * Get all wallets for the current user
   */
  async getWallets(): Promise<WalletResponse[]> {
    if (MOCK_MODE) {
      return [
        {
          id: "mock_wallet_1",
          user_id: "mock123",
          address: "0x06c52...",
          type: "manual",
          label: "Main Wallet",
          is_primary: true,
          created_at: new Date().toISOString(),
        },
      ];
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets`, {
        headers: getAuthHeaders(),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      
      // Backend returns { wallets: [], total: N, primary: {...} }
      return data.wallets || [];
    } catch (error) {
      console.error("Failed to get wallets:", error);
      throw error;
    }
  },

  /**
   * Add a new wallet
   */
  async addWallet(
    address: string,
    label: string = "Wallet",
    type: "petra" | "manual" = "manual",
    isPrimary: boolean = false
  ): Promise<WalletResponse> {
    if (MOCK_MODE) {
      return {
        id: "mock_wallet_2",
        user_id: "mock123",
        address,
        type,
        label,
        is_primary: isPrimary,
        created_at: new Date().toISOString(),
      };
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          address,
          type,
          label,
          is_primary: isPrimary,
        }),
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        
        // Parse backend validation errors
        let errorMessage = "Failed to add wallet";
        
        if (error.detail) {
          if (typeof error.detail === "string") {
            errorMessage = error.detail;
          } else if (Array.isArray(error.detail)) {
            // FastAPI validation errors
            errorMessage = error.detail.map((e: any) => e.msg).join(", ");
          }
        }
        
        throw new Error(errorMessage);
      }

      return res.json();
    } catch (error: any) {
      console.error("Failed to add wallet:", error);
      throw error;
    }
  },

  /**
   * Remove a specific wallet
   */
  async removeWallet(address: string): Promise<void> {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (error) {
      console.error("Failed to remove wallet:", error);
      throw error;
    }
  },

  /**
   * Update wallet label
   */
  async updateWalletLabel(address: string, label: string): Promise<WalletResponse> {
    if (MOCK_MODE) {
      return {
        id: "mock_wallet_1",
        user_id: "mock123",
        address,
        type: "manual",
        label,
        is_primary: true,
        created_at: new Date().toISOString(),
      };
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}/label`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify({ label }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to update wallet label:", error);
      throw error;
    }
  },

  /**
   * Set primary wallet
   */
  async setPrimaryWallet(address: string): Promise<WalletResponse> {
    if (MOCK_MODE) {
      return {
        id: "mock_wallet_1",
        user_id: "mock123",
        address,
        type: "manual",
        label: "Wallet",
        is_primary: true,
        created_at: new Date().toISOString(),
      };
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/primary`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ address }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to set primary wallet:", error);
      throw error;
    }
  },
};

// ============================================================
// Type Definitions
// ============================================================

export interface TokenBalance {
  symbol: string;
  address: string;
  decimals: number;
  raw: string;
  amount: number;
  usd_price?: number;
  usd_value?: number;
}

export interface Portfolio {
  address: string;
  balances: TokenBalance[];
  total_usd_value: number;
}

export interface Transaction {
  hash: string;
  version: string;
  success: boolean;
  timestamp: string;
  gas_used: number;
  sender: string;
  sequence_number: number;
  type: string;
  function?: string;
}

// Auth types
export interface UserResponse {
  id: string;
  name: string;
  email: string;
  wallet_address?: string | null;
  wallets: WalletInfo[];
}

export interface AuthResponse {
  user: UserResponse;
  access_token: string;
  token_type: string;
}

// OLD Wallet types (for backward compatibility with auth endpoints)
export interface WalletInfo {
  address: string;
  name: string;
  is_primary: boolean;
  added_at?: string;
}

// NEW: Backend wallet response (from /v1/wallets)
export interface WalletResponse {
  id: string;
  user_id: string;
  address: string;
  type: "petra" | "manual";
  label: string;
  is_primary: boolean;
  created_at: string;
}

// ============================================================
// Phase 3: Enhanced Chat Types
// ============================================================

export interface WalletPortfolioResult {
  address: string;
  label: string;
  success: boolean;
  error: string | null;
  data: any | null;
}

export interface TokenAggregate {
  symbol: string;
  total_amount: number;
  total_usd_value: number;
  wallet_count: number;
}

export interface AggregatedPortfolio {
  total_usd_value: number;
  total_wallets: number;
  successful_wallets: number;
  failed_wallets: number;
  by_token: TokenAggregate[];
  wallets: Array<{
    address: string;
    label: string;
    data: any;
  }>;
}

// ✅ SINGLE ChatResponse interface (the new one)
export interface ChatResponse {
  answer: string;
  portfolio: AggregatedPortfolio;
  wallet_results: WalletPortfolioResult[];
  scope_used: string;
}