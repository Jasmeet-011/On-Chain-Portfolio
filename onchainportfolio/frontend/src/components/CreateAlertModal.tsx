// src/components/CreateAlertModal.tsx
import React, { useState, useEffect, useCallback } from "react";
import { useAppContext } from "../context/AppContext";
import type { ExtendedWalletInfo } from "../context/AppContext";
import { api } from "../api";
import { RefreshCw, Bell, RepeatIcon } from "lucide-react";

interface CreateAlertModalProps {
  onClose: () => void;
  onCreate: (alertData: any) => Promise<void>;
  wallets: ExtendedWalletInfo[];
}

const POPULAR_TOKENS = [
  { symbol: "BTC",  name: "Bitcoin"   },
  { symbol: "ETH",  name: "Ethereum"  },
  { symbol: "SOL",  name: "Solana"    },
  { symbol: "APT",  name: "Aptos"     },
  { symbol: "USDC", name: "USD Coin"  },
];

const CHAIN_LABELS: Record<string, string> = {
  aptos:             "Aptos",
  solana:            "Solana",
  ethereum:          "Ethereum",
  ethereum_sepolia:  "Ethereum",
  polygon:           "Polygon",
  polygon_amoy:      "Polygon",
  base:              "Base",
  base_sepolia:      "Base",
  evm:               "Ethereum",
};

const CreateAlertModal: React.FC<CreateAlertModalProps> = ({
  onClose,
  onCreate,
  wallets,
}) => {
  const { theme, portfolioData } = useAppContext();
  const isDark = theme === "dark";

  const [formData, setFormData] = useState({
    token_symbol:  "",
    target_price:  "",
    condition:     "above" as "above" | "below",
    wallet_address: "",
    chain:         "solana",
    is_recurring:  false,
  });

  const [loading, setLoading]             = useState(false);
  const [error, setError]                 = useState<string | null>(null);
  const [availableTokens, setAvailableTokens] = useState<string[]>([]);
  const [loadingTokens, setLoadingTokens] = useState(true);
  const [currentPrice, setCurrentPrice]   = useState<number | null>(null);
  const [priceLoading, setPriceLoading]   = useState(false);

  // ── Build available token list ──────────────────────────────
  useEffect(() => {
    const build = async () => {
      setLoadingTokens(true);
      const set = new Set<string>(POPULAR_TOKENS.map(t => t.symbol));

      if (portfolioData?.balances?.length) {
        portfolioData.balances.forEach((b: any) => { if (b.symbol) set.add(b.symbol); });
      } else if (wallets.length > 0) {
        for (const wallet of wallets) {
          try {
            const data = await api.getPortfolio(wallet.address, wallet.chain);
            data?.balances?.forEach((b: any) => { if (b.symbol) set.add(b.symbol); });
          } catch { /* ignore */ }
        }
      }

      const tokens = Array.from(set).sort();
      setAvailableTokens(tokens);
      if (!formData.token_symbol && tokens.length > 0) {
        setFormData(prev => ({ ...prev, token_symbol: tokens[0] }));
      }
      setLoadingTokens(false);
    };
    build();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wallets, portfolioData]);

  // ── Fetch current price whenever token or chain changes ─────
  const fetchPrice = useCallback(async (symbol: string, chain: string) => {
    if (!symbol) { setCurrentPrice(null); return; }
    setPriceLoading(true);
    const price = await api.getTokenPrice(symbol, chain);
    setCurrentPrice(price);
    setPriceLoading(false);
  }, []);

  useEffect(() => {
    if (formData.token_symbol) {
      fetchPrice(formData.token_symbol, formData.chain);
    }
  }, [formData.token_symbol, formData.chain, fetchPrice]);

  // ── Handle wallet selection → auto-set chain ────────────────
  const handleWalletChange = (address: string) => {
    const wallet = wallets.find(w => w.address === address);
    setFormData(prev => ({
      ...prev,
      wallet_address: address,
      chain: wallet ? wallet.chain : prev.chain,
    }));
  };

  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.token_symbol) { setError("Please select a token"); return; }
    if (!formData.target_price || parseFloat(formData.target_price) <= 0) {
      setError("Please enter a valid target price");
      return;
    }

    setLoading(true);
    try {
      await onCreate({
        token_symbol:   formData.token_symbol.toUpperCase(),
        target_price:   parseFloat(formData.target_price),
        condition:      formData.condition,
        wallet_address: formData.wallet_address || undefined,
        chain:          formData.chain,
        is_recurring:   formData.is_recurring,
      });
    } catch (err: any) {
      setError(err.message || "Failed to create alert");
      setLoading(false);
    }
  };

  // ── Helpers ─────────────────────────────────────────────────
  const formatPrice = (p: number) =>
    p < 0.01 ? `$${p.toFixed(6)}` : p < 1 ? `$${p.toFixed(4)}` : `$${p.toFixed(2)}`;

  const distanceToTarget = () => {
    if (!currentPrice || !formData.target_price) return null;
    const target = parseFloat(formData.target_price);
    if (target <= 0) return null;
    const pct = ((target - currentPrice) / currentPrice) * 100;
    return pct;
  };

  const pctDiff = distanceToTarget();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className={`relative w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden ${
        isDark ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200"
      }`}>
        {/* Header */}
        <div className={`px-6 py-5 border-b ${isDark ? "border-zinc-800" : "border-gray-100"}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                <Bell className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h3 className={`text-lg font-bold ${isDark ? "text-white" : "text-gray-900"}`}>
                  Create Price Alert
                </h3>
                <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-500" : "text-gray-500"}`}>
                  Get an email when your target is reached
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${
                isDark ? "hover:bg-zinc-800 text-zinc-500" : "hover:bg-gray-100 text-gray-500"
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* ── Token Selection ─────────────────────── */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
              Token
            </label>

            {/* Popular quick-select chips */}
            <div className="flex flex-wrap gap-2 mb-2">
              {POPULAR_TOKENS.map(t => (
                <button
                  key={t.symbol}
                  type="button"
                  onClick={() => handleChange("token_symbol", t.symbol)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    formData.token_symbol === t.symbol
                      ? "bg-blue-600 text-white"
                      : isDark
                      ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {t.symbol}
                </button>
              ))}
            </div>

            {/* Full token dropdown */}
            {loadingTokens ? (
              <div className={`px-4 py-3 rounded-xl border text-sm flex items-center gap-2 ${
                isDark ? "bg-zinc-800/60 border-zinc-700 text-zinc-400" : "bg-gray-50 border-gray-200 text-gray-500"
              }`}>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Loading tokens...
              </div>
            ) : availableTokens.length > 0 ? (
              <select
                value={formData.token_symbol}
                onChange={e => handleChange("token_symbol", e.target.value)}
                className={`w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
                  isDark ? "bg-zinc-800 border-zinc-700 text-white" : "bg-white border-gray-300 text-gray-900"
                }`}
              >
                <option value="">Select a token…</option>
                {availableTokens.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={formData.token_symbol}
                onChange={e => handleChange("token_symbol", e.target.value.toUpperCase())}
                placeholder="Enter token symbol (e.g. SOL)"
                className={`w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
                  isDark ? "bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500" : "bg-white border-gray-300 text-gray-900"
                }`}
              />
            )}

            {/* Live price badge */}
            {formData.token_symbol && (
              <div className={`mt-2 flex items-center gap-2 text-xs ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
                <span>Current price:</span>
                {priceLoading
                  ? <RefreshCw className="w-3 h-3 animate-spin" />
                  : currentPrice !== null
                  ? <span className={`font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>{formatPrice(currentPrice)}</span>
                  : <span className="italic">unavailable</span>
                }
                {!priceLoading && currentPrice && (
                  <button
                    type="button"
                    onClick={() => fetchPrice(formData.token_symbol, formData.chain)}
                    className="ml-1 text-blue-400 hover:text-blue-300"
                    title="Refresh price"
                  >
                    <RefreshCw className="w-3 h-3" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* ── Condition ───────────────────────────── */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
              Alert When Price Goes
            </label>
            <div className="grid grid-cols-2 gap-2">
              {(["above", "below"] as const).map(cond => (
                <button
                  key={cond}
                  type="button"
                  onClick={() => handleChange("condition", cond)}
                  className={`px-4 py-3 rounded-xl font-medium text-sm transition-colors ${
                    formData.condition === cond
                      ? cond === "above" ? "bg-green-600 text-white" : "bg-red-600 text-white"
                      : isDark ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {cond === "above" ? "⬆️ Above" : "⬇️ Below"}
                </button>
              ))}
            </div>
          </div>

          {/* ── Target Price ─────────────────────────── */}
          <div>
            <label className={`block text-sm font-medium mb-2 ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
              Target Price (USD)
            </label>
            <div className="relative">
              <span className={`absolute left-4 top-1/2 -translate-y-1/2 text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>$</span>
              <input
                type="number"
                step="0.000001"
                min="0"
                value={formData.target_price}
                onChange={e => handleChange("target_price", e.target.value)}
                placeholder="0.00"
                className={`w-full pl-8 pr-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
                  isDark ? "bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500" : "bg-white border-gray-300 text-gray-900"
                }`}
              />
            </div>
            {/* Distance indicator */}
            {pctDiff !== null && (
              <p className={`mt-1.5 text-xs ${Math.abs(pctDiff) < 5 ? "text-yellow-400" : isDark ? "text-zinc-500" : "text-gray-400"}`}>
                {pctDiff > 0
                  ? `Target is ${pctDiff.toFixed(1)}% above current price`
                  : `Target is ${Math.abs(pctDiff).toFixed(1)}% below current price`}
              </p>
            )}
          </div>

          {/* ── Recurring toggle ─────────────────────── */}
          <div className={`flex items-start gap-3 p-4 rounded-xl border ${
            isDark ? "bg-zinc-800/50 border-zinc-700" : "bg-gray-50 border-gray-200"
          }`}>
            <div className="flex items-center h-5 mt-0.5">
              <input
                id="is_recurring"
                type="checkbox"
                checked={formData.is_recurring}
                onChange={e => handleChange("is_recurring", e.target.checked)}
                className="w-4 h-4 rounded border-gray-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </div>
            <div className="flex-1">
              <label htmlFor="is_recurring" className={`flex items-center gap-2 text-sm font-medium cursor-pointer ${isDark ? "text-zinc-200" : "text-gray-800"}`}>
                <RepeatIcon className="w-4 h-4 text-blue-400" />
                Recurring alert
              </label>
              <p className={`text-xs mt-1 ${isDark ? "text-zinc-500" : "text-gray-500"}`}>
                Re-notify every hour while condition is met. Unchecked = one-time trigger then auto-disable.
              </p>
            </div>
          </div>

          {/* ── Wallet (optional) ────────────────────── */}
          {wallets.length > 0 && (
            <div>
              <label className={`block text-sm font-medium mb-2 ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
                Wallet <span className={`font-normal ${isDark ? "text-zinc-500" : "text-gray-400"}`}>(optional)</span>
              </label>
              <select
                value={formData.wallet_address}
                onChange={e => handleWalletChange(e.target.value)}
                className={`w-full px-4 py-3 rounded-xl border focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
                  isDark ? "bg-zinc-800 border-zinc-700 text-white" : "bg-white border-gray-300 text-gray-900"
                }`}
              >
                <option value="">All wallets</option>
                {wallets.map(w => (
                  <option key={w.address} value={w.address}>
                    {w.label || `${w.address.substring(0, 10)}…`} ({CHAIN_LABELS[w.chain] ?? w.chain})
                  </option>
                ))}
              </select>
              <p className={`text-xs mt-1 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                Leave empty to track across all your wallets
              </p>
            </div>
          )}

          {/* ── Preview pill ─────────────────────────── */}
          {formData.token_symbol && formData.target_price && (
            <div className={`p-3 rounded-xl text-xs ${
              isDark ? "bg-blue-500/10 border border-blue-500/20 text-blue-300" : "bg-blue-50 border border-blue-200 text-blue-700"
            }`}>
              <span>You'll receive an email when </span>
              <strong>{formData.token_symbol}</strong>
              <span> {formData.condition === "above" ? "rises above" : "falls below"} </span>
              <strong>${formData.target_price}</strong>
              {formData.is_recurring && <span> (repeating every hour)</span>}
              .
            </div>
          )}

          {/* ── Actions ──────────────────────────────── */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className={`flex-1 px-6 py-3 rounded-xl font-medium text-sm transition-colors disabled:opacity-50 ${
                isDark ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !formData.token_symbol || !formData.target_price}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Creating…
                </span>
              ) : "Create Alert"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateAlertModal;
