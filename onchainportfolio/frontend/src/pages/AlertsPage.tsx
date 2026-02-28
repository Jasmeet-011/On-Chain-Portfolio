// src/pages/AlertsPage.tsx
import React, { useState, useEffect, useCallback } from "react";
import { useAppContext } from "../context/AppContext";
import AlertCard from "../components/AlertCard";
import CreateAlertModal from "../components/CreateAlertModal";
import {
  RefreshCw, Bell, Plus, TrendingUp, TrendingDown,
  Shuffle, DollarSign, ChevronRight, Mail, Calendar, Sparkles,
} from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../api";
import type { Alert, PortfolioSuggestion } from "../api";

type AlertFilter = "all" | "active" | "paused" | "triggered";

const SUGGESTION_ICONS: Record<string, React.ReactNode> = {
  reduce:      <TrendingDown className="w-5 h-5 text-red-400" />,
  buy:         <DollarSign   className="w-5 h-5 text-emerald-400" />,
  diversify:   <Shuffle      className="w-5 h-5 text-blue-400" />,
  take_profit: <TrendingUp   className="w-5 h-5 text-yellow-400" />,
};

const PRIORITY_BADGE: Record<string, string> = {
  high:   "text-red-400    bg-red-500/10    border border-red-500/20",
  medium: "text-yellow-400 bg-yellow-500/10 border border-yellow-500/20",
  low:    "text-blue-400   bg-blue-500/10   border border-blue-500/20",
};

// ── Simple inline toggle component ────────────────────────────────────────────
const Toggle: React.FC<{
  checked: boolean;
  onChange: () => void;
  disabled?: boolean;
}> = ({ checked, onChange, disabled }) => (
  <button
    type="button"
    role="switch"
    aria-checked={checked}
    onClick={onChange}
    disabled={disabled}
    className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none disabled:opacity-50 ${
      checked ? "bg-blue-600" : "bg-zinc-600"
    }`}
  >
    <span
      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
        checked ? "translate-x-6" : "translate-x-1"
      }`}
    />
  </button>
);

// ── Notification preferences (inline, no modal) ───────────────────────────────
const NotificationPrefs: React.FC<{ isDark: boolean }> = ({ isDark }) => {
  const [prefs, setPrefs] = useState({
    price_alerts_enabled: true,
    daily_digest_enabled: false,
    weekly_summary_enabled: false,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState<string | null>(null);

  useEffect(() => {
    api.getEmailPreferences()
      .then(d => setPrefs({
        price_alerts_enabled:  d.email_enabled   ?? true,
        daily_digest_enabled:  d.daily_digest    ?? false,
        weekly_summary_enabled: d.weekly_summary ?? false,
      }))
      .catch(() => {/* use defaults */})
      .finally(() => setLoading(false));
  }, []);

  const toggle = useCallback(async (key: keyof typeof prefs) => {
    const next = { ...prefs, [key]: !prefs[key] };
    setPrefs(next);
    setSaving(key);
    try {
      await api.updateEmailPreferences({
        email_enabled:  next.price_alerts_enabled,
        daily_digest:   next.daily_digest_enabled,
        weekly_summary: next.weekly_summary_enabled,
        instant_alerts: true,
      });
      toast.success("Preference saved");
    } catch {
      setPrefs(prefs); // revert
      toast.error("Failed to save");
    } finally {
      setSaving(null);
    }
  }, [prefs]);

  const items = [
    {
      key:   "price_alerts_enabled" as const,
      icon:  <Bell    className="w-4 h-4 text-blue-400"    />,
      label: "Instant price alerts",
      desc:  "Email when a price target is hit",
    },
    {
      key:   "daily_digest_enabled" as const,
      icon:  <Mail    className="w-4 h-4 text-green-400"   />,
      label: "Daily digest",
      desc:  "Morning portfolio summary (9 AM)",
    },
    {
      key:   "weekly_summary_enabled" as const,
      icon:  <Calendar className="w-4 h-4 text-purple-400" />,
      label: "Weekly suggestions",
      desc:  "Sunday report with rebalancing tips",
    },
  ];

  return (
    <div className={`rounded-2xl border p-5 ${
      isDark ? "bg-zinc-900 border-zinc-700/60" : "bg-white border-gray-200 shadow-sm"
    }`}>
      <div className="flex items-center gap-2 mb-4">
        <Mail className={`w-4 h-4 ${isDark ? "text-zinc-400" : "text-gray-500"}`} />
        <h3 className={`text-sm font-semibold ${isDark ? "text-zinc-200" : "text-gray-800"}`}>
          Email Notifications
        </h3>
      </div>
      <div className="space-y-3">
        {items.map(item => (
          <div key={item.key} className="flex items-center justify-between gap-4">
            <div className="flex items-start gap-3 min-w-0">
              <div className={`mt-0.5 w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                isDark ? "bg-zinc-800" : "bg-gray-100"
              }`}>
                {item.icon}
              </div>
              <div className="min-w-0">
                <p className={`text-sm font-medium ${isDark ? "text-zinc-200" : "text-gray-800"}`}>
                  {item.label}
                </p>
                <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-500"}`}>
                  {item.desc}
                </p>
              </div>
            </div>
            <Toggle
              checked={prefs[item.key]}
              onChange={() => toggle(item.key)}
              disabled={loading || saving === item.key}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Main AlertsPage ────────────────────────────────────────────────────────────
const AlertsPage: React.FC = () => {
  const { theme, wallets } = useAppContext();
  const isDark = theme === "dark";

  const [alerts, setAlerts]                 = useState<Alert[]>([]);
  const [suggestions, setSuggestions]       = useState<PortfolioSuggestion[]>([]);
  const [loading, setLoading]               = useState(true);
  const [suggestLoading, setSuggestLoading] = useState(true);
  const [error, setError]                   = useState<string | null>(null);
  const [filter, setFilter]                 = useState<AlertFilter>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    loadAlerts();
    loadSuggestions();
  }, []);

  const loadAlerts = async (showToast = false) => {
    setLoading(true);
    setError(null);
    const id = showToast ? toast.loading("Refreshing alerts…") : null;
    try {
      const data = await api.getAlerts();
      setAlerts(data);
      if (id) toast.success(`${data.length} alerts loaded!`, { id });
    } catch (err: any) {
      setError(err.message || "Failed to load alerts");
      if (id) toast.error("Failed to refresh alerts", { id });
    } finally {
      setLoading(false);
    }
  };

  const loadSuggestions = async () => {
    setSuggestLoading(true);
    try { setSuggestions(await api.getAlertSuggestions()); }
    catch { /* silent */ }
    finally { setSuggestLoading(false); }
  };

  const handleCreateAlert = async (alertData: any) => {
    const id = toast.loading("Creating alert…");
    try {
      await api.createAlert(alertData);
      toast.success(`Alert created for ${alertData.token_symbol}!`, { id });
      await loadAlerts();
      setShowCreateModal(false);
    } catch (err: any) {
      toast.error(err.message || "Failed to create alert", { id });
      throw err;
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    toast(
      (t) => (
        <div className="flex flex-col gap-3">
          <p className="font-medium">Delete this alert?</p>
          <div className="flex gap-2">
            <button
              onClick={() => { toast.dismiss(t.id); performDelete(alertId); }}
              className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600"
            >Delete</button>
            <button
              onClick={() => toast.dismiss(t.id)}
              className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
            >Cancel</button>
          </div>
        </div>
      ),
      { duration: 10000, position: "top-center" }
    );
  };

  const performDelete = async (alertId: string) => {
    const id = toast.loading("Deleting alert…");
    try {
      await api.deleteAlert(alertId);
      toast.success("Alert deleted!", { id });
      await loadAlerts();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete alert", { id });
    }
  };

  const handleToggleAlert = async (alertId: string, isActive: boolean) => {
    const id = toast.loading(`${isActive ? "Pausing" : "Resuming"} alert…`);
    try {
      await api.updateAlert(alertId, { is_active: !isActive });
      toast.success(`Alert ${isActive ? "paused" : "resumed"}!`, { id });
      await loadAlerts();
    } catch (err: any) {
      toast.error(err.message || "Failed to update alert", { id });
    }
  };

  const handleTestAlert = async (alertId: string) => {
    const id = toast.loading("Sending test email…");
    try {
      const r = await api.testAlert(alertId);
      toast.success(r.message || "Test email sent!", { id });
    } catch (err: any) {
      toast.error(err.message || "Failed to send test email", { id });
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (filter === "all")       return true;
    if (filter === "active")    return a.is_active && !a.last_triggered;
    if (filter === "paused")    return !a.is_active;
    if (filter === "triggered") return !!a.last_triggered;
    return true;
  });

  const counts = {
    all:       alerts.length,
    active:    alerts.filter(a => a.is_active && !a.last_triggered).length,
    paused:    alerts.filter(a => !a.is_active).length,
    triggered: alerts.filter(a => !!a.last_triggered).length,
  };

  return (
    <div className="space-y-6">

      {/* ── Page header ──────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? "text-white" : "text-gray-900"}`}>
            <Bell className="w-6 h-6" />
            Price Alerts
          </h2>
          <p className={`text-sm mt-1 ${isDark ? "text-zinc-400" : "text-gray-600"}`}>
            Real-time email notifications when your price targets are reached
          </p>
        </div>

        <div className="flex gap-2 shrink-0">
          <button
            onClick={() => loadAlerts(true)}
            disabled={loading}
            title="Refresh"
            className={`p-2.5 rounded-xl transition-colors border disabled:opacity-50 ${
              isDark ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border-zinc-700"
                     : "bg-white text-gray-700 hover:bg-gray-50 border-gray-200"
            }`}
          >
            <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-500 transition-colors flex items-center gap-2 shadow-lg shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" />
            <span>New Alert</span>
          </button>
        </div>
      </div>

      {/* ── Two-column: suggestions + notification prefs ─────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Suggestions (left, 2/3 width) */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className={`text-xs font-semibold uppercase tracking-widest flex items-center gap-2 ${
            isDark ? "text-zinc-500" : "text-gray-400"
          }`}>
            <Sparkles className="w-3.5 h-3.5" />
            Portfolio Suggestions
          </h3>

          {suggestLoading ? (
            <div className={`rounded-2xl p-5 border flex items-center gap-3 ${
              isDark ? "bg-zinc-900 border-zinc-700/60" : "bg-white border-gray-200"
            }`}>
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              <span className={`text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
                Analysing your portfolio…
              </span>
            </div>
          ) : suggestions.length === 0 ? (
            <div className={`rounded-2xl p-5 border text-center ${
              isDark ? "bg-zinc-900 border-zinc-700/60" : "bg-white border-gray-200"
            }`}>
              <Sparkles className={`w-8 h-8 mx-auto mb-2 ${isDark ? "text-zinc-700" : "text-gray-300"}`} />
              <p className={`text-sm ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                Your portfolio looks balanced — no suggestions right now.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {suggestions.map((s, i) => (
                <div
                  key={i}
                  className={`rounded-2xl border p-4 transition-all duration-200 ${
                    isDark
                      ? "bg-zinc-900 border-zinc-700/60 hover:border-zinc-600"
                      : "bg-white border-gray-200 hover:border-gray-300 shadow-sm"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                      isDark ? "bg-zinc-800" : "bg-gray-100"
                    }`}>
                      {SUGGESTION_ICONS[s.type] ?? <Bell className="w-5 h-5 text-gray-400" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <p className={`text-sm font-semibold ${isDark ? "text-zinc-100" : "text-gray-900"}`}>
                          {s.title}
                        </p>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase tracking-wide ${PRIORITY_BADGE[s.priority]}`}>
                          {s.priority}
                        </span>
                      </div>
                      <p className={`text-xs leading-relaxed ${isDark ? "text-zinc-400" : "text-gray-600"}`}>
                        {s.reason}
                      </p>
                      <p className={`text-xs mt-2 flex items-center gap-1 font-medium ${isDark ? "text-blue-400" : "text-blue-600"}`}>
                        <ChevronRight className="w-3 h-3 shrink-0" />
                        {s.action}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Notification prefs (right, 1/3 width) */}
        <div className="lg:col-span-1">
          <h3 className={`text-xs font-semibold uppercase tracking-widest flex items-center gap-2 mb-3 ${
            isDark ? "text-zinc-500" : "text-gray-400"
          }`}>
            <Bell className="w-3.5 h-3.5" />
            Notifications
          </h3>
          <NotificationPrefs isDark={isDark} />
        </div>
      </div>

      {/* ── Filter tabs ──────────────────────────────────────── */}
      <div className={`flex gap-1 border-b ${isDark ? "border-zinc-700/60" : "border-gray-200"}`}>
        {(["all", "active", "paused", "triggered"] as AlertFilter[]).map(tab => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors relative capitalize ${
              filter === tab
                ? isDark ? "text-white" : "text-gray-900"
                : isDark ? "text-zinc-500 hover:text-zinc-300" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab}
            {counts[tab] > 0 && (
              <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-xs ${
                filter === tab
                  ? "bg-blue-500/20 text-blue-400"
                  : isDark ? "bg-zinc-700 text-zinc-400" : "bg-gray-200 text-gray-500"
              }`}>
                {counts[tab]}
              </span>
            )}
            {filter === tab && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* ── Loading ──────────────────────────────────────────── */}
      {loading && alerts.length === 0 && (
        <div className={`rounded-2xl p-12 text-center border ${
          isDark ? "bg-zinc-900 border-zinc-700/60" : "bg-white border-gray-200"
        }`}>
          <RefreshCw className={`w-8 h-8 animate-spin mx-auto mb-3 ${isDark ? "text-zinc-400" : "text-gray-400"}`} />
          <p className={isDark ? "text-zinc-400" : "text-gray-500"}>Loading alerts…</p>
        </div>
      )}

      {/* ── Error ────────────────────────────────────────────── */}
      {error && !loading && (
        <div className={`rounded-2xl p-12 text-center border ${
          isDark ? "bg-zinc-900 border-zinc-700/60" : "bg-white border-gray-200"
        }`}>
          <Bell className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className={`text-xl font-bold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>Error Loading Alerts</h3>
          <p className={`mb-6 ${isDark ? "text-zinc-400" : "text-gray-600"}`}>{error}</p>
          <button onClick={() => loadAlerts(true)} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-500">
            Try Again
          </button>
        </div>
      )}

      {/* ── Alerts grid ──────────────────────────────────────── */}
      {!loading && !error && filteredAlerts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filteredAlerts.map(alert => (
            <AlertCard
              key={alert.id}
              alert={alert}
              onDelete={handleDeleteAlert}
              onToggle={handleToggleAlert}
              onTest={handleTestAlert}
            />
          ))}
        </div>
      )}

      {/* ── Empty state ──────────────────────────────────────── */}
      {!loading && !error && filteredAlerts.length === 0 && (
        <div className={`rounded-2xl p-16 text-center border ${
          isDark ? "bg-zinc-900 border-zinc-700/60" : "bg-white border-gray-200"
        }`}>
          <Bell className={`w-14 h-14 mx-auto mb-4 ${isDark ? "text-zinc-700" : "text-gray-300"}`} />
          <h3 className={`text-xl font-bold mb-2 ${isDark ? "text-white" : "text-gray-900"}`}>
            {filter === "all" ? "No Alerts Yet" : `No ${filter} alerts`}
          </h3>
          <p className={`mb-6 text-sm ${isDark ? "text-zinc-400" : "text-gray-600"}`}>
            {filter === "all"
              ? "Create your first price alert to get notified when tokens reach your target prices."
              : `You don't have any ${filter} alerts.`}
          </p>
          {filter === "all" && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-500 transition-colors inline-flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Create First Alert
            </button>
          )}
        </div>
      )}

      {/* ── Modals ───────────────────────────────────────────── */}
      {showCreateModal && (
        <CreateAlertModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateAlert}
          wallets={wallets}
        />
      )}
    </div>
  );
};

export default AlertsPage;
