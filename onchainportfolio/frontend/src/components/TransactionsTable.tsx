import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import { shortenAddress } from "../utils";
import TransactionDetailModal from "./TransactionDetailModal";
import TransactionFilters from "./TransactionFilters";

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
  details: {
    recipient?: string;
    amount?: number;
    symbol?: string;
    direction?: string;
    from_coin?: string;
    to_coin?: string;
    action?: string;
    [key: string]: any;
  };
}

interface Props {
  address: string;
  onLoadTransactions?: (address: string, params: any) => Promise<any>;
}

const TransactionsTable: React.FC<Props> = ({ address, onLoadTransactions }) => {
  const { theme } = useAppContext();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  
  // Pagination
  const [offset, setOffset] = useState(0);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  
  // Filters
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const loadTransactions = async () => {
    if (!address || !onLoadTransactions) return;
    
    setLoading(true);
    try {
      const params = {
        limit,
        offset,
        type_filter: typeFilter || undefined,
        status_filter: statusFilter || undefined,
        search: searchQuery || undefined,
      };
      
      const result = await onLoadTransactions(address, params);
      
      setTransactions(result.transactions || []);
      setTotal(result.total || 0);
      setHasMore(result.has_more || false);
    } catch (error) {
      console.error("[TransactionsTable] Failed to load:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [address, offset, typeFilter, statusFilter, searchQuery]);

  const handleRowClick = (txn: Transaction) => {
    setSelectedTxn(txn);
    setShowDetailModal(true);
  };

  const handleNextPage = () => {
    if (hasMore) {
      setOffset(offset + limit);
    }
  };

  const handlePrevPage = () => {
    if (offset >= limit) {
      setOffset(offset - limit);
    }
  };

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

  const formatAmount = (amount: number | undefined, symbol: string | undefined) => {
    if (!amount || !symbol) return "N/A";
    return `${amount.toFixed(4)} ${symbol}`;
  };

  const getTypeIcon = (type: string, category: string) => {
    switch (category) {
      case "transfer":
        return "💸";
      case "swap":
        return "🔄";
      case "stake":
        return "📊";
      case "nft":
        return "🖼️";
      case "mint":
        return "⚡";
      default:
        return "📋";
    }
  };

  const openExplorer = (hash: string, e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(`https://explorer.aptoslabs.com/txn/${hash}?network=testnet`, "_blank");
  };

  if (loading && transactions.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-block w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className={`mt-4 text-sm ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
          Loading transactions...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <TransactionFilters
        typeFilter={typeFilter}
        statusFilter={statusFilter}
        searchQuery={searchQuery}
        onTypeFilterChange={setTypeFilter}
        onStatusFilterChange={setStatusFilter}
        onSearchChange={setSearchQuery}
        onExport={() => {
          window.open(`http://localhost:8000/v1/wallets/${address}/transactions/export/csv`, "_blank");
        }}
      />

      {/* Results Info */}
      <div className="flex items-center justify-between">
        <p className={`text-sm ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
          Showing {transactions.length > 0 ? offset + 1 : 0}-{offset + transactions.length} of {total} transactions
        </p>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-blue-500">
            <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            Loading...
          </div>
        )}
      </div>

      {/* Table */}
      {transactions.length === 0 ? (
        <div className={`text-center py-12 ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
          {searchQuery || typeFilter || statusFilter ? (
            <>
              <div className="text-4xl mb-4">🔍</div>
              <p className="font-medium mb-2">No transactions match your filters</p>
              <p className="text-sm">Try adjusting your search criteria</p>
            </>
          ) : (
            <>
              <div className="text-4xl mb-4">📭</div>
              <p>No transactions found</p>
            </>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className={`border-b ${theme === "dark" ? "border-gray-700" : "border-gray-200"}`}>
                <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                  Type
                </th>
                <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                  Details
                </th>
                <th className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                  Time
                </th>
                <th className={`px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                  Amount
                </th>
                <th className={`px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn, idx) => (
                <tr
                  key={idx}
                  onClick={() => handleRowClick(txn)}
                  className={`border-b transition-colors cursor-pointer ${
                    theme === "dark"
                      ? "border-gray-800 hover:bg-gray-800/50"
                      : "border-gray-100 hover:bg-gray-50"
                  }`}
                >
                  {/* Type */}
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{getTypeIcon(txn.type, txn.category)}</span>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          txn.category === "transfer"
                            ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                            : txn.category === "swap"
                            ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                            : txn.category === "stake"
                            ? "bg-green-500/10 text-green-400 border border-green-500/20"
                            : "bg-gray-500/10 text-gray-400 border border-gray-500/20"
                        }`}
                      >
                        {txn.type}
                      </span>
                    </div>
                  </td>

                  {/* Details */}
                  <td className="px-4 py-4">
                    <div className={`text-sm ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                      {txn.category === "transfer" && txn.details.recipient && (
                        <div>
                          To: <span className="font-mono text-xs">{shortenAddress(txn.details.recipient)}</span>
                        </div>
                      )}
                      {txn.category === "swap" && (
                        <div>
                          {txn.details.from_coin} → {txn.details.to_coin}
                        </div>
                      )}
                      {txn.category === "stake" && (
                        <div className="capitalize">
                          {txn.details.action || "Stake"}
                        </div>
                      )}
                      {!["transfer", "swap", "stake"].includes(txn.category) && (
                        <div className="font-mono text-xs">
                          {shortenAddress(txn.hash)}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={(e) => openExplorer(txn.hash, e)}
                      className={`text-xs mt-1 hover:underline ${theme === "dark" ? "text-blue-400" : "text-blue-600"}`}
                    >
                      View on explorer →
                    </button>
                  </td>

                  {/* Time */}
                  <td className={`px-4 py-4 text-sm ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
                    {formatDate(txn.timestamp)}
                  </td>

                  {/* Amount */}
                  <td className={`px-4 py-4 text-right ${theme === "dark" ? "text-gray-300" : "text-gray-700"}`}>
                    {txn.details.amount && txn.details.symbol ? (
                      <div>
                        <div className="font-semibold">
                          {formatAmount(txn.details.amount, txn.details.symbol)}
                        </div>
                        <div className={`text-xs ${theme === "dark" ? "text-gray-500" : "text-gray-500"}`}>
                          Gas: {txn.gas_used}
                        </div>
                      </div>
                    ) : (
                      <div className={`text-sm ${theme === "dark" ? "text-gray-500" : "text-gray-500"}`}>
                        Gas: {txn.gas_used}
                      </div>
                    )}
                  </td>

                  {/* Status */}
                  <td className="px-4 py-4 text-center">
                    {txn.success ? (
                      <span className="text-green-500 text-xl">✓</span>
                    ) : (
                      <span className="text-red-500 text-xl">✗</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {transactions.length > 0 && (
        <div className="flex items-center justify-between pt-4 border-t border-gray-700">
          <button
            onClick={handlePrevPage}
            disabled={offset === 0}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              offset === 0
                ? "opacity-50 cursor-not-allowed"
                : theme === "dark"
                ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            ← Previous
          </button>
          
          <span className={`text-sm ${theme === "dark" ? "text-gray-400" : "text-gray-600"}`}>
            Page {Math.floor(offset / limit) + 1}
          </span>
          
          <button
            onClick={handleNextPage}
            disabled={!hasMore}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              !hasMore
                ? "opacity-50 cursor-not-allowed"
                : theme === "dark"
                ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Next →
          </button>
        </div>
      )}

      {/* Transaction Detail Modal */}
      {showDetailModal && selectedTxn && (
        <TransactionDetailModal
          transaction={selectedTxn}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedTxn(null);
          }}
        />
      )}
    </div>
  );
};

export default TransactionsTable;