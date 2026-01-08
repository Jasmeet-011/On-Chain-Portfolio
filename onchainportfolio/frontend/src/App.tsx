// src/App.tsx - UPDATED: Added Toast Notifications Support
import React, { useState, useEffect } from "react";
import { Toaster } from "react-hot-toast";
import { WalletProvider } from "./context/WalletProvider";
import { SolanaWalletProvider } from "./context/SolanaWalletProvider";
import { AppProvider, useAppContext } from "./context/AppContext";
import Sidebar, { type TabType } from "./components/Sidebar";
import Header from "./components/Header";

import HomePage from "./pages/HomePage";
import AnalyticsPage from "./pages/AnalyticsPage";
import TransactionsPage from "./pages/TransactionsPage";
import ChatPage from "./pages/ChatPage";
import AlertsPage from "./pages/AlertsPage";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";

// ✅ Toast Configuration Component (inside AppProvider for theme access)
const ToastConfig: React.FC = () => {
  const { theme } = useAppContext();

  return (
    <Toaster
      position="top-center"
      reverseOrder={false}
      gutter={8}
      toastOptions={{
        duration: 4000,
        style: {
          background: theme === 'dark' ? '#18181b' : '#ffffff',
          color: theme === 'dark' ? '#fafafa' : '#18181b',
          border: theme === 'dark' ? '1px solid #3f3f46' : '1px solid #e5e7eb',
          padding: '12px 16px',
          borderRadius: '12px',
          fontSize: '14px',
          fontWeight: '500',
          boxShadow: theme === 'dark'
            ? '0 10px 40px rgba(0, 0, 0, 0.4)'
            : '0 10px 40px rgba(0, 0, 0, 0.1)',
        },
        success: {
          duration: 3000,
          iconTheme: {
            primary: '#10b981',
            secondary: theme === 'dark' ? '#18181b' : '#ffffff',
          },
          style: {
            border: theme === 'dark' ? '1px solid #10b981' : '1px solid #10b981',
          },
        },
        error: {
          duration: 5000,
          iconTheme: {
            primary: '#ef4444',
            secondary: theme === 'dark' ? '#18181b' : '#ffffff',
          },
          style: {
            border: theme === 'dark' ? '1px solid #ef4444' : '1px solid #ef4444',
          },
        },
        loading: {
          duration: Infinity,
          style: {
            background: theme === 'dark' ? '#18181b' : '#ffffff',
            color: theme === 'dark' ? '#a1a1aa' : '#71717a',
          },
        },
      }}
    />
  );
};

const AppShell: React.FC = () => {
  const { theme, currentUser, setCurrentUser, logout } = useAppContext();

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    const user = localStorage.getItem("user");
    return !!user;
  });

  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const [activeTab, setActiveTab] = useState<TabType>("home");

  // Sidebar collapse state (responsive: collapsed on mobile by default)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.innerWidth < 1024;
  });

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser && !currentUser) {
      try {
        const user = JSON.parse(storedUser);
        setCurrentUser({
          id: user.id,
          name: user.name,
          email: user.email,
        });
        setIsAuthenticated(true);
      } catch (error) {
        console.error("Failed to parse stored user:", error);
        localStorage.removeItem("user");
        setIsAuthenticated(false);
      }
    }
  }, []);

  // Handle window resize for responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setIsSidebarCollapsed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
    setAuthMode("signin");
    setActiveTab("home");
  };

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);

    // Auto-collapse sidebar on mobile after navigation
    if (window.innerWidth < 1024) {
      setIsSidebarCollapsed(true);
    }
  };

  // Auth screens
  if (!isAuthenticated) {
    if (authMode === "signin") {
      return (
        <>
          <ToastConfig />
          <SignInPage
            onSwitchToSignUp={() => setAuthMode("signup")}
            onSignedIn={() => {
              setIsAuthenticated(true);
              setActiveTab("home");
            }}
          />
        </>
      );
    }

    return (
      <>
        <ToastConfig />
        <SignUpPage
          onSwitchToSignIn={() => setAuthMode("signin")}
          onSignedUp={() => {
            setIsAuthenticated(true);
            setActiveTab("home");
          }}
        />
      </>
    );
  }

  // Main app with sidebar layout
  return (
    <div
      className={`min-h-screen transition-colors duration-200 ${theme === "dark" ? "bg-zinc-950" : "bg-slate-50"
        }`}
    >
      {/* ✅ Toast Notifications */}
      <ToastConfig />

      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div
        className={`transition-all duration-300 ${isSidebarCollapsed ? "lg:ml-20" : "lg:ml-64"
          }`}
      >
        {/* Header */}
        <Header onLogout={handleLogout} />

        {/* Page Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {activeTab === "home" && <HomePage onNavigateToAnalytics={() => setActiveTab('analytics')} />}
          {activeTab === "analytics" && <AnalyticsPage />}
          {activeTab === "transactions" && <TransactionsPage />}
          {activeTab === "alerts" && <AlertsPage />}
          {activeTab === "chat" && <ChatPage />}
        </main>
      </div>

      {/* Mobile Menu Button - Fixed position on mobile */}
      <button
        onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        className={`fixed bottom-6 right-6 lg:hidden z-50 p-4 rounded-full shadow-lg transition-colors ${theme === "dark"
            ? "bg-blue-600 text-white hover:bg-blue-700"
            : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isSidebarCollapsed ? (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          ) : (
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          )}
        </svg>
      </button>
    </div>
  );
};

// Correct provider nesting order
const App: React.FC = () => (
  <WalletProvider>
    <SolanaWalletProvider>
      <AppProvider>
        <AppShell />
      </AppProvider>
    </SolanaWalletProvider>
  </WalletProvider>
);

export default App;