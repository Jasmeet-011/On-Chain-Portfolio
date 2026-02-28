// src/components/TransactionDetailModal.tsx - PROFESSIONAL: Black/White/Gray Theme
import React, { useEffect, useState } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import type { ChainType } from "../api";
import { shortenAddress } from "../utils";
import { CheckCircle2, XCircle, Copy, ExternalLink, AlertTriangle, RefreshCw, X } from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  txHash: string;
  address: string;
  chain: ChainType;
}

const CHAIN_CONFIG: Record<ChainType, { name: string; emoji: string; explorer: string }> = {
  aptos:            { name: "APTOS",    emoji: "⬢",  explorer: "https://explorer.aptoslabs.com/txn" },
  solana:           { name: "SOLANA",   emoji: "◎",  explorer: "https://explorer.solana.com/tx" },
  ethereum:         { name: "ETHEREUM", emoji: "Ξ",  explorer: "https://etherscan.io/tx" },
  ethereum_sepolia: { name: "SEPOLIA",  emoji: "Ξ",  explorer: "https://sepolia.etherscan.io/tx" },
  polygon:          { name: "POLYGON",  emoji: "⬡",  explorer: "https://polygonscan.com/tx" },
  polygon_amoy:     { name: "AMOY",     emoji: "⬡",  explorer: "https://amoy.polygonscan.com/tx" },
  base:             { name: "BASE",     emoji: "🔵", explorer: "https://basescan.org/tx" },
  base_sepolia:     { name: "BASE SEP", emoji: "🔵", explorer: "https://sepolia.basescan.org/tx" },
  evm:              { name: "EVM",      emoji: "⬡",  explorer: "https://etherscan.io/tx" },
};

const TransactionDetailModal: React.FC<Props> = ({ isOpen, onClose, txHash, address, chain }) => {
  const { theme } = useAppContext();
  const [txDetail, setTxDetail] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && txHash) {
      loadTransactionDetail();
    }
  }, [isOpen, txHash, chain]);

  const loadTransactionDetail = async () => {
    setLoading(true);
    setError(null);

    try {
      const detail = await api.getTransactionDetail(address, txHash, chain);
      setTxDetail(detail);
    } catch (err: any) {
      console.error("Failed to load transaction detail:", err);
      setError(err.message || "Failed to load transaction details");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(parseInt(timestamp) / 1000);
    return date.toLocaleString();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getExplorerUrl = () => {
    const config = CHAIN_CONFIG[chain];
    return `${config.explorer}/${txHash}`;
  };

  const getChainBadge = () => {
    const config = CHAIN_CONFIG[chain];
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${
        theme === "dark" 
          ? "bg-zinc-800 text-zinc-300 border-zinc-700"
          : "bg-gray-100 text-gray-700 border border-gray-200"
      }`}>
        <span>{config.emoji}</span>
        {config.name}
      </span>
    );
  };

  return (
    <div
      className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className={`w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl shadow-2xl ${
          theme === "dark" ? "bg-zinc-900" : "bg-white"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`sticky top-0 z-10 flex items-center justify-between p-6 border-b ${
          theme === "dark" ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200"
        }`}>
          <div>
            <div className="flex items-center gap-3">
              <h3 className={`text-xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                Transaction Details
              </h3>
              {getChainBadge()}
            </div>
            <p className={`text-sm mt-1 font-mono ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
              {shortenAddress(txHash)}
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors ${
              theme === "dark" ? "hover:bg-zinc-800 text-zinc-400" : "hover:bg-gray-100 text-gray-600"
            }`}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex items-center gap-3">
                <RefreshCw className={`w-6 h-6 animate-spin ${
                  theme === "dark" ? "text-white" : "text-black"
                }`} />
                <span className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
                  Loading transaction details...
                </span>
              </div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <p className={`mb-4 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                {error}
              </p>
              <button
                onClick={loadTransactionDetail}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  theme === "dark"
                    ? "bg-white text-black hover:bg-gray-200"
                    : "bg-black text-white hover:bg-gray-800"
                }`}
              >
                Try Again
              </button>
            </div>
          ) : txDetail ? (
            <div className="space-y-6">
              {/* Status */}
              <div className="flex items-center justify-between">
                <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                  Status
                </span>
                <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
                  txDetail.success
                    ? "bg-green-500/10 text-green-400 border border-green-500/20"
                    : "bg-red-500/10 text-red-400 border border-red-500/20"
                }`}>
                  {txDetail.success ? (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      Success
                    </>
                  ) : (
                    <>
                      <XCircle className="w-4 h-4" />
                      Failed
                    </>
                  )}
                </span>
              </div>

              {/* Transaction Hash */}
              <div>
                <span className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                  Transaction Hash
                </span>
                <div className="flex items-center gap-2">
                  <code className={`flex-1 px-3 py-2 rounded-lg font-mono text-sm ${
                    theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700"
                  }`}>
                    {txHash}
                  </code>
                  <button
                    onClick={() => copyToClipboard(txHash)}
                    className={`p-2 rounded-lg transition-colors ${
                      theme === "dark" ? "hover:bg-zinc-800 text-zinc-400" : "hover:bg-gray-200 text-gray-600"
                    }`}
                    title="Copy hash"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
                {copied && (
                  <p className="text-xs text-green-500 mt-1">Copied to clipboard!</p>
                )}
              </div>

              {/* Timestamp */}
              {txDetail.timestamp && (
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Timestamp
                  </span>
                  <span className={`text-sm ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                    {formatTimestamp(txDetail.timestamp)}
                  </span>
                </div>
              )}

              {/* Sender */}
              {txDetail.sender && (
                <div>
                  <span className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    From
                  </span>
                  <code className={`block px-3 py-2 rounded-lg font-mono text-sm ${
                    theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700"
                  }`}>
                    {txDetail.sender}
                  </code>
                </div>
              )}

              {/* Type */}
              {txDetail.type && (
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Type
                  </span>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${
                    theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-200 text-gray-700"
                  }`}>
                    {txDetail.type}
                  </span>
                </div>
              )}

              {/* Function */}
              {txDetail.function && (
                <div>
                  <span className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Function
                  </span>
                  <code className={`block px-3 py-2 rounded-lg font-mono text-sm ${
                    theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700"
                  }`}>
                    {txDetail.function}
                  </code>
                </div>
              )}

              {/* Gas Used */}
              {txDetail.gas_used && (
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Gas Used
                  </span>
                  <span className={`text-sm ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                    {txDetail.gas_used}
                  </span>
                </div>
              )}

              {/* Version */}
              {txDetail.version && (
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Version
                  </span>
                  <span className={`text-sm ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                    {txDetail.version}
                  </span>
                </div>
              )}

              {/* Sequence Number */}
              {txDetail.sequence_number !== undefined && (
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                    Sequence Number
                  </span>
                  <span className={`text-sm ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
                    {txDetail.sequence_number}
                  </span>
                </div>
              )}

              {/* View on Explorer Button */}
              <div className="pt-4">
                <a
                  href={getExplorerUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                    theme === "dark"
                      ? "bg-white text-black hover:bg-gray-200"
                      : "bg-black text-white hover:bg-gray-800"
                  }`}
                >
                  <span>View on {CHAIN_CONFIG[chain].name} Explorer</span>
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <AlertTriangle className={`w-12 h-12 mx-auto mb-4 ${
                theme === "dark" ? "text-zinc-600" : "text-gray-400"
              }`} />
              <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
                No transaction details available
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransactionDetailModal;