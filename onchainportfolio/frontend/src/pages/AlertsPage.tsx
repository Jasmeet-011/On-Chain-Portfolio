// src/pages/AlertsPage.tsx - FIXED: API Response Handling
import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import AlertCard from "../components/AlertCard";
import CreateAlertModal from "../components/CreateAlertModal";
import EmailPreferencesModal from "../components/EmailPreferencesModal";
import { RefreshCw, Bell, Settings, Plus, AlertTriangle } from "lucide-react";
import toast from "react-hot-toast";

type AlertFilter = "all" | "active" | "paused" | "triggered";

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
  last_triggered?: string;  // ✅ Backend sends last_triggered, not triggered_at
  trigger_count: number;
  last_checked?: string;
  created_at: string;
  updated_at?: string;
}

const AlertsPage: React.FC = () => {
  const { theme, wallets } = useAppContext();
  
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<AlertFilter>("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showPreferencesModal, setShowPreferencesModal] = useState(false);

  // Load alerts on mount
  useEffect(() => {
    loadAlerts();
  }, []);

  // Helper to get auth token
  const getAuthToken = (): string => {
    const userStr = localStorage.getItem("user");
    if (!userStr) return "";
    try {
      const user = JSON.parse(userStr);
      return user.access_token || "";
    } catch {
      return "";
    }
  };

  const loadAlerts = async (showToast: boolean = false) => {
    setLoading(true);
    setError(null);

    const toastId = showToast ? toast.loading("Refreshing alerts...") : null;

    try {
      const response = await fetch("http://localhost:8000/v1/alerts", {
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load alerts");
      }

      const data = await response.json();
      
      // ✅ FIXED: Backend returns direct array, not { alerts: [...] }
      const alertsArray = Array.isArray(data) ? data : (data.alerts || []);
      setAlerts(alertsArray);
      
      if (toastId) {
        toast.success(`${alertsArray.length} alerts loaded!`, { id: toastId });
      }
    } catch (err: any) {
      console.error("Failed to load alerts:", err);
      setError(err.message || "Failed to load alerts");
      
      if (toastId) {
        toast.error("Failed to refresh alerts", { id: toastId });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlert = async (alertData: any) => {
    const toastId = toast.loading("Creating alert...");
    
    try {
      const response = await fetch("http://localhost:8000/v1/alerts", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(alertData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to create alert");
      }

      toast.success(`Alert created for ${alertData.token_symbol}!`, { id: toastId });
      
      // Reload alerts
      await loadAlerts();
      setShowCreateModal(false);
    } catch (err: any) {
      console.error("Failed to create alert:", err);
      toast.error(err.message || "Failed to create alert", { id: toastId });
      throw err;
    }
  };

  const handleDeleteAlert = async (alertId: string) => {
    // Use toast confirmation
    toast((t) => (
      <div className="flex flex-col gap-3">
        <p className="font-medium">Delete this alert?</p>
        <div className="flex gap-2">
          <button
            onClick={() => {
              toast.dismiss(t.id);
              performDelete(alertId);
            }}
            className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600"
          >
            Delete
          </button>
          <button
            onClick={() => toast.dismiss(t.id)}
            className="px-3 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>
      </div>
    ), {
      duration: 10000,
      position: 'top-center',
    });
  };

  const performDelete = async (alertId: string) => {
    const toastId = toast.loading("Deleting alert...");
    
    try {
      const response = await fetch(`http://localhost:8000/v1/alerts/${alertId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to delete alert");
      }

      toast.success("Alert deleted!", { id: toastId });
      await loadAlerts();
    } catch (err: any) {
      console.error("Failed to delete alert:", err);
      toast.error(err.message || "Failed to delete alert", { id: toastId });
    }
  };

  const handleToggleAlert = async (alertId: string, isActive: boolean) => {
    const action = isActive ? "Pausing" : "Resuming";
    const toastId = toast.loading(`${action} alert...`);
    
    try {
      const response = await fetch(`http://localhost:8000/v1/alerts/${alertId}`, {
        method: "PATCH",
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ is_active: !isActive }),
      });

      if (!response.ok) {
        throw new Error("Failed to update alert");
      }

      toast.success(`Alert ${isActive ? "paused" : "resumed"}!`, { id: toastId });
      await loadAlerts();
    } catch (err: any) {
      console.error("Failed to update alert:", err);
      toast.error(err.message || "Failed to update alert", { id: toastId });
    }
  };

  const handleTestAlert = async (alertId: string) => {
    const toastId = toast.loading("Sending test email...");
    
    try {
      const response = await fetch(`http://localhost:8000/v1/alerts/${alertId}/test`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to send test email");
      }

      const result = await response.json();
      toast.success(result.message || "Test email sent!", { id: toastId });
    } catch (err: any) {
      console.error("Failed to test alert:", err);
      toast.error(err.message || "Failed to send test email", { id: toastId });
    }
  };

  // ✅ FIXED: Filter uses last_triggered instead of triggered_at
  const filteredAlerts = alerts.filter(alert => {
    if (filter === "all") return true;
    if (filter === "active") return alert.is_active && !alert.last_triggered;
    if (filter === "paused") return !alert.is_active;
    if (filter === "triggered") return !!alert.last_triggered;
    return true;
  });

  // Get filter counts
  const getCounts = () => ({
    all: alerts.length,
    active: alerts.filter(a => a.is_active && !a.last_triggered).length,
    paused: alerts.filter(a => !a.is_active).length,
    triggered: alerts.filter(a => !!a.last_triggered).length,
  });

  const counts = getCounts();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className={`text-2xl font-bold flex items-center gap-2 ${
            theme === "dark" ? "text-white" : "text-slate-900"
          }`}>
            <Bell className="w-6 h-6" />
            Price Alerts
          </h2>
          <p className={`text-sm mt-1 ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}>
            Get notified when tokens reach your target prices
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          {/* Refresh Button */}
          <button
            onClick={() => loadAlerts(true)}
            disabled={loading}
            className={`px-4 py-3 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              theme === "dark"
                ? "bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-200"
            } disabled:opacity-50`}
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          {/* Email Preferences Button */}
          <button
            onClick={() => setShowPreferencesModal(true)}
            className={`px-4 py-3 rounded-lg font-medium transition-colors flex items-center gap-2 ${
              theme === "dark"
                ? "bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                : "bg-white text-slate-700 hover:bg-slate-50 border border-slate-200"
            }`}
          >
            <Settings className="w-5 h-5" />
            <span className="hidden sm:inline">Settings</span>
          </button>

          {/* Create Alert Button */}
          <button
            onClick={() => {
              if (wallets.length === 0) {
                toast.error("Please connect a wallet first");
                return;
              }
              setShowCreateModal(true);
            }}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span className="hidden sm:inline">Create Alert</span>
            <span className="sm:hidden">Create</span>
          </button>
        </div>
      </div>

      {/* No Wallets Warning */}
      {wallets.length === 0 && (
        <div className={`rounded-xl p-6 ${
          theme === "dark" 
            ? "bg-yellow-500/10 border border-yellow-500/20" 
            : "bg-yellow-50 border border-yellow-200"
        }`}>
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-500" />
            <div>
              <p className={`text-sm font-medium ${
                theme === "dark" ? "text-yellow-400" : "text-yellow-900"
              }`}>
                No Wallets Connected
              </p>
              <p className={`text-xs mt-1 ${
                theme === "dark" ? "text-yellow-300/70" : "text-yellow-700/70"
              }`}>
                Connect a wallet to create price alerts for your tokens
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className={`flex gap-2 border-b ${
        theme === "dark" ? "border-slate-700" : "border-slate-200"
      }`}>
        {[
          { id: "all", label: "All", count: counts.all },
          { id: "active", label: "Active", count: counts.active },
          { id: "paused", label: "Paused", count: counts.paused },
          { id: "triggered", label: "Triggered", count: counts.triggered },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id as AlertFilter)}
            className={`px-4 py-3 text-sm font-medium transition-colors relative ${
              filter === tab.id
                ? "text-blue-500"
                : theme === "dark"
                ? "text-slate-400 hover:text-slate-300"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                filter === tab.id
                  ? "bg-blue-500/20 text-blue-400"
                  : theme === "dark"
                  ? "bg-slate-700 text-slate-400"
                  : "bg-slate-200 text-slate-600"
              }`}>
                {tab.count}
              </span>
            )}
            {filter === tab.id && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />
            )}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && alerts.length === 0 && (
        <div className={`rounded-xl p-12 text-center ${
          theme === "dark" ? "bg-slate-800 border border-slate-700" : "bg-white border border-slate-200"
        }`}>
          <div className="flex justify-center mb-4">
            <RefreshCw className={`w-8 h-8 animate-spin ${theme === "dark" ? "text-white" : "text-black"}`} />
          </div>
          <p className={theme === "dark" ? "text-slate-400" : "text-slate-600"}>
            Loading alerts...
          </p>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <div className={`rounded-xl p-12 text-center ${
          theme === "dark" ? "bg-slate-800 border border-slate-700" : "bg-white border border-slate-200"
        }`}>
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className={`text-xl font-bold mb-2 ${theme === "dark" ? "text-white" : "text-slate-900"}`}>
            Error Loading Alerts
          </h3>
          <p className={`mb-6 ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}>
            {error}
          </p>
          <button
            onClick={() => loadAlerts(true)}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Alerts Grid */}
      {!loading && !error && filteredAlerts.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAlerts.map((alert) => (
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

      {/* Empty State */}
      {!loading && !error && filteredAlerts.length === 0 && (
        <div className={`rounded-xl p-16 text-center ${
          theme === "dark" ? "bg-slate-800 border border-slate-700" : "bg-white border border-slate-200"
        }`}>
          <Bell className={`w-16 h-16 mx-auto mb-4 ${theme === "dark" ? "text-slate-600" : "text-slate-400"}`} />
          <h3 className={`text-xl font-bold mb-2 ${theme === "dark" ? "text-white" : "text-slate-900"}`}>
            {filter === "all" ? "No Alerts Yet" : `No ${filter} alerts`}
          </h3>
          <p className={`mb-6 ${theme === "dark" ? "text-slate-400" : "text-slate-600"}`}>
            {filter === "all"
              ? "Create your first price alert to get notified when tokens reach your target prices"
              : `You don't have any ${filter} alerts`
            }
          </p>
          {filter === "all" && wallets.length > 0 && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Create First Alert
            </button>
          )}
        </div>
      )}

      {/* Info Banner */}
      <div className={`rounded-xl p-4 ${
        theme === "dark" ? "bg-blue-500/10 border border-blue-500/20" : "bg-blue-50 border border-blue-200"
      }`}>
        <div className="flex items-start gap-3">
          <span className="text-xl">💡</span>
          <div>
            <p className={`text-sm font-medium ${theme === "dark" ? "text-blue-400" : "text-blue-900"}`}>
              How Price Alerts Work
            </p>
            <p className={`text-xs mt-1 ${theme === "dark" ? "text-blue-300/70" : "text-blue-700/70"}`}>
              We check prices every 5 minutes. When your target is reached, you'll receive an email notification. 
              You can create multiple alerts and pause them anytime.
            </p>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateAlertModal
          onClose={() => setShowCreateModal(false)}
          onCreate={handleCreateAlert}
          wallets={wallets}
        />
      )}

      {showPreferencesModal && (
        <EmailPreferencesModal
          onClose={() => setShowPreferencesModal(false)}
        />
      )}
    </div>
  );
};

export default AlertsPage;