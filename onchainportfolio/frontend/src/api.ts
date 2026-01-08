// src/api.ts - UPDATED: Added Wallet Filtering Support

// Toggle this to switch between mock and real backend
export const MOCK_MODE = false;

// Backend URL - adjust if your backend runs on a different port
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
  async getBalances(address: string, chain: string = "aptos") {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return MOCK_RESPONSE.portfolio.wallets[0].data.balances;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}/balances?chain=${chain}`);
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
  async getPrices(symbols: string[], chain?: string) {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      return { APT: 7.12, USDC: 1.0, SOL: 126.04 };
    }

    try {
      const symbolsParam = symbols.join(",");
      const chainParam = chain ? `&chain=${chain}` : '';
      const res = await fetch(`${API_BASE_URL}/prices?symbols=${symbolsParam}${chainParam}`);
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
  async getPortfolio(address: string, chain: string = "aptos") {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_RESPONSE.portfolio.wallets[0].data;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/wallets/${address}/portfolio?chain=${chain}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch portfolio:", error);
      throw error;
    }
  },

  /**
   * Chat with AI about portfolio
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
  async getTransactions(
    address: string, 
    chain: string = "aptos",
    limit: number = 20
  ): Promise<Transaction[]> {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      return MOCK_TRANSACTIONS;
    }

    try {
      const res = await fetch(
        `${API_BASE_URL}/wallets/${address}/transactions?chain=${chain}&limit=${limit}`
      );
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
      chain?: string;
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
    
    if (params.chain) queryParams.append("chain", params.chain);
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
  async getTransactionDetail(
    address: string, 
    hash: string,
    chain: string = "aptos"
  ) {
    try {
      const res = await fetch(
        `${API_BASE_URL}/wallets/${address}/transactions/${hash}?chain=${chain}`,
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
  // Wallet Management Endpoints (Multi-Chain Support)
  // ============================================================

  /**
   * Get all wallets for the current user
   */
  async getWallets(): Promise<WalletResponse[]> {
    if (MOCK_MODE) {
      return [
        {
          id: "mock_wallet_1",
          _id: "mock_wallet_1", // ✅ Added for compatibility
          user_id: "mock123",
          address: "0x06c52...",
          chain: "aptos",
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
    type: "petra" | "phantom" | "manual" = "manual",
    isPrimary: boolean = false,
    chain: "aptos" | "solana" = "aptos"
  ): Promise<WalletResponse> {
    if (MOCK_MODE) {
      return {
        id: "mock_wallet_2",
        _id: "mock_wallet_2", // ✅ Added for compatibility
        user_id: "mock123",
        address,
        chain,
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
          chain,
          type,
          label,
          is_primary: isPrimary,
        }),
      });

      if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        
        let errorMessage = "Failed to add wallet";
        
        if (error.detail) {
          if (typeof error.detail === "string") {
            errorMessage = error.detail;
          } else if (Array.isArray(error.detail)) {
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
        _id: "mock_wallet_1", // ✅ Added for compatibility
        user_id: "mock123",
        address,
        chain: "aptos",
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
        _id: "mock_wallet_1", // ✅ Added for compatibility
        user_id: "mock123",
        address,
        chain: "aptos",
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
  
  // ============================================================
  // HISTORY ENDPOINTS
  // ============================================================

  /**
   * Get historical price data for a token
   */
  async getPriceHistory(
    symbol: string,
    days: number = 7,
    chain?: string
  ): Promise<PriceHistoryResponse> {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      const now = Date.now() / 1000;
      const prices = Array.from({ length: days * 24 }, (_, i) => ({
        timestamp: now - (days * 24 - i) * 3600,
        price: 120 + Math.random() * 10
      }));
      return {
        symbol,
        prices,
        current_price: 125.67,
        change_24h: 2.34,
        change_percent: 1.90,
        period_change: 5.67,
        period_change_percent: 4.72,
        data_points: prices.length
      };
    }

    try {
      const chainParam = chain ? `&chain=${chain}` : '';
      const res = await fetch(
        `${API_BASE_URL}/history/prices/history/${symbol}?days=${days}${chainParam}`,
        { headers: getAuthHeaders() }
      );
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch price history:", error);
      throw error;
    }
  },

  /**
   * Get portfolio value history (basic version)
   */
  async getPortfolioHistory(days: number = 7): Promise<PortfolioHistoryResponse> {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const now = Date.now() / 1000;
      const values = Array.from({ length: days * 24 }, (_, i) => ({
        timestamp: now - (days * 24 - i) * 3600,
        value: 300 + Math.random() * 50
      }));
      return {
        values,
        current_value: 333.61,
        period_change: -7.10,
        period_change_percent: -2.08,
        data_points: values.length,
        metadata: {
          earliest_wallet_date: "2024-12-18",
          wallet_age_days: 9,
          requested_days: days,
          actual_days_shown: 9,
          scope: "all_wallets",
          scope_label: "Complete Portfolio",
          disclaimer: "Portfolio values are approximations based on current holdings."
        }
      };
    }

    try {
      const res = await fetch(
        `${API_BASE_URL}/history/portfolio/history?days=${days}`,
        {
          method: "POST",
          headers: getAuthHeaders()
        }
      );
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch portfolio history:", error);
      throw error;
    }
  },

  /**
   * ✅ UPDATED: Get detailed portfolio history with wallet filtering support
   */
  async getDetailedPortfolioHistory(
    days: number = 7,
    walletId: string | null = null  // ✅ NEW: Optional wallet ID for filtering
  ): Promise<DetailedPortfolioHistoryResponse> {
    if (MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      const now = Date.now() / 1000;
      const values = Array.from({ length: days * 24 }, (_, i) => ({
        timestamp: now - (days * 24 - i) * 3600,
        value: 300 + Math.random() * 50
      }));
      
      return {
        values,
        current_value: 333.61,
        period_change: -7.10,
        period_change_percent: -2.08,
        data_points: values.length,
        wallet_events: [],
        wallet_breakdown: [
          {
            wallet_id: "wallet1",
            label: "Main Wallet",
            chain: "aptos",
            current_value: 333.61,
            percentage: 100,
            created_at: "2024-12-18",
            age_days: 9
          }
        ],
        metadata: {
          earliest_wallet_date: "2024-12-18",
          wallet_age_days: 9,
          requested_days: days,
          actual_days_shown: 9,
          scope: walletId || "all_wallets",
          scope_label: walletId ? "Specific Wallet" : "Complete Portfolio",
          disclaimer: "Portfolio values based on current holdings × historical prices."
        }
      };
    }

    try {
      // ✅ NEW: Build query params with optional wallet_id
      const params = new URLSearchParams({
        days: days.toString()
      });
      
      if (walletId) {
        params.append('wallet_id', walletId);
      }
      
      const res = await fetch(
        `${API_BASE_URL}/history/portfolio/detailed?${params.toString()}`,
        {
          method: "POST",
          headers: getAuthHeaders()
        }
      );
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    } catch (error) {
      console.error("Failed to fetch detailed portfolio history:", error);
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

export interface WalletInfo {
  address: string;
  name: string;
  is_primary: boolean;
  added_at?: string;
}

export interface WalletResponse {
  id: string;
  _id?: string;  // ✅ ADDED: MongoDB ID (alias for id)
  user_id: string;
  address: string;
  chain: "aptos" | "solana";
  type: "petra" | "phantom" | "manual";
  label: string;
  is_primary: boolean;
  created_at: string;
}

// Chat Types
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

export interface ChatResponse {
  answer: string;
  portfolio: AggregatedPortfolio;
  wallet_results: WalletPortfolioResult[];
  scope_used: string;
}

// History Types
export interface PricePoint {
  timestamp: number;
  price: number;
}

export interface PriceHistoryResponse {
  symbol: string;
  prices: PricePoint[];
  current_price: number;
  change_24h: number;
  change_percent: number;
  period_change: number;
  period_change_percent: number;
  data_points: number;
}

export interface PortfolioValuePoint {
  timestamp: number;
  value: number;
}

export interface PortfolioHistoryMetadata {
  earliest_wallet_date: string;
  wallet_age_days: number;
  requested_days: number;
  actual_days_shown: number;
  scope: string;  // ✅ ADDED
  scope_label: string;  // ✅ ADDED
  disclaimer: string;
}

export interface PortfolioHistoryResponse {
  values: PortfolioValuePoint[];
  current_value: number;
  period_change: number;
  period_change_percent: number;
  data_points: number;
  metadata: PortfolioHistoryMetadata;
}

// Enhanced portfolio history types
export interface WalletEvent {
  date: string;
  timestamp: number;
  type: string;
  wallet_id: string;
  wallet_label: string;
  wallet_chain: string;
  value_before: number;
  value_after: number;
  impact: number;
}

export interface WalletBreakdown {
  wallet_id: string;
  label: string;
  chain: string;
  current_value: number;
  percentage: number;
  created_at: string;
  age_days: number;
}

export interface DetailedPortfolioHistoryResponse {
  values: PortfolioValuePoint[];
  current_value: number;
  period_change: number;
  period_change_percent: number;
  data_points: number;
  wallet_events: WalletEvent[];
  wallet_breakdown: WalletBreakdown[];
  metadata: PortfolioHistoryMetadata;
}