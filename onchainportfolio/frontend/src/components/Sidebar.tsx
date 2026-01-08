// src/components/Sidebar.tsx - PROFESSIONAL: Black/White/Gray Theme + Alerts
import React from "react";
import { useAppContext } from "../context/AppContext";
import { Home, BarChart3, Receipt, MessageSquare, Bell, ChevronLeft, Wallet2 } from "lucide-react";
import Logo from "./Logo";

export type TabType = "home" | "analytics" | "transactions" | "alerts" | "chat";

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  isCollapsed,
  onToggleCollapse,
}) => {
  const { theme, wallets } = useAppContext();

  const tabs = [
    { 
      id: "home" as TabType, 
      label: "Portfolio", 
      icon: Home, 
      description: "Overview" 
    },
    { 
      id: "analytics" as TabType, 
      label: "Analytics", 
      icon: BarChart3, 
      description: "Charts & History" 
    },
    { 
      id: "transactions" as TabType, 
      label: "Transactions", 
      icon: Receipt, 
      description: "Activity Log" 
    },
    { 
      id: "alerts" as TabType, 
      label: "Alerts", 
      icon: Bell, 
      description: "Price Alerts" 
    },
    { 
      id: "chat" as TabType, 
      label: "AI Assistant", 
      icon: MessageSquare, 
      description: "Ask Questions" 
    },
  ];

  // Get wallet stats
  const aptosCount = wallets.filter(w => w.chain === 'aptos').length;
  const solanaCount = wallets.filter(w => w.chain === 'solana').length;

  return (
    <>
      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full z-40 transition-all duration-300 ${
          isCollapsed ? "w-20" : "w-64"
        } ${
          theme === "dark"
            ? "bg-zinc-950 border-r border-zinc-800"
            : "bg-white border-r border-gray-200"
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Header with Logo */}
          <div className={`flex items-center justify-between p-4 border-b ${
            theme === "dark" ? "border-zinc-800" : "border-gray-200"
          }`}>
            {!isCollapsed && (
              <Logo size="md" theme={theme} />
            )}
            {isCollapsed && (
              <Logo size="md" theme={theme} iconOnly />
            )}
            
            {/* Collapse Toggle */}
            <button
              onClick={onToggleCollapse}
              className={`p-2 rounded-lg transition-colors ${
                theme === "dark"
                  ? "hover:bg-zinc-800 text-zinc-400 hover:text-zinc-300"
                  : "hover:bg-gray-100 text-gray-600 hover:text-gray-900"
              } ${isCollapsed ? "mx-auto" : ""}`}
              title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              <ChevronLeft
                className={`w-5 h-5 transition-transform duration-300 ${
                  isCollapsed ? "rotate-180" : ""
                }`}
              />
            </button>
          </div>

          {/* Navigation Items */}
          <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              const Icon = tab.icon;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                    isActive
                      ? theme === "dark"
                        ? "bg-white text-black"
                        : "bg-black text-white"
                      : theme === "dark"
                      ? "text-zinc-400 hover:text-white hover:bg-zinc-800/50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                  } ${isCollapsed ? "justify-center" : ""}`}
                  title={isCollapsed ? tab.label : ""}
                >
                  <Icon className={`w-5 h-5 flex-shrink-0 ${
                    isActive ? "" : "group-hover:scale-110 transition-transform"
                  }`} />
                  
                  {!isCollapsed && (
                    <div className="flex-1 text-left">
                      <div className={`text-sm font-medium ${
                        isActive ? "" : ""
                      }`}>
                        {tab.label}
                      </div>
                      <div className={`text-xs ${
                        isActive
                          ? theme === "dark"
                            ? "text-black/60"
                            : "text-white/70"
                          : theme === "dark"
                          ? "text-zinc-500"
                          : "text-gray-500"
                      }`}>
                        {tab.description}
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Wallet Stats Footer */}
          {!isCollapsed && wallets.length > 0 && (
            <div className={`p-4 border-t ${
              theme === "dark" ? "border-zinc-800" : "border-gray-200"
            }`}>
              <div className={`text-xs font-medium mb-3 ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}>
                Connected Wallets
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className={`p-2 rounded-lg ${
                  theme === "dark" ? "bg-zinc-900" : "bg-gray-50"
                }`}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      theme === "dark" ? "bg-zinc-500" : "bg-gray-400"
                    }`} />
                    <div className={`text-xs ${
                      theme === "dark" ? "text-zinc-500" : "text-gray-500"
                    }`}>
                      Aptos
                    </div>
                  </div>
                  <div className={`text-lg font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}>
                    {aptosCount}
                  </div>
                </div>
                <div className={`p-2 rounded-lg ${
                  theme === "dark" ? "bg-zinc-900" : "bg-gray-50"
                }`}>
                  <div className="flex items-center gap-1.5 mb-1">
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      theme === "dark" ? "bg-zinc-500" : "bg-gray-400"
                    }`} />
                    <div className={`text-xs ${
                      theme === "dark" ? "text-zinc-500" : "text-gray-500"
                    }`}>
                      Solana
                    </div>
                  </div>
                  <div className={`text-lg font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}>
                    {solanaCount}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Collapsed Wallet Count */}
          {isCollapsed && wallets.length > 0 && (
            <div className={`p-4 border-t text-center ${
              theme === "dark" ? "border-zinc-800" : "border-gray-200"
            }`}>
              <Wallet2 className={`w-6 h-6 mx-auto mb-2 ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`} />
              <div className={`text-lg font-bold ${
                theme === "dark" ? "text-white" : "text-gray-900"
              }`}>
                {wallets.length}
              </div>
              <div className={`text-xs ${
                theme === "dark" ? "text-zinc-500" : "text-gray-500"
              }`}>
                Wallets
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Mobile Overlay */}
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