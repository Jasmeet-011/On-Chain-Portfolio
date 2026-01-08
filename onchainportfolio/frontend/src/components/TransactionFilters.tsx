// src/components/TransactionFilters.tsx - PROFESSIONAL: Black/White/Gray Theme
import React from "react";
import { useAppContext } from "../context/AppContext";
import { Search, RefreshCw } from "lucide-react";

interface Props {
  typeFilter: string;
  setTypeFilter: (value: string) => void;
  statusFilter: string;
  setStatusFilter: (value: string) => void;
  searchQuery: string;
  setSearchQuery: (value: string) => void;
  dateFrom: string;
  setDateFrom: (value: string) => void;
  dateTo: string;
  setDateTo: (value: string) => void;
  onSearch: () => void;
  onReset: () => void;
}

const TransactionFilters: React.FC<Props> = ({
  typeFilter,
  setTypeFilter,
  statusFilter,
  setStatusFilter,
  searchQuery,
  setSearchQuery,
  dateFrom,
  setDateFrom,
  dateTo,
  setDateTo,
  onSearch,
  onReset,
}) => {
  const { theme } = useAppContext();

  const transactionTypes = [
    { value: "all", label: "All Types" },
    { value: "Transfer", label: "Transfer" },
    { value: "Swap", label: "Swap" },
    { value: "Stake", label: "Stake" },
    { value: "Unstake", label: "Unstake" },
  ];

  const statusOptions = [
    { value: "all", label: "All Status" },
    { value: "success", label: "Success" },
    { value: "failed", label: "Failed" },
  ];

  return (
    <div className={`p-4 rounded-lg border ${
      theme === "dark" 
        ? "bg-zinc-900 border-zinc-800" 
        : "bg-gray-50 border-gray-200"
    }`}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Type Filter */}
        <div>
          <label className={`block text-xs font-medium mb-1.5 ${
            theme === "dark" ? "text-zinc-400" : "text-gray-600"
          }`}>
            Type
          </label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
              theme === "dark"
                ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                : "bg-white border-gray-300 text-gray-900 focus:ring-black focus:border-black"
            }`}
          >
            {transactionTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className={`block text-xs font-medium mb-1.5 ${
            theme === "dark" ? "text-zinc-400" : "text-gray-600"
          }`}>
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
              theme === "dark"
                ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                : "bg-white border-gray-300 text-gray-900 focus:ring-black focus:border-black"
            }`}
          >
            {statusOptions.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date From */}
        <div>
          <label className={`block text-xs font-medium mb-1.5 ${
            theme === "dark" ? "text-zinc-400" : "text-gray-600"
          }`}>
            From Date
          </label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
              theme === "dark"
                ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                : "bg-white border-gray-300 text-gray-900 focus:ring-black focus:border-black"
            }`}
          />
        </div>

        {/* Date To */}
        <div>
          <label className={`block text-xs font-medium mb-1.5 ${
            theme === "dark" ? "text-zinc-400" : "text-gray-600"
          }`}>
            To Date
          </label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className={`w-full px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
              theme === "dark"
                ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                : "bg-white border-gray-300 text-gray-900 focus:ring-black focus:border-black"
            }`}
          />
        </div>
      </div>

      {/* Search Bar & Actions */}
      <div className="flex flex-col sm:flex-row gap-3 mt-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by hash, sender, or function..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                onSearch();
              }
            }}
            className={`w-full px-4 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
              theme === "dark"
                ? "bg-zinc-800 border-zinc-700 text-white placeholder-zinc-400 focus:ring-white focus:border-white"
                : "bg-white border-gray-300 text-gray-900 placeholder-gray-500 focus:ring-black focus:border-black"
            }`}
          />
        </div>

        <div className="flex gap-2">
          {/* Search Button */}
          <button
            onClick={onSearch}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              theme === "dark"
                ? "bg-white text-black hover:bg-gray-200"
                : "bg-black text-white hover:bg-gray-800"
            }`}
          >
            <Search className="w-4 h-4" />
            Search
          </button>

          {/* Reset Button */}
          <button
            onClick={onReset}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              theme === "dark"
                ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border border-zinc-700"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300 border border-gray-300"
            }`}
          >
            <RefreshCw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>
    </div>
  );
};

export default TransactionFilters;