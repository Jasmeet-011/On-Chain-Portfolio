// src/components/Sidebar.tsx
import React from "react";
import { useAppContext } from "../context/AppContext";
import { Home, BarChart3, Receipt, MessageSquare, Bell, ChevronLeft } from "lucide-react";
import Logo from "./Logo";

export type TabType = "home" | "analytics" | "transactions" | "alerts" | "chat";

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}


const TAB_ACCENTS: Record<TabType, string> = {
  home:         "#627EEA",
  analytics:    "#10B981",
  transactions: "#F59E0B",
  alerts:       "#EF4444",
  chat:         "#9945FF",
};

const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange, isCollapsed, onToggleCollapse }) => {
  const { theme } = useAppContext();
  const isDark = theme === "dark";

  const tabs = [
    { id: "home"         as TabType, label: "Portfolio",    icon: Home,         description: "Overview"        },
    { id: "analytics"    as TabType, label: "Analytics",    icon: BarChart3,     description: "Charts & History" },
    { id: "transactions" as TabType, label: "Transactions", icon: Receipt,       description: "Activity Log"    },
    { id: "alerts"       as TabType, label: "Alerts",       icon: Bell,          description: "Price Alerts"    },
    { id: "chat"         as TabType, label: "AI Assistant", icon: MessageSquare, description: "Ask Questions"   },
  ];

  return (
    <>
      <aside
        className={`fixed left-0 top-0 h-full z-40 transition-all duration-300 flex flex-col ${
          isCollapsed ? "w-20" : "w-64"
        } ${isDark ? "bg-zinc-950 border-r border-zinc-800" : "bg-white border-r border-gray-200"}`}
      >
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b ${isDark ? "border-zinc-800" : "border-gray-200"}`}>
          {isCollapsed
            ? <Logo size="md" theme={theme} iconOnly />
            : <Logo size="md" theme={theme} />
          }
          <button
            onClick={onToggleCollapse}
            className={`p-2 rounded-lg transition-colors ${
              isDark
                ? "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-300"
                : "hover:bg-gray-100 text-gray-600 hover:text-gray-900"
            } ${isCollapsed ? "mx-auto" : ""}`}
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <ChevronLeft className={`w-5 h-5 transition-transform duration-300 ${isCollapsed ? "rotate-180" : ""}`} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            const accentColor = TAB_ACCENTS[tab.id];

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative overflow-hidden ${
                  isCollapsed ? "justify-center" : ""
                } ${
                  isActive
                    ? isDark ? "bg-zinc-800/80 text-white" : "bg-gray-100 text-gray-900"
                    : isDark ? "text-zinc-400 hover:text-white hover:bg-zinc-800/40" : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
                style={isActive && isDark ? { boxShadow: `inset 0 0 0 1px ${accentColor}22` } : {}}
                title={isCollapsed ? tab.label : ""}
              >
                {/* Accent left stripe */}
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 rounded-full"
                    style={{ background: accentColor }}
                  />
                )}

                <Icon
                  className="w-5 h-5 shrink-0 transition-all duration-200 group-hover:scale-110"
                  style={isActive ? { color: accentColor } : {}}
                />

                {!isCollapsed && (
                  <div className="flex-1 text-left">
                    <div className="text-sm font-medium">{tab.label}</div>
                    <div className={`text-xs ${
                      isDark
                        ? isActive ? "text-zinc-400" : "text-zinc-600"
                        : isActive ? "text-gray-500" : "text-gray-400"
                    }`}>
                      {tab.description}
                    </div>
                  </div>
                )}

                {/* Active dot below icon in collapsed mode */}
                {isActive && isCollapsed && (
                  <span
                    className="absolute bottom-1.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
                    style={{ background: accentColor }}
                  />
                )}
              </button>
            );
          })}
        </nav>

      </aside>

      {/* Mobile overlay */}
      {!isCollapsed && (
        <div className="fixed inset-0 bg-black/50 z-30 lg:hidden backdrop-blur-sm" onClick={onToggleCollapse} />
      )}
    </>
  );
};

export default Sidebar;
