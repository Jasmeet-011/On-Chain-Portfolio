// src/components/TransactionsTable.tsx - PROFESSIONAL: Black/White/Gray Theme
import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress } from "../utils";
import { CheckCircle2, XCircle, ExternalLink, ChevronLeft, ChevronRight, RefreshCw, Receipt } from "lucide-react";
import TransactionFilters from "./TransactionFilters";
import TransactionDetailModal from "./TransactionDetailModal";

interface Transaction {
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

interface Props {
  address: string;
  onLoadTransactions: (address: string, params: any) => Promise<any>;
}

const TransactionsTable: React.FC<Props> = ({ address, onLoadTransactions }) => {
  const { theme, activeWallet } = useAppContext();
  
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTx, setSelectedTx] = useState<string | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const itemsPerPage = 20;

  const chain = activeWallet?.chain || 'aptos';

  const loadTransactions = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {
        chain,
        limit: itemsPerPage,
        offset: (currentPage - 1) * itemsPerPage,
      };

      if (typeFilter !== "all") params.type_filter = typeFilter;
      if (statusFilter !== "all") params.status_filter = statusFilter;
      if (searchQuery) params.search = searchQuery;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;

      const result = await onLoadTransactions(address, params);
      
      if (Array.isArray(result)) {
        setTransactions(result);
        setTotalPages(Math.ceil(result.length / itemsPerPage));
      } else if (result.transactions) {
        setTransactions(result.transactions);
        setTotalPages(Math.ceil((result.total || result.transactions.length) / itemsPerPage));
      } else {
        setTransactions([]);
        setTotalPages(1);
      }
    } catch (err: any) {
      console.error("Failed to load transactions:", err);
      setError(err.message || "Failed to load transactions");
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (address) {
      loadTransactions();
    }
  }, [address, currentPage, typeFilter, statusFilter, chain]);

  const handleSearch = () => {
    setCurrentPage(1);
    loadTransactions();
  };

  const handleReset = () => {
    setTypeFilter("all");
    setStatusFilter("all");
    setSearchQuery("");
    setDateFrom("");
    setDateTo("");
    setCurrentPage(1);
  };

  const handleTxClick = (hash: string) => {
    setSelectedTx(hash);
    setShowDetailModal(true);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(parseInt(timestamp) / 1000);
    return date.toLocaleString();
  };

  const getTypeColor = (type: string) => {
    const typeMap: Record<string, string> = {
      Transfer: theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700",
      Swap: theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700",
      Stake: theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700",
      Unstake: theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700",
    };
    return typeMap[type] || (theme === "dark" ? "bg-zinc-800 text-zinc-300" : "bg-gray-100 text-gray-700");
  };

  const getChainBadge = (txChain?: string) => {
    const displayChain = (txChain || chain) as 'aptos' | 'solana';
    const emoji = displayChain === 'aptos' ? '⬢' : '◎';
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${
        theme === "dark" 
          ? "bg-zinc-800 text-zinc-300 border-zinc-700"
          : "bg-gray-100 text-gray-700 border-gray-200"
      }`}>
        <span>{emoji}</span>
        {displayChain.toUpperCase()}
      </span>
    );
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="flex items-center gap-3">
          <RefreshCw className={`w-6 h-6 animate-spin ${
            theme === "dark" ? "text-white" : "text-black"
          }`} />
          <span className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            Loading {chain} transactions...
          </span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className={`mb-4 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
          {error}
        </p>
        <button
          onClick={loadTransactions}
          className={`px-4 py-2 rounded-lg transition-colors ${
            theme === "dark"
              ? "bg-zinc-800 text-zinc-200 hover:bg-zinc-700 border border-zinc-700"
              : "bg-black text-white hover:bg-gray-800"
          }`}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <TransactionFilters
        typeFilter={typeFilter}
        setTypeFilter={setTypeFilter}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        dateFrom={dateFrom}
        setDateFrom={setDateFrom}
        dateTo={dateTo}
        setDateTo={setDateTo}
        onSearch={handleSearch}
        onReset={handleReset}
      />

      {transactions.length === 0 ? (
        <div className="text-center py-12">
          <Receipt className={`w-12 h-12 mx-auto mb-4 ${
            theme === "dark" ? "text-zinc-600" : "text-gray-400"
          }`} />
          <h3 className={`text-lg font-semibold mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
            No Transactions Found
          </h3>
          <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            No transaction history available for this wallet on {chain}
          </p>
        </div>
      ) : (
        <>
          {/* Desktop Table */}
          <div className="hidden lg:block overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className={`border-b ${theme === "dark" ? "border-zinc-800" : "border-gray-200"}`}>
                  <th className={`px-4 py-3 text-left text-xs font-semibold uppercase ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>Status</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold uppercase ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>Chain</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold uppercase ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>Type</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold uppercase ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>Hash</th>
                  <th className={`px-4 py-3 text-left text-xs font-semibold uppercase ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>Time</th>
                  <th className={`px-4 py-3 text-right text-xs font-semibold uppercase ${
                    theme === "dark" ? "text-zinc-500" : "text-gray-600"
                  }`}>Gas</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx, idx) => (
                  <tr
                    key={`${tx.hash}-${idx}`}
                    onClick={() => handleTxClick(tx.hash)}
                    className={`border-b cursor-pointer transition-colors ${
                      theme === "dark"
                        ? "border-zinc-800/60 hover:bg-zinc-800/50"
                        : "border-gray-100 hover:bg-gray-50"
                    }`}
                  >
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        {tx.success ? (
                          <CheckCircle2 className="w-5 h-5 text-green-500" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500" />
                        )}
                        <span className={`text-sm font-medium ${
                          tx.success ? "text-green-500" : "text-red-500"
                        }`}>
                          {tx.success ? "Success" : "Failed"}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">{getChainBadge()}</td>
                    <td className="px-4 py-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(tx.type)}`}>
                        {tx.type}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <span className={`font-mono text-sm ${
                          theme === "dark" ? "text-zinc-300" : "text-gray-700"
                        }`}>
                          {shortenAddress(tx.hash)}
                        </span>
                        <ExternalLink className={`w-3 h-3 ${
                          theme === "dark" ? "text-zinc-500" : "text-gray-500"
                        }`} />
                      </div>
                    </td>
                    <td className={`px-4 py-4 text-sm ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}>
                      {formatTimestamp(tx.timestamp)}
                    </td>
                    <td className={`px-4 py-4 text-right text-sm ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}>
                      {tx.gas_used}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="lg:hidden space-y-3">
            {transactions.map((tx, idx) => (
              <div
                key={`${tx.hash}-${idx}`}
                onClick={() => handleTxClick(tx.hash)}
                className={`p-4 rounded-xl border cursor-pointer transition-all duration-150 ${
                  theme === "dark"
                    ? "bg-zinc-900 border-zinc-700/60 hover:border-zinc-600 hover:bg-zinc-800/60"
                    : "bg-white border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {tx.success ? (
                      <CheckCircle2 className="w-5 h-5 text-green-500" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-500" />
                    )}
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(tx.type)}`}>
                      {tx.type}
                    </span>
                  </div>
                  {getChainBadge()}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm ${theme === "dark" ? "text-zinc-500" : "text-gray-600"}`}>
                      Hash
                    </span>
                    <span className={`font-mono text-sm ${
                      theme === "dark" ? "text-zinc-300" : "text-gray-700"
                    }`}>
                      {shortenAddress(tx.hash)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className={`text-sm ${theme === "dark" ? "text-zinc-500" : "text-gray-600"}`}>
                      Gas
                    </span>
                    <span className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                      {tx.gas_used}
                    </span>
                  </div>

                  <div className={`text-xs ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
                    {formatTimestamp(tx.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4">
              <div className={`text-sm ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                Page {currentPage} of {totalPages}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                    currentPage === 1
                      ? "opacity-50 cursor-not-allowed"
                      : ""
                  } ${
                    theme === "dark"
                      ? "bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border border-zinc-800"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1 ${
                    currentPage === totalPages
                      ? "opacity-50 cursor-not-allowed"
                      : ""
                  } ${
                    theme === "dark"
                      ? "bg-zinc-900 text-zinc-300 hover:bg-zinc-800 border border-zinc-800"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {selectedTx && (
        <TransactionDetailModal
          isOpen={showDetailModal}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedTx(null);
          }}
          txHash={selectedTx}
          address={address}
          chain={chain}
        />
      )}
    </div>
  );
};

export default TransactionsTable;