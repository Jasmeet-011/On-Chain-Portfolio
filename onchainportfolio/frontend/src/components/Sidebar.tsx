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
    { id: "home"         as TabType, label: "Portfolio",    icon: Home         },
    { id: "analytics"    as TabType, label: "Analytics",    icon: BarChart3    },
    { id: "transactions" as TabType, label: "Transactions", icon: Receipt      },
    { id: "alerts"       as TabType, label: "Alerts",       icon: Bell         },
    { id: "chat"         as TabType, label: "AI Assistant", icon: MessageSquare },
  ];

  return (
    <>
      <aside
        className={`fixed left-0 top-0 h-full z-40 transition-all duration-300 flex flex-col ${
          isCollapsed ? "w-17" : "w-60"
        } ${isDark ? "bg-zinc-950 border-r border-zinc-800/80" : "bg-white border-r border-gray-200"}`}
      >
        {/* Logo row */}
        <div className={`flex items-center h-14 px-3 border-b ${isDark ? "border-zinc-800/80" : "border-gray-200"}`}>
          {isCollapsed ? (
            <button
              onClick={onToggleCollapse}
              className={`mx-auto p-1.5 rounded-lg transition-colors ${
                isDark ? "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" : "hover:bg-gray-100 text-gray-500 hover:text-gray-900"
              }`}
              title="Expand sidebar"
            >
              <ChevronLeft className="w-5 h-5 rotate-180" />
            </button>
          ) : (
            <>
              <Logo size="md" theme={theme} className="flex-1" />
              <button
                onClick={onToggleCollapse}
                className={`p-1.5 rounded-lg transition-colors shrink-0 ${
                  isDark ? "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200" : "hover:bg-gray-100 text-gray-500 hover:text-gray-900"
                }`}
                title="Collapse sidebar"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            const accent = TAB_ACCENTS[tab.id];

            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 relative ${
                  isCollapsed ? "justify-center" : ""
                } ${
                  isActive
                    ? isDark ? "bg-zinc-800/80 text-white" : "bg-gray-100 text-gray-900"
                    : isDark ? "text-zinc-400 hover:text-white hover:bg-zinc-800/50" : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                }`}
                title={isCollapsed ? tab.label : undefined}
              >
                {/* Active left stripe */}
                {isActive && (
                  <span
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                    style={{ background: accent }}
                  />
                )}

                <Icon
                  className="w-4.5 h-4.5 shrink-0 transition-colors"
                  style={isActive ? { color: accent } : {}}
                />

                {!isCollapsed && (
                  <span className="text-sm font-medium">{tab.label}</span>
                )}

                {/* Active dot in collapsed mode */}
                {isActive && isCollapsed && (
                  <span
                    className="absolute bottom-1.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full"
                    style={{ background: accent }}
                  />
                )}
              </button>
            );
          })}
        </nav>
      </aside>

      {/* Mobile overlay */}
      {!isCollapsed && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden backdrop-blur-sm"
          onClick={onToggleCollapse}
        />
      )}
    </>
  );
};

export default Sidebar;
