// src/components/EmailPreferencesModal.tsx
import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import { Bell, Mail, BarChart2, X, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { api } from "../api";

interface EmailPreferencesModalProps {
  onClose: () => void;
}

interface LocalEmailPreferences {
  price_alerts_enabled: boolean;
  daily_digest_enabled: boolean;
  weekly_summary_enabled: boolean;
}

const PREFS_CONFIG = [
  {
    key: "price_alerts_enabled" as const,
    icon: <Bell className="w-5 h-5 text-blue-400" />,
    iconBg: "bg-blue-500/10",
    label: "Price Alerts",
    desc: "Receive emails when your price alerts are triggered",
  },
  {
    key: "daily_digest_enabled" as const,
    icon: <Mail className="w-5 h-5 text-emerald-400" />,
    iconBg: "bg-emerald-500/10",
    label: "Daily Digest",
    desc: "Daily summary of your portfolio performance (9 AM)",
  },
  {
    key: "weekly_summary_enabled" as const,
    icon: <BarChart2 className="w-5 h-5 text-purple-400" />,
    iconBg: "bg-purple-500/10",
    label: "Weekly Summary",
    desc: "Weekly portfolio report every Sunday at 9 AM",
  },
];

const EmailPreferencesModal: React.FC<EmailPreferencesModalProps> = ({ onClose }) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";

  const [preferences, setPreferences] = useState<LocalEmailPreferences>({
    price_alerts_enabled: true,
    daily_digest_enabled: true,
    weekly_summary_enabled: true,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadPreferences(); }, []);

  const loadPreferences = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getEmailPreferences();
      setPreferences({
        price_alerts_enabled: data.email_enabled ?? true,
        daily_digest_enabled: data.daily_digest ?? true,
        weekly_summary_enabled: data.weekly_summary ?? true,
      });
    } catch {
      setPreferences({ price_alerts_enabled: true, daily_digest_enabled: true, weekly_summary_enabled: true });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    const toastId = toast.loading("Saving preferences...");
    try {
      await api.updateEmailPreferences({
        email_enabled: preferences.price_alerts_enabled,
        daily_digest: preferences.daily_digest_enabled,
        weekly_summary: preferences.weekly_summary_enabled,
        instant_alerts: true,
      });
      toast.success("Preferences saved!", { id: toastId });
      setTimeout(onClose, 400);
    } catch (err: any) {
      toast.error(err.message || "Failed to save preferences", { id: toastId });
      setError(err.message || "Failed to save preferences");
    } finally {
      setSaving(false);
    }
  };

  const handleToggle = (key: keyof LocalEmailPreferences) => {
    setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className={`relative w-full max-w-md rounded-2xl shadow-2xl ${
        isDark
          ? "bg-zinc-900 border border-zinc-700/60"
          : "bg-white border border-gray-200"
      }`}>

        {/* Header */}
        <div className={`flex items-center justify-between px-6 py-4 border-b ${
          isDark ? "border-zinc-700/60" : "border-gray-200"
        }`}>
          <div>
            <h3 className={`text-lg font-bold ${isDark ? "text-zinc-100" : "text-gray-900"}`}>
              Email Preferences
            </h3>
            <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-500" : "text-gray-500"}`}>
              Manage your notification settings
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-xl transition-colors ${
              isDark ? "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" : "hover:bg-gray-100 text-gray-500"
            }`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex justify-center py-10">
              <Loader2 className="w-7 h-7 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="space-y-3">
              {error && (
                <div className="mb-2 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
                  {error}
                </div>
              )}

              {PREFS_CONFIG.map(({ key, icon, iconBg, label, desc }) => (
                <div
                  key={key}
                  className={`flex items-center gap-4 p-4 rounded-xl border transition-colors ${
                    isDark
                      ? "bg-zinc-800/50 border-zinc-700/60 hover:border-zinc-600"
                      : "bg-gray-50 border-gray-200 hover:border-gray-300"
                  }`}
                >
                  {/* Icon */}
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>
                    {icon}
                  </div>

                  {/* Text */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-semibold ${isDark ? "text-zinc-100" : "text-gray-900"}`}>
                      {label}
                    </p>
                    <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-500" : "text-gray-500"}`}>
                      {desc}
                    </p>
                  </div>

                  {/* Toggle */}
                  <button
                    onClick={() => handleToggle(key)}
                    role="switch"
                    aria-checked={preferences[key]}
                    className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none ${
                      preferences[key] ? "bg-blue-600" : isDark ? "bg-zinc-700" : "bg-gray-300"
                    }`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      preferences[key] ? "translate-x-6" : "translate-x-1"
                    }`} />
                  </button>
                </div>
              ))}

              {/* Info note */}
              <div className={`mt-4 px-4 py-3 rounded-xl text-xs ${
                isDark ? "bg-blue-500/10 text-blue-300 border border-blue-500/20" : "bg-blue-50 text-blue-700"
              }`}>
                All emails include an unsubscribe link. Changes take effect immediately.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={`flex gap-3 px-6 py-4 border-t ${
          isDark ? "border-zinc-700/60" : "border-gray-200"
        }`}>
          <button
            onClick={onClose}
            disabled={saving}
            className={`flex-1 px-5 py-2.5 rounded-xl font-medium text-sm transition-colors disabled:opacity-50 ${
              isDark
                ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700 border border-zinc-700"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || loading}
            className="flex-1 px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Saving…
              </span>
            ) : "Save Preferences"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EmailPreferencesModal;
