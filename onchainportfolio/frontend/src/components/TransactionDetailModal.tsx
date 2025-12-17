import React from "react";
import { useAppContext } from "../context/AppContext";
// import { shortenAddress } from "../utils";

interface Transaction {
  hash: string;
  version: string;
  success: boolean;
  timestamp: string;
  gas_used: number;
  sender: string;
  type: string;
  category: string;
  function?: string;
  details: Record<string, any>;
}

interface Props {
  transaction: Transaction;
  onClose: () => void;
}

const TransactionDetailModal: React.FC<Props> = ({ transaction, onClose }) => {
  const { theme } = useAppContext();

  const formatDate = (timestamp: string) => {
    try {
      const tsMicro = parseInt(timestamp);
      const tsSec = tsMicro / 1_000_000;
      const date = new Date(tsSec * 1000);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const openExplorer = () => {
    window.open(`https://explorer.aptoslabs.com/txn/${transaction.hash}?network=testnet`, "_blank");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className={`max-w-2xl w-full max-h-[80vh] overflow-y-auto rounded-2xl border ${
          theme === "dark"
            ? "bg-gray-800 border-gray-700"
            : "bg-white border-gray-200"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h2 className={`text-2xl font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              Transaction Details
            </h2>
            <p className={`text-sm mt-1 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              {transaction.type}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-2xl text-gray-400 hover:text-white transition-colors"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Status */}
          <div>
            <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              Status
            </label>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              transaction.success
                ? "bg-green-500/10 text-green-400 border border-green-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
            }`}>
              {transaction.success ? "✓ Success" : "✗ Failed"}
            </span>
          </div>

          {/* Hash */}
          <div>
            <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              Transaction Hash
            </label>
            <div className="flex items-center gap-2">
              <code className={`flex-1 px-3 py-2 rounded-lg text-sm font-mono ${
                theme === "dark" ? "bg-gray-900 text-gray-300" : "bg-gray-100 text-gray-700"
              }`}>
                {transaction.hash}
              </code>
              <button
                onClick={() => navigator.clipboard.writeText(transaction.hash)}
                className={`px-3 py-2 rounded-lg text-sm ${
                  theme === "dark" ? "bg-gray-700 hover:bg-gray-600" : "bg-gray-200 hover:bg-gray-300"
                }`}
              >
                📋
              </button>
            </div>
          </div>

          {/* Time */}
          <div>
            <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              Time
            </label>
            <p className={theme === "dark" ? "text-white" : "text-gray-900"}>
              {formatDate(transaction.timestamp)}
            </p>
          </div>

          {/* Sender */}
          <div>
            <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              Sender
            </label>
            <code className={`block px-3 py-2 rounded-lg text-sm font-mono ${
              theme === "dark" ? "bg-gray-900 text-gray-300" : "bg-gray-100 text-gray-700"
            }`}>
              {transaction.sender}
            </code>
          </div>

          {/* Transaction Details */}
          {Object.keys(transaction.details).length > 0 && (
            <div>
              <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                Details
              </label>
              <div className={`px-4 py-3 rounded-lg space-y-2 ${
                theme === "dark" ? "bg-gray-900" : "bg-gray-100"
              }`}>
                {Object.entries(transaction.details).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className={`text-sm capitalize ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                      {key.replace(/_/g, " ")}:
                    </span>
                    <span className={`text-sm font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                      {typeof value === "object" ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gas */}
          <div>
            <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
              Gas Used
            </label>
            <p className={theme === "dark" ? "text-white" : "text-gray-900"}>
              {transaction.gas_used} units
            </p>
          </div>

          {/* Function */}
          {transaction.function && (
            <div>
              <label className={`text-sm font-medium block mb-2 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                Function
              </label>
              <code className={`block px-3 py-2 rounded-lg text-xs font-mono break-all ${
                theme === "dark" ? "bg-gray-900 text-gray-300" : "bg-gray-100 text-gray-700"
              }`}>
                {transaction.function}
              </code>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-700 flex gap-3">
          <button
            onClick={openExplorer}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
          >
            View on Explorer
          </button>
          <button
            onClick={onClose}
            className={`px-6 py-2 rounded-xl font-medium transition-colors ${
              theme === "dark"
                ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionDetailModal;