import React from "react";
import { useAppContext } from "../context/AppContext";

interface Props {
  typeFilter: string;
  statusFilter: string;
  searchQuery: string;
  onTypeFilterChange: (value: string) => void;
  onStatusFilterChange: (value: string) => void;
  onSearchChange: (value: string) => void;
  onExport: () => void;
}

const TransactionFilters: React.FC<Props> = ({
  typeFilter,
  statusFilter,
  searchQuery,
  onTypeFilterChange,
  onStatusFilterChange,
  onSearchChange,
  onExport,
}) => {
  const { theme } = useAppContext();

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="flex-1 min-w-[200px]">
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            🔍
          </span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search by hash, function, or address..."
            className={`w-full pl-10 pr-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
              theme === "dark"
                ? "bg-gray-700/50 border-gray-600 text-white placeholder-gray-400"
                : "bg-white border-gray-200 text-gray-900 placeholder-gray-500"
            }`}
          />
        </div>
      </div>

      {/* Type Filter */}
      <select
        value={typeFilter}
        onChange={(e) => onTypeFilterChange(e.target.value)}
        className={`px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
          theme === "dark"
            ? "bg-gray-700/50 border-gray-600 text-white"
            : "bg-white border-gray-200 text-gray-900"
        }`}
      >
        <option value="">All Types</option>
        <option value="transfer">Transfer</option>
        <option value="swap">Swap</option>
        <option value="stake">Stake</option>
        <option value="mint">Mint</option>
        <option value="nft">NFT</option>
      </select>

      {/* Status Filter */}
      <select
        value={statusFilter}
        onChange={(e) => onStatusFilterChange(e.target.value)}
        className={`px-4 py-2 rounded-lg border focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all ${
          theme === "dark"
            ? "bg-gray-700/50 border-gray-600 text-white"
            : "bg-white border-gray-200 text-gray-900"
        }`}
      >
        <option value="">All Status</option>
        <option value="success">Success</option>
        <option value="failed">Failed</option>
      </select>

      {/* Export Button */}
      <button
        onClick={onExport}
        className={`px-4 py-2 rounded-lg font-medium transition-all ${
          theme === "dark"
            ? "bg-green-600 text-white hover:bg-green-700"
            : "bg-green-500 text-white hover:bg-green-600"
        }`}
      >
        📥 Export CSV
      </button>

      {/* Clear Filters */}
      {(typeFilter || statusFilter || searchQuery) && (
        <button
          onClick={() => {
            onTypeFilterChange("");
            onStatusFilterChange("");
            onSearchChange("");
          }}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            theme === "dark"
              ? "bg-gray-700 text-gray-300 hover:bg-gray-600"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          Clear Filters
        </button>
      )}
    </div>
  );
};

export default TransactionFilters;