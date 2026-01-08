// src/components/CreateAlertModal.tsx - BEST VERSION
import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import type { ExtendedWalletInfo } from "../context/AppContext";

interface CreateAlertModalProps {
  onClose: () => void;
  onCreate: (alertData: any) => Promise<void>;
  wallets: ExtendedWalletInfo[];
}

const CreateAlertModal: React.FC<CreateAlertModalProps> = ({
  onClose,
  onCreate,
  wallets,
}) => {
  const { theme, portfolioData } = useAppContext();
  
  const [formData, setFormData] = useState({
    token_symbol: "",
    target_price: "",
    condition: "above" as "above" | "below",
    wallet_address: "",
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableTokens, setAvailableTokens] = useState<string[]>([]);
  const [loadingTokens, setLoadingTokens] = useState(true);

  // Popular tokens for quick selection
  const popularTokens = [
    { symbol: "SOL", name: "Solana" },
    { symbol: "APT", name: "Aptos" },
    { symbol: "BTC", name: "Bitcoin" },
    { symbol: "ETH", name: "Ethereum" },
    { symbol: "USDC", name: "USD Coin" },
  ];

  // Get auth token
  const getAuthToken = (): string => {
    const userStr = localStorage.getItem("user");
    if (!userStr) return "";
    try {
      const user = JSON.parse(userStr);
      return user.access_token || "";
    } catch {
      return "";
    }
  };

  // Fetch tokens from all wallets
  useEffect(() => {
    const fetchTokens = async () => {
      setLoadingTokens(true);
      
      try {
        // Try to get from portfolioData first (fastest)
        if (portfolioData?.balances && portfolioData.balances.length > 0) {
          const tokens = Array.from(
            new Set(portfolioData.balances.map((b: any) => b.symbol))
          ).filter(Boolean);
          
          setAvailableTokens(tokens as string[]);
          
          // Auto-select first token
          if (tokens.length > 0 && !formData.token_symbol) {
            setFormData(prev => ({ ...prev, token_symbol: tokens[0] as string }));
          }
          
          setLoadingTokens(false);
          return;
        }

        // If no portfolioData, fetch from all wallets
        if (wallets.length === 0) {
          setAvailableTokens([]);
          setLoadingTokens(false);
          return;
        }

        const allTokens = new Set<string>();
        
        // Fetch portfolio for each wallet
        for (const wallet of wallets) {
          try {
            const response = await fetch(
              `http://localhost:8000/v1/wallets/${wallet.address}/portfolio?chain=${wallet.chain}`,
              {
                headers: {
                  "Authorization": `Bearer ${getAuthToken()}`,
                },
              }
            );

            if (response.ok) {
              const data = await response.json();
              if (data.balances) {
                data.balances.forEach((balance: any) => {
                  if (balance.symbol) {
                    allTokens.add(balance.symbol);
                  }
                });
              }
            }
          } catch (err) {
            console.error(`Failed to fetch tokens for wallet ${wallet.address}:`, err);
          }
        }

        const tokens = Array.from(allTokens).sort();
        setAvailableTokens(tokens);
        
        // Auto-select first token
        if (tokens.length > 0 && !formData.token_symbol) {
          setFormData(prev => ({ ...prev, token_symbol: tokens[0] }));
        }
      } catch (err) {
        console.error("Failed to fetch tokens:", err);
      } finally {
        setLoadingTokens(false);
      }
    };

    fetchTokens();
  }, [wallets, portfolioData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.token_symbol) {
      setError("Please select a token");
      return;
    }

    if (!formData.target_price || parseFloat(formData.target_price) <= 0) {
      setError("Please enter a valid target price");
      return;
    }

    setLoading(true);

    try {
      await onCreate({
        token_symbol: formData.token_symbol.toUpperCase(),
        target_price: parseFloat(formData.target_price),
        condition: formData.condition,
        wallet_address: formData.wallet_address || undefined,
      });
    } catch (err: any) {
      setError(err.message || "Failed to create alert");
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`relative w-full max-w-lg rounded-xl shadow-2xl ${
          theme === "dark"
            ? "bg-slate-800 border border-slate-700"
            : "bg-white border border-slate-200"
        }`}
      >
        {/* Header */}
        <div className={`px-6 py-4 border-b ${
          theme === "dark" ? "border-slate-700" : "border-slate-200"
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className={`text-xl font-bold ${
                theme === "dark" ? "text-white" : "text-slate-900"
              }`}>
                Create Price Alert
              </h3>
              <p className={`text-sm mt-1 ${
                theme === "dark" ? "text-slate-400" : "text-slate-600"
              }`}>
                Get notified when a token reaches your target price
              </p>
            </div>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${
                theme === "dark"
                  ? "hover:bg-slate-700 text-slate-400"
                  : "hover:bg-slate-100 text-slate-600"
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Error Message */}
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Token Selection */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              theme === "dark" ? "text-slate-300" : "text-slate-700"
            }`}>
              Token
            </label>
            
            {/* Popular Token Quick Select */}
            <div className="grid grid-cols-5 gap-2 mb-2">
              {popularTokens.map((token) => (
                <button
                  key={token.symbol}
                  type="button"
                  onClick={() => handleChange("token_symbol", token.symbol)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    formData.token_symbol === token.symbol
                      ? "bg-blue-600 text-white"
                      : theme === "dark"
                      ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  {token.symbol}
                </button>
              ))}
            </div>

            {/* Token Dropdown (from portfolio) */}
            {loadingTokens ? (
              <div className={`px-4 py-3 rounded-lg border text-sm flex items-center gap-2 ${
                theme === "dark"
                  ? "bg-slate-900 border-slate-700 text-slate-400"
                  : "bg-slate-50 border-slate-200 text-slate-600"
              }`}>
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                Loading your tokens...
              </div>
            ) : availableTokens.length > 0 ? (
              <select
                value={formData.token_symbol}
                onChange={(e) => handleChange("token_symbol", e.target.value)}
                className={`w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  theme === "dark"
                    ? "bg-slate-900 border-slate-700 text-white"
                    : "bg-white border-slate-300 text-slate-900"
                }`}
              >
                <option value="">Select from your tokens</option>
                {availableTokens.map((token) => (
                  <option key={token} value={token}>
                    {token}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={formData.token_symbol}
                onChange={(e) => handleChange("token_symbol", e.target.value.toUpperCase())}
                placeholder={wallets.length === 0 ? "Connect wallet first" : "Or enter token symbol"}
                disabled={wallets.length === 0}
                className={`w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  theme === "dark"
                    ? "bg-slate-900 border-slate-700 text-white placeholder-slate-500"
                    : "bg-white border-slate-300 text-slate-900 placeholder-slate-400"
                } disabled:opacity-50`}
              />
            )}
          </div>

          {/* Condition */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              theme === "dark" ? "text-slate-300" : "text-slate-700"
            }`}>
              Alert When Price Goes
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleChange("condition", "above")}
                className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                  formData.condition === "above"
                    ? "bg-green-600 text-white"
                    : theme === "dark"
                    ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                ⬆️ Above
              </button>
              <button
                type="button"
                onClick={() => handleChange("condition", "below")}
                className={`px-4 py-3 rounded-lg font-medium transition-colors ${
                  formData.condition === "below"
                    ? "bg-red-600 text-white"
                    : theme === "dark"
                    ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                ⬇️ Below
              </button>
            </div>
          </div>

          {/* Target Price */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              theme === "dark" ? "text-slate-300" : "text-slate-700"
            }`}>
              Target Price (USD)
            </label>
            <div className="relative">
              <span className={`absolute left-4 top-1/2 -translate-y-1/2 ${
                theme === "dark" ? "text-slate-400" : "text-slate-600"
              }`}>
                $
              </span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={formData.target_price}
                onChange={(e) => handleChange("target_price", e.target.value)}
                placeholder="0.00"
                className={`w-full pl-8 pr-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  theme === "dark"
                    ? "bg-slate-900 border-slate-700 text-white placeholder-slate-500"
                    : "bg-white border-slate-300 text-slate-900 placeholder-slate-400"
                }`}
              />
            </div>
          </div>

          {/* Wallet Selection (Optional) */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              theme === "dark" ? "text-slate-300" : "text-slate-700"
            }`}>
              Wallet (Optional)
            </label>
            <select
              value={formData.wallet_address}
              onChange={(e) => handleChange("wallet_address", e.target.value)}
              className={`w-full px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                theme === "dark"
                  ? "bg-slate-900 border-slate-700 text-white"
                  : "bg-white border-slate-300 text-slate-900"
              }`}
            >
              <option value="">All wallets</option>
              {wallets.map((wallet) => (
                <option key={wallet.address} value={wallet.address}>
                  {wallet.label || wallet.address.substring(0, 10)}... ({wallet.chain === 'aptos' ? '⬢ Aptos' : '◎ Solana'})
                </option>
              ))}
            </select>
            <p className={`text-xs mt-1 ${
              theme === "dark" ? "text-slate-500" : "text-slate-400"
            }`}>
              Leave empty to track this token across all your wallets
            </p>
          </div>

          {/* Preview */}
          {formData.token_symbol && formData.target_price && (
            <div className={`p-3 rounded-lg text-xs ${
              theme === "dark" ? "bg-blue-500/10 text-blue-300" : "bg-blue-50 text-blue-700"
            }`}>
              💡 You'll receive an email when <strong>{formData.token_symbol}</strong> {formData.condition === "above" ? "rises above" : "falls below"} <strong>${formData.target_price}</strong>
              {formData.wallet_address ? " in the selected wallet" : " in any of your wallets"}.
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className={`flex-1 px-6 py-3 rounded-lg font-medium transition-colors ${
                theme === "dark"
                  ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              } disabled:opacity-50`}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.token_symbol || !formData.target_price || loadingTokens}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Creating...</span>
                </div>
              ) : (
                "Create Alert"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAlertModal;
