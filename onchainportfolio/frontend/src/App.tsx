// src/App.tsx - CONSISTENT COLOR THEME (Blue Only)
import React, { useState } from "react";
import { AppProvider, useAppContext } from "./context/AppContext";
import Header from "./components/Header";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";

const AppShell: React.FC = () => {
  const { theme } = useAppContext();

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    const user = localStorage.getItem("user");
    return !!user;
  });

  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  const [activeTab, setActiveTab] = useState<"dashboard" | "chat">("dashboard");

  const handleLogout = () => {
    localStorage.removeItem("user");
    setIsAuthenticated(false);
    setAuthMode("signin");
  };

  // Auth screens
  if (!isAuthenticated) {
    if (authMode === "signin") {
      return (
        <SignInPage
          onSwitchToSignUp={() => setAuthMode("signup")}
          onSignedIn={() => {
            setIsAuthenticated(true);
            setActiveTab("dashboard");
          }}
        />
      );
    }

    return (
      <SignUpPage
        onSwitchToSignIn={() => setAuthMode("signin")}
        onSignedUp={() => {
          setIsAuthenticated(true);
          setActiveTab("dashboard");
        }}
      />
    );
  }

  // Main app
  return (
    <div
      className={`min-h-screen ${
        theme === "dark"
          ? "bg-slate-900"
          : "bg-slate-50"
      }`}
    >
      <Header onLogout={handleLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Navigation Tabs - CONSISTENT BLUE */}
        <div className={`inline-flex rounded-lg p-1 mb-6 ${
          theme === "dark" ? "bg-slate-800 border border-slate-700" : "bg-white border border-slate-200 shadow-sm"
        }`}>
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`px-6 py-2.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === "dashboard"
                ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
                : theme === "dark"
                ? "text-slate-400 hover:text-white hover:bg-slate-700"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <span className="mr-2">📊</span>
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`px-6 py-2.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === "chat"
                ? "bg-blue-600 text-white shadow-lg shadow-blue-600/30"
                : theme === "dark"
                ? "text-slate-400 hover:text-white hover:bg-slate-700"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            <span className="mr-2">💬</span>
            AI Assistant
          </button>
        </div>

        {/* Page Content */}
        {activeTab === "dashboard" ? <DashboardPage /> : <ChatPage />}
      </main>
    </div>
  );
};

const App: React.FC = () => (
  <AppProvider>
    <AppShell />
  </AppProvider>
);

export default App;