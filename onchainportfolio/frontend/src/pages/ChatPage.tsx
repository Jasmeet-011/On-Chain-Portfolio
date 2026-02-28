// src/pages/ChatPage.tsx - PROFESSIONAL: Black/White/Gray Theme
import React, { useState, useRef, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import {
  MessageCircle,
  Loader2,
  Sparkles,
  TrendingUp,
  Image as ImageIcon,
  BarChart3,
  CheckCircle2,
  XCircle,
  Settings,
} from "lucide-react";

const ChatPage: React.FC = () => {
  const {
    messages,
    addMessage,
    manualAddress,
    theme,
    isLoading,
    setIsLoading,
    wallets,
  } = useAppContext();

  const [inputMessage, setInputMessage] = useState("");
  const [scope, setScope] = useState<string>("all");
  const [walletResults, setWalletResults] = useState<any[]>([]);
  const [portfolioSummary, setPortfolioSummary] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputMessage.trim() || !manualAddress) return;

    const userMessage = inputMessage.trim();
    setInputMessage("");

    addMessage({
      role: "user",
      text: userMessage,
    });

    setIsLoading(true);
    setWalletResults([]);
    setPortfolioSummary(null);

    try {
      const response = await api.chat(userMessage, scope);

      if (response.wallet_results) {
        setWalletResults(response.wallet_results);
      }
      if (response.portfolio) {
        setPortfolioSummary(response.portfolio);
      }

      addMessage({
        role: "assistant",
        text: response.answer,
        data: response.portfolio,
      });
    } catch (error: any) {
      console.error("Chat error:", error);
      
      let errorMessage = "Sorry, I encountered an error. Please try again.";
      
      if (error.message) {
        if (error.message.includes("401")) {
          errorMessage = "Your session has expired. Please log in again.";
        } else if (error.message.includes("404")) {
          errorMessage = "No wallets found. Please add a wallet first.";
        } else if (error.message.includes("502")) {
          errorMessage = "Failed to fetch portfolio data. Please check your wallets and try again.";
        }
      }
      
      addMessage({
        role: "assistant",
        text: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    { icon: TrendingUp, text: "What tokens do I hold?", color: theme === "dark" ? "text-zinc-400" : "text-gray-600" },
    { icon: BarChart3, text: "What's my portfolio value in USD?", color: theme === "dark" ? "text-zinc-400" : "text-gray-600" },
    { icon: ImageIcon, text: "Show my NFTs", color: theme === "dark" ? "text-zinc-400" : "text-gray-600" },
    { icon: Sparkles, text: "What's my largest holding?", color: theme === "dark" ? "text-zinc-400" : "text-gray-600" },
  ];

  const handleQuickAction = (text: string) => {
    setInputMessage(text);
  };

  const getScopeOptions = () => {
    const options = [
      { value: "all", label: "All Wallets", count: wallets.length },
      { value: "primary", label: "Primary Wallet Only", count: 1 },
    ];

    wallets.forEach((wallet) => {
      const chainEmoji = wallet.chain === 'aptos' ? '⬢' : '◎';
      options.push({
        value: wallet.address,
        label: `${chainEmoji} ${wallet.label || wallet.address.substring(0, 10) + "..."}`,
        count: 1,
      });
    });

    return options;
  };

  const scopeOptions = getScopeOptions();
  const aptosCount = wallets.filter(w => w.chain === 'aptos').length;
  const solanaCount = wallets.filter(w => w.chain === 'solana').length;

  // No wallet connected
  if (!manualAddress) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className={`rounded-xl p-16 text-center max-w-md ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-6 ${
            theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
          }`}>
            <MessageCircle className={`w-8 h-8 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
          </div>
          <h3 className={`text-2xl font-bold mb-3 ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}>
            Connect Your Wallet
          </h3>
          <p className={theme === "dark" ? "text-zinc-400" : "text-gray-600"}>
            Please connect your wallet to start chatting about your portfolio
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-6 h-[calc(100vh-200px)]">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <div className={`flex-1 rounded-xl overflow-hidden flex flex-col ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          {/* Chat Header */}
          <div className={`border-b p-4 flex items-center justify-between ${
            theme === "dark" ? "border-zinc-800" : "border-gray-200"
          }`}>
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                theme === "dark"
                  ? "bg-linear-to-br from-blue-500 to-purple-600 text-white"
                  : "bg-black text-white"
              }`}>
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h3 className={`font-semibold ${
                  theme === "dark" ? "text-white" : "text-gray-900"
                }`}>
                  Portfolio Assistant
                </h3>
                <p className={`text-xs ${
                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                }`}>
                  Ask me about your multi-chain portfolio
                </p>
              </div>
            </div>

            {/* Scope Selector */}
            <div className="flex items-center gap-2">
              <span className={`text-sm ${
                theme === "dark" ? "text-zinc-400" : "text-gray-600"
              }`}>
                Analyzing:
              </span>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value)}
                disabled={isLoading}
                className={`px-3 py-2 rounded-lg border text-sm focus:outline-none focus:ring-2 ${
                  theme === "dark"
                    ? "bg-zinc-800 border-zinc-700 text-white focus:ring-white focus:border-white"
                    : "bg-white border-gray-200 text-gray-900 focus:ring-black focus:border-black"
                } disabled:opacity-50`}
              >
                {scopeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                    {option.value === "all" && option.count > 0 ? ` (${option.count})` : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className={`w-16 h-16 rounded-xl flex items-center justify-center mb-4 ${
                  theme === "dark"
                    ? "bg-linear-to-br from-blue-500 to-purple-600 text-white"
                    : "bg-black text-white"
                }`}>
                  <Sparkles className="w-8 h-8" />
                </div>
                <h3 className={`text-xl font-bold mb-2 ${
                  theme === "dark" ? "text-white" : "text-gray-900"
                }`}>
                  Welcome to ChainLens
                </h3>
                <p className={`max-w-md mb-4 ${
                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                }`}>
                  Ask me anything about your portfolio across{" "}
                  {wallets.length} wallet{wallets.length !== 1 ? "s" : ""}
                  {(aptosCount > 0 && solanaCount > 0) && (
                    <span> ({aptosCount} Aptos, {solanaCount} Solana)</span>
                  )}
                </p>

                {portfolioSummary && (
                  <div className={`mt-4 p-4 rounded-lg border ${
                    theme === "dark"
                      ? "bg-zinc-800/50 border-zinc-700"
                      : "bg-gray-50 border-gray-200"
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className={`w-5 h-5 ${theme === "dark" ? "text-zinc-400" : "text-gray-600"}`} />
                      <span className={`text-sm font-medium ${
                        theme === "dark" ? "text-zinc-300" : "text-gray-700"
                      }`}>
                        Portfolio Overview
                      </span>
                    </div>
                    <div className="text-left space-y-1">
                      <p className={`text-xs ${
                        theme === "dark" ? "text-zinc-400" : "text-gray-600"
                      }`}>
                        Total Value:{" "}
                        <span className="font-semibold text-green-500">
                          ${portfolioSummary.total_usd_value?.toFixed(2)}
                        </span>
                      </p>
                      <p className={`text-xs ${
                        theme === "dark" ? "text-zinc-400" : "text-gray-600"
                      }`}>
                        Wallets: {portfolioSummary.successful_wallets}/{portfolioSummary.total_wallets} analyzed
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <>
                {messages.map((msg, idx) => (
                  <div key={idx}>
                    <div className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}>
                      <div className={`max-w-[80%] rounded-xl px-4 py-3 ${
                        msg.role === "user"
                          ? theme === "dark"
                            ? "bg-blue-600 text-white"
                            : "bg-black text-white"
                          : theme === "dark"
                          ? "bg-zinc-800 border border-zinc-700/60 text-zinc-200"
                          : "bg-gray-100 text-gray-900"
                      }`}>
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      </div>
                    </div>

                    {/* Wallet Results */}
                    {msg.role === "assistant" && idx === messages.length - 1 && walletResults.length > 0 && (
                      <div className={`mt-3 ml-0 max-w-[80%] p-3 rounded-lg border text-xs ${
                        theme === "dark"
                          ? "bg-zinc-800/50 border-zinc-700 text-zinc-300"
                          : "bg-gray-50 border-gray-200 text-gray-700"
                      }`}>
                        <div className="flex items-center gap-2 mb-2">
                          <Settings className="w-4 h-4" />
                          <span className="font-medium">Wallet Analysis</span>
                        </div>
                        <div className="space-y-1">
                          {walletResults.map((result, i) => (
                            <div key={i} className="flex items-start gap-2 py-1">
                              {result.success ? (
                                <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                              ) : (
                                <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                              )}
                              <div className="flex-1">
                                <div className="flex items-center gap-1">
                                  <span className="font-medium">{result.label}</span>
                                  {result.chain && (
                                    <span className={`text-[10px] px-1 py-0.5 rounded ${
                                      result.chain === 'aptos'
                                        ? theme === "dark"
                                          ? "bg-zinc-700 text-zinc-300"
                                          : "bg-gray-200 text-gray-700"
                                        : theme === "dark"
                                        ? "bg-zinc-700 text-zinc-300"
                                        : "bg-gray-200 text-gray-700"
                                    }`}>
                                      {result.chain.toUpperCase()}
                                    </span>
                                  )}
                                </div>
                                <div className={`text-xs ${
                                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                                }`}>
                                  {result.address.substring(0, 10)}...
                                </div>
                                {!result.success && result.error && (
                                  <div className="text-xs text-red-400 mt-1">
                                    Error: {result.error}
                                  </div>
                                )}
                                {result.success && result.data && (
                                  <div className="text-xs text-green-500 mt-1">
                                    ${result.data.total_usd_value?.toFixed(2) || "0.00"}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className={`rounded-xl px-4 py-3 ${
                      theme === "dark" ? "bg-zinc-800" : "bg-gray-100"
                    }`}>
                      <div className="flex items-center gap-2">
                        <Loader2 className={`w-4 h-4 animate-spin ${
                          theme === "dark" ? "text-white" : "text-black"
                        }`} />
                        <span className={`text-sm ${
                          theme === "dark" ? "text-zinc-400" : "text-gray-600"
                        }`}>
                          Analyzing{" "}
                          {scope === "all"
                            ? `${wallets.length} wallets`
                            : scope === "primary"
                            ? "primary wallet"
                            : "wallet"}
                          ...
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className={`border-t p-4 ${
            theme === "dark" ? "border-zinc-800" : "border-gray-200"
          }`}>
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isLoading}
                className={`flex-1 px-4 py-3 rounded-lg border focus:outline-none focus:ring-2 ${
                  theme === "dark"
                    ? "bg-zinc-800 border-zinc-700 text-white placeholder-zinc-400 focus:ring-white focus:border-white"
                    : "bg-white border-gray-200 text-gray-900 placeholder-gray-500 focus:ring-black focus:border-black"
                } disabled:opacity-50`}
              />
              <button
                onClick={handleSend}
                disabled={!inputMessage.trim() || isLoading}
                className={`p-3 rounded-lg font-medium transition-colors flex items-center justify-center ${
                  theme === "dark"
                    ? "bg-blue-600 text-white hover:bg-blue-500"
                    : "bg-black text-white hover:bg-gray-800"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 10l7-7m0 0l7 7m-7-7v18"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions Sidebar */}
      <div className="w-80">
        <div className={`rounded-xl p-6 mb-4 ${
          theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
        }`}>
          <h3 className={`text-lg font-bold mb-4 ${
            theme === "dark" ? "text-white" : "text-gray-900"
          }`}>
            Quick Actions
          </h3>
          <div className="space-y-3">
            {quickActions.map((action, idx) => {
              const Icon = action.icon;
              return (
                <button
                  key={idx}
                  onClick={() => handleQuickAction(action.text)}
                  disabled={isLoading}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                    theme === "dark"
                      ? "bg-zinc-800 hover:bg-zinc-700 text-zinc-200"
                      : "bg-gray-100 hover:bg-gray-200 text-gray-900"
                  } disabled:opacity-50`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-5 h-5 ${action.color}`} />
                    <span className="text-sm">{action.text}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Portfolio Stats */}
        {portfolioSummary && (
          <div className={`rounded-xl p-6 ${
            theme === "dark" ? "bg-zinc-900 border border-zinc-800" : "bg-white border border-gray-200 shadow-sm"
          }`}>
            <h3 className={`text-lg font-bold mb-4 ${
              theme === "dark" ? "text-white" : "text-gray-900"
            }`}>
              Portfolio Stats
            </h3>
            <div className="space-y-3">
              <div>
                <div className={`text-xs mb-1 ${
                  theme === "dark" ? "text-zinc-400" : "text-gray-600"
                }`}>
                  Total Value
                </div>
                <div className="text-2xl font-bold text-green-500">
                  ${portfolioSummary.total_usd_value?.toFixed(2) || "0.00"}
                </div>
              </div>

              <div className="flex gap-4">
                <div>
                  <div className={`text-xs mb-1 ${
                    theme === "dark" ? "text-zinc-400" : "text-gray-600"
                  }`}>
                    Wallets
                  </div>
                  <div className={`text-lg font-semibold ${
                    theme === "dark" ? "text-white" : "text-gray-900"
                  }`}>
                    {portfolioSummary.total_wallets}
                  </div>
                </div>

                <div>
                  <div className={`text-xs mb-1 ${
                    theme === "dark" ? "text-zinc-400" : "text-gray-600"
                  }`}>
                    Successful
                  </div>
                  <div className="text-lg font-semibold text-green-500">
                    {portfolioSummary.successful_wallets}
                  </div>
                </div>

                {portfolioSummary.failed_wallets > 0 && (
                  <div>
                    <div className={`text-xs mb-1 ${
                      theme === "dark" ? "text-zinc-400" : "text-gray-600"
                    }`}>
                      Failed
                    </div>
                    <div className="text-lg font-semibold text-red-400">
                      {portfolioSummary.failed_wallets}
                    </div>
                  </div>
                )}
              </div>

              {portfolioSummary.by_chain && (
                <div className={`pt-3 border-t ${
                  theme === "dark" ? "border-zinc-800" : "border-gray-200"
                }`}>
                  <div className={`text-xs mb-2 ${
                    theme === "dark" ? "text-zinc-400" : "text-gray-600"
                  }`}>
                    By Chain
                  </div>
                  <div className="space-y-2">
                    {Object.entries(portfolioSummary.by_chain).map(([chain, count]: any) => (
                      <div key={chain} className="flex justify-between items-center">
                        <span className={`text-sm font-medium flex items-center gap-1 ${
                          theme === "dark" ? "text-zinc-300" : "text-gray-700"
                        }`}>
                          <span>{chain === 'aptos' ? '⬢' : '◎'}</span>
                          {chain.charAt(0).toUpperCase() + chain.slice(1)}
                        </span>
                        <span className={`text-sm ${
                          theme === "dark" ? "text-zinc-400" : "text-gray-600"
                        }`}>
                          {count} wallet{count !== 1 ? 's' : ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {portfolioSummary.by_token && portfolioSummary.by_token.length > 0 && (
                <div className={`pt-3 border-t ${
                  theme === "dark" ? "border-zinc-800" : "border-gray-200"
                }`}>
                  <div className={`text-xs mb-2 ${
                    theme === "dark" ? "text-zinc-400" : "text-gray-600"
                  }`}>
                    Top Holdings
                  </div>
                  <div className="space-y-2">
                    {portfolioSummary.by_token.slice(0, 3).map((token: any, i: number) => (
                      <div key={i} className="flex justify-between items-center">
                        <span className={`text-sm font-medium ${
                          theme === "dark" ? "text-zinc-300" : "text-gray-700"
                        }`}>
                          {token.symbol}
                        </span>
                        <span className={`text-sm ${
                          theme === "dark" ? "text-zinc-400" : "text-gray-600"
                        }`}>
                          ${token.total_usd_value?.toFixed(2) || "0.00"}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;