// src/components/AlertCard.tsx - FIXED: Uses last_triggered instead of triggered_at
import React from "react";
import { useAppContext } from "../context/AppContext";
import { format } from "date-fns";

// ✅ FIXED: Interface matches backend AlertResponse
interface Alert {
  id: string;
  user_id: string;
  alert_type: string;
  token_symbol: string;
  chain: string;
  condition: "above" | "below";
  target_price: number;
  current_price?: number;
  wallet_address?: string;
  is_active: boolean;
  is_recurring: boolean;
  status: string;
  last_triggered?: string;  // ✅ Backend sends last_triggered
  trigger_count: number;
  last_checked?: string;
  created_at: string;
  updated_at?: string;
}

interface AlertCardProps {
  alert: Alert;
  onDelete: (alertId: string) => void;
  onToggle: (alertId: string, isActive: boolean) => void;
  onTest: (alertId: string) => void;
}

const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onDelete,
  onToggle,
  onTest,
}) => {
  const { theme } = useAppContext();

  // Get status info - ✅ FIXED: Uses last_triggered
  const getStatus = () => {
    if (alert.last_triggered) {
      return {
        label: "Triggered",
        color: theme === "dark" ? "bg-green-500/10 text-green-400 border-green-500/20" : "bg-green-50 text-green-600 border-green-200",
        icon: "✅"
      };
    }
    if (!alert.is_active) {
      return {
        label: "Paused",
        color: theme === "dark" ? "bg-slate-700 text-slate-400 border-slate-600" : "bg-slate-100 text-slate-600 border-slate-200",
        icon: "⏸️"
      };
    }
    return {
      label: "Active",
      color: theme === "dark" ? "bg-blue-500/10 text-blue-400 border-blue-500/20" : "bg-blue-50 text-blue-600 border-blue-200",
      icon: "🔔"
    };
  };

  const status = getStatus();

  // Format date
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), "MMM d, yyyy");
    } catch {
      return dateString;
    }
  };

  // Get chain icon
  const getChainIcon = (chain: string) => {
    switch (chain?.toLowerCase()) {
      case "aptos":
        return "⬢";
      case "solana":
        return "◎";
      default:
        return "🔗";
    }
  };

  return (
    <div
      className={`rounded-xl p-6 border transition-all duration-200 ${
        theme === "dark"
          ? "bg-slate-800 border-slate-700 hover:border-slate-600"
          : "bg-white border-slate-200 hover:border-slate-300 shadow-sm"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Token Icon Placeholder */}
          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${
            theme === "dark" ? "bg-slate-700" : "bg-slate-100"
          }`}>
            {alert.token_symbol?.substring(0, 2) || "??"}
          </div>
          
          <div>
            <h3 className={`text-lg font-bold flex items-center gap-2 ${
              theme === "dark" ? "text-white" : "text-slate-900"
            }`}>
              {alert.token_symbol}
              <span className="text-sm opacity-60" title={alert.chain}>
                {getChainIcon(alert.chain)}
              </span>
            </h3>
            <p className={`text-sm ${
              theme === "dark" ? "text-slate-400" : "text-slate-600"
            }`}>
              {alert.condition === "above" ? "⬆️ Above" : "⬇️ Below"} ${alert.target_price?.toFixed(2) || "0.00"}
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${status.color}`}>
          {status.icon} {status.label}
        </span>
      </div>

      {/* Current Price (if available) */}
      {alert.current_price && (
        <div className={`mb-4 p-3 rounded-lg ${
          theme === "dark" ? "bg-slate-700/50" : "bg-slate-50"
        }`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}>
              Current Price
            </span>
            <span className={`text-lg font-bold ${theme === "dark" ? "text-white" : "text-slate-900"}`}>
              ${alert.current_price.toFixed(2)}
            </span>
          </div>
          {/* Progress indicator */}
          <div className="mt-2">
            <div className={`h-1 rounded-full ${theme === "dark" ? "bg-slate-600" : "bg-slate-200"}`}>
              <div 
                className={`h-1 rounded-full ${
                  alert.condition === "above" 
                    ? "bg-green-500" 
                    : "bg-red-500"
                }`}
                style={{ 
                  width: `${Math.min(100, Math.max(0, 
                    alert.condition === "above"
                      ? (alert.current_price / alert.target_price) * 100
                      : (alert.target_price / alert.current_price) * 100
                  ))}%` 
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Details */}
      <div className={`space-y-2 py-3 border-t border-b ${
        theme === "dark" ? "border-slate-700" : "border-slate-200"
      }`}>
        {/* Wallet */}
        {alert.wallet_address ? (
          <div className="flex items-center justify-between text-sm">
            <span className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
              Wallet:
            </span>
            <span className={`font-mono ${
              theme === "dark" ? "text-slate-300" : "text-slate-700"
            }`}>
              {alert.wallet_address.substring(0, 6)}...{alert.wallet_address.substring(alert.wallet_address.length - 4)}
            </span>
          </div>
        ) : (
          <div className="flex items-center justify-between text-sm">
            <span className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
              Scope:
            </span>
            <span className={theme === "dark" ? "text-slate-300" : "text-slate-700"}>
              All wallets
            </span>
          </div>
        )}

        {/* Recurring */}
        <div className="flex items-center justify-between text-sm">
          <span className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
            Type:
          </span>
          <span className={theme === "dark" ? "text-slate-300" : "text-slate-700"}>
            {alert.is_recurring ? "🔄 Recurring" : "1️⃣ One-time"}
          </span>
        </div>

        {/* Created Date */}
        <div className="flex items-center justify-between text-sm">
          <span className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
            Created:
          </span>
          <span className={theme === "dark" ? "text-slate-300" : "text-slate-700"}>
            {formatDate(alert.created_at)}
          </span>
        </div>

        {/* Triggered Date - ✅ FIXED: Uses last_triggered */}
        {alert.last_triggered && (
          <div className="flex items-center justify-between text-sm">
            <span className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
              Triggered:
            </span>
            <span className="text-green-500 font-medium">
              {formatDate(alert.last_triggered)}
            </span>
          </div>
        )}

        {/* Trigger Count */}
        {alert.trigger_count > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
              Times Triggered:
            </span>
            <span className={`font-medium ${theme === "dark" ? "text-green-400" : "text-green-600"}`}>
              {alert.trigger_count}
            </span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 mt-4">
        {/* Toggle Active - ✅ FIXED: Uses last_triggered */}
        <button
          onClick={() => onToggle(alert.id, alert.is_active)}
          disabled={!!alert.last_triggered && !alert.is_recurring}
          className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            alert.is_active && !alert.last_triggered
              ? theme === "dark"
                ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              : "bg-blue-600 text-white hover:bg-blue-700"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title={
            alert.last_triggered && !alert.is_recurring 
              ? "Already triggered (one-time alert)" 
              : alert.is_active 
                ? "Pause alert" 
                : "Resume alert"
          }
        >
          {alert.is_active ? "⏸️ Pause" : "▶️ Resume"}
        </button>

        {/* Test Email - ✅ FIXED: Uses last_triggered */}
        {alert.is_active && !alert.last_triggered && (
          <button
            onClick={() => onTest(alert.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              theme === "dark"
                ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
            title="Send test email"
          >
            📧 Test
          </button>
        )}

        {/* Delete */}
        <button
          onClick={() => onDelete(alert.id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            theme === "dark"
              ? "bg-red-500/10 text-red-400 hover:bg-red-500/20"
              : "bg-red-50 text-red-600 hover:bg-red-100"
          }`}
          title="Delete alert"
        >
          🗑️
        </button>
      </div>

      {/* Triggered Info - ✅ FIXED: Uses last_triggered */}
      {alert.last_triggered && !alert.is_recurring && (
        <div className={`mt-4 p-3 rounded-lg ${
          theme === "dark" ? "bg-green-500/10" : "bg-green-50"
        }`}>
          <p className={`text-xs ${
            theme === "dark" ? "text-green-300" : "text-green-700"
          }`}>
            ✅ This alert was triggered and an email was sent to you. The alert has been automatically paused.
          </p>
        </div>
      )}

      {/* Recurring Info */}
      {alert.last_triggered && alert.is_recurring && (
        <div className={`mt-4 p-3 rounded-lg ${
          theme === "dark" ? "bg-blue-500/10" : "bg-blue-50"
        }`}>
          <p className={`text-xs ${
            theme === "dark" ? "text-blue-300" : "text-blue-700"
          }`}>
            🔄 This recurring alert was triggered {alert.trigger_count} time(s). It will continue to monitor the price.
          </p>
        </div>
      )}
    </div>
  );
};

export default AlertCard;