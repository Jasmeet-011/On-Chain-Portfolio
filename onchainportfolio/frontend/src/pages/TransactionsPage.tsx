// src/pages/TransactionsPage.tsx - PROFESSIONAL: Black/White/Gray Theme
import React from "react";
import { useAppContext } from "../context/AppContext";
import TransactionsTable from "../components/TransactionsTable";
import { api } from "../api";
import { Receipt, Lightbulb } from "lucide-react";

const TransactionsPage: React.FC = () => {
  const { theme, activeWallet } = useAppContext();

  // Load transactions with filters (passed to TransactionsTable)
  const loadTransactionsWithFilters = async (address: string, params: any) => {
    return await api.getTransactionsFiltered(address, {
      ...params,
      chain: activeWallet?.chain || 'aptos',
    });
  };

  // No wallet connected
  if (!activeWallet) {
    return (
      <div className={`rounded-xl p-16 text-center ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
      }`}>
        <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 ${
          theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
        }`}>
          <Receipt className={`w-8 h-8 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
        </div>
        <h3 className={`text-2xl font-bold mb-3 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          No Wallet Connected
        </h3>
        <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
          Connect a wallet to view transaction history
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold flex items-center gap-2 ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}>
            Transaction History
          </h2>
          <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              {activeWallet.label}
            </span>
            <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${
              activeWallet.chain === 'aptos'
                ? theme === "dark"
                  ? "bg-zinc-800 text-zinc-300 border border-zinc-700"
                  : "bg-gray-100 text-gray-700 border border-gray-200"
                : theme === "dark"
                ? "bg-zinc-800 text-zinc-300 border border-zinc-700"
                : "bg-gray-100 text-gray-700 border border-gray-200"
            }`}>
              {activeWallet.chain.toUpperCase()}
            </span>
          </p>
        </div>
      </div>

      {/* Transaction History Card */}
      <div className={`rounded-xl overflow-hidden ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
      }`}>
        <div className={`px-6 py-4 border-b ${
          theme === "dark" ? "border-zinc-800" : "border-gray-200"
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
                Recent Activity
              </h3>
              <p className={`text-sm mt-0.5 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
                All transactions for this wallet
              </p>
            </div>
          </div>
        </div>

        {/* Transactions Table */}
        <div className="p-6">
          <TransactionsTable 
            address={activeWallet.address}
            onLoadTransactions={loadTransactionsWithFilters}
          />
        </div>
      </div>

      {/* Info Tip */}
      <div className={`rounded-xl p-4 ${
        theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-gray-50 border border-gray-200"
      }`}>
        <div className="flex items-start gap-3">
          <Lightbulb className={`w-5 h-5 mt-0.5 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
          <div>
            <p className={`text-sm ${theme === "dark" ? "text-zinc-300" : "text-gray-700"}`}>
              <span className="font-medium">Tip:</span> Click on any transaction to view detailed information, 
              including gas fees, events, and state changes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionsPage;