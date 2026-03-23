import React from "react";
import { useAppContext } from "../context/AppContext";
import TransactionsTable from "../components/TransactionsTable";
import { api } from "../api";
import { Receipt, Lightbulb } from "lucide-react";
import { getChainColors } from "../utils/tokens";

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
        <div className={`inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5 ${
          theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
        }`}>
          <Receipt className={`w-7 h-7 ${theme === "dark" ? "text-zinc-400" : "text-gray-500"}`} />
        </div>
        <h3 className={`text-lg font-semibold mb-2 ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
          No Wallet Connected
        </h3>
        <p className={`text-sm ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`}>
          Connect a wallet to view transaction history
        </p>
      </div>
    );
  }

  const chainColors = getChainColors(activeWallet.chain);

  return (
    <div className="space-y-5">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-xl font-bold flex items-center gap-2 ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}>
            Transaction History
          </h2>
          <p className={`text-sm mt-1 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            <span className={`font-medium ${theme === "dark" ? "text-white" : "text-gray-900"}`}>
              {activeWallet.label}
            </span>
            <span className={`ml-2 px-2 py-0.5 rounded-md text-xs font-medium border ${chainColors.bg} ${chainColors.text} ${chainColors.border}`}>
              {activeWallet.chain.charAt(0).toUpperCase() + activeWallet.chain.slice(1)}
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
        theme === "dark" ? "bg-zinc-900/60 border border-zinc-800/80" : "bg-gray-50 border border-gray-200"
      }`}>
        <div className="flex items-start gap-3">
          <Lightbulb className={`w-4 h-4 mt-0.5 shrink-0 ${theme === "dark" ? "text-zinc-500" : "text-gray-500"}`} />
          <p className={`text-xs ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`}>
            <span className="font-medium">Tip:</span> Click on any transaction to view detailed information,
            including gas fees, events, and state changes.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TransactionsPage;