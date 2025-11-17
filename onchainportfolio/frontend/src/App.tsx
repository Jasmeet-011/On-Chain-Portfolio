// src/App.tsx
import React, { useState } from "react";
import { AppProvider, useAppContext } from "./context/AppContext";
import Header from "./components/Header";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";

const AppShell: React.FC = () => {
  const { theme } = useAppContext();

  // NEW: simple auth state
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("user");
  });
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");

  const [activeTab, setActiveTab] = useState<"chat" | "dashboard">("chat");

  // 🔐 If user is NOT logged in, show auth screens instead of dashboard/chat
  if (!isAuthenticated) {
    if (authMode === "signin") {
      return (
       <SignInPage
        onSwitchToSignUp={() => setAuthMode("signup")}
        onSignedIn={() => {
          setIsAuthenticated(true);
          setActiveTab("dashboard");  // 👈 redirect to dashboard
        }}
      />
      );
    }

    return (
      <SignUpPage
      onSwitchToSignIn={() => setAuthMode("signin")}
      onSignedUp={() => {
        setIsAuthenticated(true);
        setActiveTab("dashboard");  // 👈 redirect to dashboard
      }}
    />
    );
  }

  // ✅ After login/signup, show your existing UI
  return (
    <div
      className={`min-h-screen transition-colors duration-200 ${
        theme === "dark"
          ? "bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800"
          : "bg-gradient-to-br from-gray-50 via-white to-gray-100"
      }`}
    >
      <Header />

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8 flex gap-3">
          <button
            onClick={() => setActiveTab("chat")}
            className={`px-8 py-3 rounded-xl font-semibold transition-all duration-200 ${
              activeTab === "chat"
                ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/50"
                : theme === "dark"
                ? "bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700"
                : "bg-white text-gray-600 hover:bg-gray-50 border border-gray-200"
            }`}
          >
            💬 Chat
          </button>
          <button
            onClick={() => setActiveTab("dashboard")}
            className={`px-8 py-3 rounded-xl font-semibold transition-all duration-200 ${
              activeTab === "dashboard"
                ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/50"
                : theme === "dark"
                ? "bg-gray-800 text-gray-400 hover:bg-gray-700 border border-gray-700"
                : "bg-white text-gray-600 hover:bg-gray-50 border border-gray-200"
            }`}
          >
            📊 Dashboard
          </button>
        </div>

        <div className="min-h-[600px]">
          {activeTab === "chat" ? <ChatPage /> : <DashboardPage />}
        </div>
      </div>

      {/* Decorative gradient orbs */}
      <div className="fixed top-0 left-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -z-10"></div>
      <div className="fixed bottom-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl -z-10"></div>
    </div>
  );
};

const App: React.FC = () => (
  <AppProvider>
    <AppShell />
  </AppProvider>
);

export default App;
