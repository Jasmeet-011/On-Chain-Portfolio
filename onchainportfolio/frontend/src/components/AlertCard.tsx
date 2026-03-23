import React from "react";
import { useAppContext } from "../context/AppContext";
import { format } from "date-fns";
import {
  ArrowUp, ArrowDown, Pause, Play, Mail, Trash2,
  RefreshCw, CheckCircle2, BellOff,
} from "lucide-react";
import { getTokenGradient, getChainColors } from "../utils/tokens";

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
  last_triggered?: string;
  trigger_count: number;
  last_checked?: string;
  created_at: string;
  updated_at?: string;
}

interface AlertCardProps {
  alert: Alert;
  onDelete: (alertId: string) => void;
  onToggle: (alertId: string, isActive: boolean) => void;
  onTest:   (alertId: string) => void;
}

const AlertCard: React.FC<AlertCardProps> = ({ alert, onDelete, onToggle, onTest }) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";

  const isTriggered = !!alert.last_triggered;
  const isActive    = alert.is_active && !isTriggered;

  const statusLabel = isTriggered ? "Triggered" : isActive ? "Active" : "Paused";
  const statusClass = isTriggered
    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    : isActive
      ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
      : "bg-zinc-800 text-zinc-400 border-zinc-700/50";

  const StatusIcon = isTriggered ? CheckCircle2 : isActive ? null : BellOff;

  const chain = getChainColors(alert.chain);
  const gradient = getTokenGradient(alert.token_symbol);

  const formatDate = (ds: string) => {
    try { return format(new Date(ds), "MMM d, yyyy"); }
    catch { return ds; }
  };

  const progress = alert.current_price && alert.target_price
    ? Math.min(100, Math.max(0,
        alert.condition === "above"
          ? (alert.current_price / alert.target_price) * 100
          : (alert.target_price / alert.current_price) * 100
      ))
    : null;

  const rowClass = `flex items-center justify-between text-xs`;
  const labelClass = isDark ? "text-zinc-500" : "text-gray-500";
  const valueClass = isDark ? "text-zinc-300" : "text-gray-700";

  return (
    <div className={`rounded-xl p-5 border transition-all duration-200 flex flex-col gap-4 ${
      isDark
        ? "bg-zinc-900 border-zinc-800/80 hover:border-zinc-700"
        : "bg-white border-gray-200 hover:border-gray-300 shadow-sm"
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {/* Token icon */}
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${gradient}`}>
            <span className="text-white text-sm font-bold">
              {alert.token_symbol?.slice(0, 2).toUpperCase() || "??"}
            </span>
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <span className={`text-sm font-bold ${isDark ? "text-white" : "text-gray-900"}`}>
                {alert.token_symbol}
              </span>
              <span className={`text-xs px-1.5 py-0.5 rounded-md border font-medium ${chain.bg} ${chain.text} ${chain.border}`}>
                {alert.chain?.slice(0, 3).toUpperCase()}
              </span>
            </div>
            <div className={`flex items-center gap-1 text-xs mt-0.5 ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
              {alert.condition === "above"
                ? <ArrowUp className="w-3 h-3 text-emerald-400" />
                : <ArrowDown className="w-3 h-3 text-red-400" />}
              <span>
                {alert.condition === "above" ? "Above" : "Below"} ${alert.target_price?.toFixed(2) ?? "0.00"}
              </span>
            </div>
          </div>
        </div>

        {/* Status badge */}
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border ${statusClass}`}>
          {StatusIcon && <StatusIcon className="w-3 h-3" />}
          {statusLabel}
        </span>
      </div>

      {/* Current price + progress */}
      {alert.current_price && (
        <div className={`p-3 rounded-lg ${isDark ? "bg-zinc-800/60" : "bg-gray-50"}`}>
          <div className="flex items-center justify-between mb-2">
            <span className={`text-xs ${labelClass}`}>Current price</span>
            <span className={`text-sm font-bold font-numeric ${isDark ? "text-white" : "text-gray-900"}`}>
              ${alert.current_price.toFixed(2)}
            </span>
          </div>
          {progress !== null && (
            <div className={`h-1 rounded-full overflow-hidden ${isDark ? "bg-zinc-700" : "bg-gray-200"}`}>
              <div
                className={`h-full rounded-full transition-all ${
                  alert.condition === "above" ? "bg-emerald-500" : "bg-red-500"
                }`}
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* Details */}
      <div className={`space-y-2 pt-3 border-t ${isDark ? "border-zinc-800" : "border-gray-100"}`}>
        <div className={rowClass}>
          <span className={labelClass}>Wallet</span>
          <span className={`font-mono ${valueClass}`}>
            {alert.wallet_address
              ? `${alert.wallet_address.slice(0, 6)}…${alert.wallet_address.slice(-4)}`
              : "All wallets"}
          </span>
        </div>

        <div className={rowClass}>
          <span className={labelClass}>Type</span>
          <div className={`flex items-center gap-1 ${valueClass}`}>
            {alert.is_recurring && <RefreshCw className="w-3 h-3" />}
            <span>{alert.is_recurring ? "Recurring" : "One-time"}</span>
          </div>
        </div>

        <div className={rowClass}>
          <span className={labelClass}>Created</span>
          <span className={valueClass}>{formatDate(alert.created_at)}</span>
        </div>

        {alert.last_triggered && (
          <div className={rowClass}>
            <span className={labelClass}>Triggered</span>
            <span className="text-emerald-400 font-medium">{formatDate(alert.last_triggered)}</span>
          </div>
        )}

        {alert.trigger_count > 0 && (
          <div className={rowClass}>
            <span className={labelClass}>Times triggered</span>
            <span className={`font-medium font-numeric ${isDark ? "text-emerald-400" : "text-emerald-600"}`}>
              {alert.trigger_count}
            </span>
          </div>
        )}
      </div>

      {/* Info banners */}
      {isTriggered && !alert.is_recurring && (
        <div className={`px-3 py-2 rounded-lg text-xs ${
          isDark ? "bg-emerald-500/10 text-emerald-300" : "bg-emerald-50 text-emerald-700"
        }`}>
          Alert triggered — email sent. Alert automatically paused.
        </div>
      )}
      {isTriggered && alert.is_recurring && (
        <div className={`px-3 py-2 rounded-lg text-xs ${
          isDark ? "bg-blue-500/10 text-blue-300" : "bg-blue-50 text-blue-700"
        }`}>
          Triggered {alert.trigger_count} time(s) — still monitoring.
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onToggle(alert.id, alert.is_active)}
          disabled={isTriggered && !alert.is_recurring}
          className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
            isActive
              ? isDark ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              : "bg-blue-600 text-white hover:bg-blue-500"
          }`}
          title={isActive ? "Pause alert" : "Resume alert"}
        >
          {isActive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          {isActive ? "Pause" : "Resume"}
        </button>

        {isActive && (
          <button
            onClick={() => onTest(alert.id)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              isDark ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
            title="Send test email"
          >
            <Mail className="w-3.5 h-3.5" />
            Test
          </button>
        )}

        <button
          onClick={() => onDelete(alert.id)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
            isDark ? "bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20" : "bg-red-50 text-red-600 hover:bg-red-100 border border-red-100"
          }`}
          title="Delete alert"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};

export default AlertCard;
