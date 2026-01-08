// src/components/EmailPreferencesModal.tsx - FIXED: Correct API Endpoints
import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import toast from "react-hot-toast";

interface EmailPreferencesModalProps {
  onClose: () => void;
}

interface EmailPreferences {
  user_id?: string;
  price_alerts_enabled: boolean;
  daily_digest_enabled: boolean;
  weekly_summary_enabled: boolean;
  updated_at?: string;
}

const EmailPreferencesModal: React.FC<EmailPreferencesModalProps> = ({ onClose }) => {
  const { theme } = useAppContext();
  
  const [preferences, setPreferences] = useState<EmailPreferences>({
    price_alerts_enabled: true,
    daily_digest_enabled: true,
    weekly_summary_enabled: true,
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get auth token
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

  // Load current preferences
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setLoading(true);
    setError(null);

    try {
      // ✅ FIXED: Correct endpoint
      const response = await fetch("http://localhost:8000/v1/alerts/preferences/email", {
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
        },
      });

      if (!response.ok) {
        // If 404, use defaults (preferences not created yet)
        if (response.status === 404) {
          setPreferences({
            price_alerts_enabled: true,
            daily_digest_enabled: true,
            weekly_summary_enabled: true,
          });
          setLoading(false);
          return;
        }
        throw new Error("Failed to load preferences");
      }

      const data = await response.json();
      setPreferences({
        price_alerts_enabled: data.price_alerts_enabled ?? true,
        daily_digest_enabled: data.daily_digest_enabled ?? true,
        weekly_summary_enabled: data.weekly_summary_enabled ?? true,
      });
    } catch (err: any) {
      console.error("Failed to load preferences:", err);
      // Don't show error, just use defaults
      setPreferences({
        price_alerts_enabled: true,
        daily_digest_enabled: true,
        weekly_summary_enabled: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    const toastId = toast.loading("Saving preferences...");

    try {
      // ✅ FIXED: Correct endpoint and method (PUT, not POST)
      const response = await fetch("http://localhost:8000/v1/alerts/preferences/email", {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${getAuthToken()}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          price_alerts_enabled: preferences.price_alerts_enabled,
          daily_digest_enabled: preferences.daily_digest_enabled,
          weekly_summary_enabled: preferences.weekly_summary_enabled,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to save preferences");
      }

      toast.success("Preferences saved!", { id: toastId });
      
      // Close modal after short delay
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err: any) {
      console.error("Failed to save preferences:", err);
      toast.error(err.message || "Failed to save preferences", { id: toastId });
      setError(err.message || "Failed to save preferences");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key: keyof EmailPreferences) => {
    setPreferences(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`relative w-full max-w-lg rounded-xl shadow-2xl ${
          theme === "dark"
            ? "bg-slate-800 border border-slate-700"
            : "bg-white border border-slate-200"
        }`}
      >
        {/* Header */}
        <div className={`px-6 py-4 border-b ${
          theme === "dark" ? "border-slate-700" : "border-slate-200"
        }`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className={`text-xl font-bold ${
                theme === "dark" ? "text-white" : "text-slate-900"
              }`}>
                Email Preferences
              </h3>
              <p className={`text-sm mt-1 ${
                theme === "dark" ? "text-slate-400" : "text-slate-600"
              }`}>
                Manage your notification settings
              </p>
            </div>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${
                theme === "dark"
                  ? "hover:bg-slate-700 text-slate-400"
                  : "hover:bg-slate-100 text-slate-600"
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Loading State */}
          {loading && (
            <div className="flex justify-center py-8">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Preferences */}
          {!loading && (
            <div className="space-y-4">
              {/* Price Alerts */}
              <div className={`p-4 rounded-lg border ${
                theme === "dark" ? "border-slate-700 bg-slate-900/50" : "border-slate-200 bg-slate-50"
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">🔔</span>
                      <h4 className={`font-semibold ${
                        theme === "dark" ? "text-white" : "text-slate-900"
                      }`}>
                        Price Alerts
                      </h4>
                    </div>
                    <p className={`text-sm mt-1 ${
                      theme === "dark" ? "text-slate-400" : "text-slate-600"
                    }`}>
                      Receive emails when your price alerts are triggered
                    </p>
                  </div>
                  
                  <button
                    onClick={() => handleToggle('price_alerts_enabled')}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      preferences.price_alerts_enabled
                        ? "bg-blue-600"
                        : theme === "dark"
                        ? "bg-slate-700"
                        : "bg-slate-300"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        preferences.price_alerts_enabled ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Daily Digest */}
              <div className={`p-4 rounded-lg border ${
                theme === "dark" ? "border-slate-700 bg-slate-900/50" : "border-slate-200 bg-slate-50"
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">📧</span>
                      <h4 className={`font-semibold ${
                        theme === "dark" ? "text-white" : "text-slate-900"
                      }`}>
                        Daily Digest
                      </h4>
                    </div>
                    <p className={`text-sm mt-1 ${
                      theme === "dark" ? "text-slate-400" : "text-slate-600"
                    }`}>
                      Daily summary of your portfolio performance (9 AM)
                    </p>
                  </div>
                  
                  <button
                    onClick={() => handleToggle('daily_digest_enabled')}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      preferences.daily_digest_enabled
                        ? "bg-blue-600"
                        : theme === "dark"
                        ? "bg-slate-700"
                        : "bg-slate-300"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        preferences.daily_digest_enabled ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Weekly Summary */}
              <div className={`p-4 rounded-lg border ${
                theme === "dark" ? "border-slate-700 bg-slate-900/50" : "border-slate-200 bg-slate-50"
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">📊</span>
                      <h4 className={`font-semibold ${
                        theme === "dark" ? "text-white" : "text-slate-900"
                      }`}>
                        Weekly Summary
                      </h4>
                    </div>
                    <p className={`text-sm mt-1 ${
                      theme === "dark" ? "text-slate-400" : "text-slate-600"
                    }`}>
                      Weekly portfolio report every Sunday at 9 AM
                    </p>
                  </div>
                  
                  <button
                    onClick={() => handleToggle('weekly_summary_enabled')}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      preferences.weekly_summary_enabled
                        ? "bg-blue-600"
                        : theme === "dark"
                        ? "bg-slate-700"
                        : "bg-slate-300"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        preferences.weekly_summary_enabled ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Info Note */}
              <div className={`p-3 rounded-lg text-xs ${
                theme === "dark" ? "bg-blue-500/10 text-blue-300" : "bg-blue-50 text-blue-700"
              }`}>
                💡 You can change these settings anytime. All emails include an unsubscribe link.
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className={`px-6 py-4 border-t flex gap-3 ${
          theme === "dark" ? "border-slate-700" : "border-slate-200"
        }`}>
          <button
            onClick={onClose}
            disabled={saving}
            className={`flex-1 px-6 py-3 rounded-lg font-medium transition-colors ${
              theme === "dark"
                ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            } disabled:opacity-50`}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Saving...</span>
              </div>
            ) : (
              "Save Preferences"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailPreferencesModal;