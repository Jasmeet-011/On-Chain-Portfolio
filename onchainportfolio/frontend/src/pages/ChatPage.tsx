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
  Send,
} from "lucide-react";
import { getChainColors } from "../utils/tokens";

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
  const isDark = theme === "dark";

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!inputMessage.trim() || !manualAddress) return;

    const userMessage = inputMessage.trim();
    // Capture history BEFORE adding the new user message
    const history = messages.map((m) => ({ role: m.role, text: m.text }));
    setInputMessage("");
    addMessage({ role: "user", text: userMessage });
    setIsLoading(true);
    setWalletResults([]);
    setPortfolioSummary(null);

    try {
      const response = await api.chat(userMessage, scope, history);
      if (response.wallet_results) setWalletResults(response.wallet_results);
      if (response.portfolio) setPortfolioSummary(response.portfolio);
      addMessage({ role: "assistant", text: response.answer, data: response.portfolio });
    } catch (error: any) {
      let errorMessage = "Sorry, I encountered an error. Please try again.";
      if (error.message?.includes("401")) errorMessage = "Your session has expired. Please log in again.";
      else if (error.message?.includes("404")) errorMessage = "No wallets found. Please add a wallet first.";
      else if (error.message?.includes("502")) errorMessage = "Failed to fetch portfolio data. Please check your wallets and try again.";
      addMessage({ role: "assistant", text: errorMessage });
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
    { icon: TrendingUp,  text: "What tokens do I hold?" },
    { icon: BarChart3,   text: "What's my portfolio value in USD?" },
    { icon: ImageIcon,   text: "Show my NFTs" },
    { icon: Sparkles,    text: "What's my largest holding?" },
  ];

  const getScopeOptions = () => {
    const options = [
      { value: "all",     label: `All Wallets (${wallets.length})` },
      { value: "primary", label: "Primary Wallet Only" },
    ];
    wallets.forEach((wallet) => {
      options.push({
        value: wallet.address,
        label: `${wallet.label || wallet.address.slice(0, 10) + "…"}`,
      });
    });
    return options;
  };

  // No wallet connected
  if (!manualAddress) {
    return (
      <div className="flex items-center justify-center min-h-125">
        <div className={`rounded-xl p-14 text-center max-w-sm border ${
          isDark ? "bg-zinc-900 border-zinc-800" : "bg-white border-gray-200 shadow-sm"
        }`}>
          <div className={`inline-flex items-center justify-center w-13 h-13 rounded-2xl mb-5 ${
            isDark ? "bg-zinc-800 border border-zinc-700/50" : "bg-gray-100"
          }`}>
            <MessageCircle className={`w-7 h-7 ${isDark ? "text-zinc-400" : "text-gray-500"}`} />
          </div>
          <p className={`text-base font-semibold mb-1.5 ${isDark ? "text-white" : "text-gray-900"}`}>
            Connect Your Wallet
          </p>
          <p className={`text-sm ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
            Connect a wallet to start chatting about your portfolio
          </p>
        </div>
      </div>
    );
  }

  const sectionPanel = `rounded-xl border ${
    isDark ? "bg-zinc-900 border-zinc-800/80" : "bg-white border-gray-200 shadow-sm"
  }`;

  return (
    <div className="flex gap-4 h-[calc(100vh-130px)]">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className={`flex-1 overflow-hidden flex flex-col ${sectionPanel}`}>

          {/* Chat Header */}
          <div className={`border-b px-4 py-3 flex items-center justify-between shrink-0 ${
            isDark ? "border-zinc-800/80" : "border-gray-200"
          }`}>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                <Sparkles className="w-4.5 h-4.5 text-white" />
              </div>
              <div>
                <p className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
                  Portfolio Assistant
                </p>
                <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                  Ask me about your multi-chain portfolio
                </p>
              </div>
            </div>

            <select
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              disabled={isLoading}
              className={`px-3 py-1.5 rounded-lg border text-xs focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 ${
                isDark
                  ? "bg-zinc-800 border-zinc-700 text-zinc-200"
                  : "bg-gray-50 border-gray-200 text-gray-800"
              }`}
            >
              {getScopeOptions().map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-14 h-14 rounded-2xl bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-4">
                  <Sparkles className="w-7 h-7 text-white" />
                </div>
                <p className={`text-base font-semibold mb-1.5 ${isDark ? "text-white" : "text-gray-900"}`}>
                  Welcome to ChainLens AI
                </p>
                <p className={`text-sm max-w-xs ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
                  Ask me anything about your portfolio across {wallets.length} wallet{wallets.length !== 1 ? "s" : ""}
                </p>
              </div>
            ) : (
              <>
                {messages.map((msg, idx) => (
                  <div key={idx} className="space-y-2">
                    <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-blue-600 text-white"
                          : isDark
                            ? "bg-zinc-800 border border-zinc-700/60 text-zinc-200"
                            : "bg-gray-100 text-gray-900"
                      }`}>
                        <p className="whitespace-pre-wrap">{msg.text}</p>
                      </div>
                    </div>

                    {/* Wallet Results */}
                    {msg.role === "assistant" && idx === messages.length - 1 && walletResults.length > 0 && (
                      <div className={`max-w-[78%] px-4 py-3 rounded-xl border text-xs space-y-2 ${
                        isDark ? "bg-zinc-800/60 border-zinc-700/60 text-zinc-300" : "bg-gray-50 border-gray-200 text-gray-700"
                      }`}>
                        <div className="flex items-center gap-1.5 font-medium">
                          <Settings className="w-3.5 h-3.5" />
                          Wallet Analysis
                        </div>
                        {walletResults.map((r, i) => {
                          const c = getChainColors(r.chain);
                          return (
                            <div key={i} className="flex items-start gap-2">
                              {r.success
                                ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                                : <XCircle className="w-3.5 h-3.5 text-red-500 mt-0.5 shrink-0" />}
                              <div className="min-w-0">
                                <div className="flex items-center gap-1 flex-wrap">
                                  <span className="font-medium">{r.label}</span>
                                  {r.chain && (
                                    <span className={`text-[10px] px-1.5 py-0.5 rounded-md border ${c.bg} ${c.text} ${c.border}`}>
                                      {r.chain.toUpperCase()}
                                    </span>
                                  )}
                                </div>
                                <p className={isDark ? "text-zinc-500" : "text-gray-400"}>
                                  {r.address?.slice(0, 10)}…
                                </p>
                                {r.success && r.data && (
                                  <p className="text-emerald-500 font-medium">
                                    ${r.data.total_usd_value?.toFixed(2) ?? "0.00"}
                                  </p>
                                )}
                                {!r.success && r.error && (
                                  <p className="text-red-400">{r.error}</p>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))}

                {/* Typing indicator */}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className={`rounded-2xl px-4 py-3 flex items-center gap-1.5 ${
                      isDark ? "bg-zinc-800 border border-zinc-700/60" : "bg-gray-100"
                    }`}>
                      {[0, 150, 300].map((delay) => (
                        <span
                          key={delay}
                          className={`w-1.5 h-1.5 rounded-full animate-bounce ${isDark ? "bg-zinc-400" : "bg-gray-400"}`}
                          style={{ animationDelay: `${delay}ms` }}
                        />
                      ))}
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className={`border-t px-4 py-3 shrink-0 ${isDark ? "border-zinc-800/80" : "border-gray-200"}`}>
            <div className="flex gap-2 items-center">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about your portfolio…"
                disabled={isLoading}
                className={`flex-1 px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 ${
                  isDark
                    ? "bg-zinc-800 border-zinc-700 text-white placeholder-zinc-500"
                    : "bg-white border-gray-200 text-gray-900 placeholder-gray-400"
                }`}
              />
              <button
                onClick={handleSend}
                disabled={!inputMessage.trim() || isLoading}
                className="p-2.5 rounded-xl bg-blue-600 text-white hover:bg-blue-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center shrink-0"
              >
                {isLoading ? <Loader2 className="w-4.5 h-4.5 animate-spin" /> : <Send className="w-4.5 h-4.5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className="w-72 shrink-0 flex flex-col gap-4 overflow-y-auto">

        {/* Quick Actions */}
        <div className={`${sectionPanel} p-4`}>
          <p className={`text-xs font-semibold uppercase tracking-wider mb-3 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
            Quick Actions
          </p>
          <div className="space-y-1.5">
            {quickActions.map((action, idx) => {
              const Icon = action.icon;
              return (
                <button
                  key={idx}
                  onClick={() => setInputMessage(action.text)}
                  disabled={isLoading}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-xs transition-colors disabled:opacity-50 flex items-center gap-2.5 ${
                    isDark
                      ? "bg-zinc-800/60 hover:bg-zinc-800 text-zinc-300"
                      : "bg-gray-50 hover:bg-gray-100 text-gray-700"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${isDark ? "text-zinc-500" : "text-gray-400"}`} />
                  {action.text}
                </button>
              );
            })}
          </div>
        </div>

        {/* Portfolio Stats */}
        {portfolioSummary && (
          <div className={`${sectionPanel} p-4`}>
            <p className={`text-xs font-semibold uppercase tracking-wider mb-3 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
              Portfolio Stats
            </p>
            <div className="space-y-3">
              <div>
                <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>Total Value</p>
                <p className="text-xl font-bold font-numeric text-emerald-500">
                  ${portfolioSummary.total_usd_value?.toFixed(2) ?? "0.00"}
                </p>
              </div>

              <div className={`flex gap-4 pt-2 border-t ${isDark ? "border-zinc-800" : "border-gray-100"}`}>
                <div>
                  <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>Wallets</p>
                  <p className={`text-sm font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>
                    {portfolioSummary.total_wallets}
                  </p>
                </div>
                <div>
                  <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>OK</p>
                  <p className="text-sm font-semibold text-emerald-500">{portfolioSummary.successful_wallets}</p>
                </div>
                {portfolioSummary.failed_wallets > 0 && (
                  <div>
                    <p className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>Failed</p>
                    <p className="text-sm font-semibold text-red-400">{portfolioSummary.failed_wallets}</p>
                  </div>
                )}
              </div>

              {portfolioSummary.by_chain && (
                <div className={`pt-2 border-t ${isDark ? "border-zinc-800" : "border-gray-100"}`}>
                  <p className={`text-xs mb-2 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>By Chain</p>
                  <div className="space-y-1.5">
                    {Object.entries(portfolioSummary.by_chain).map(([chain, count]: any) => {
                      const c = getChainColors(chain);
                      return (
                        <div key={chain} className="flex justify-between items-center">
                          <span className={`text-xs font-medium flex items-center gap-1.5 ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${c.bg.replace('/10', '')}`} style={{ background: c.hex }} />
                            {chain.charAt(0).toUpperCase() + chain.slice(1)}
                          </span>
                          <span className={`text-xs ${isDark ? "text-zinc-500" : "text-gray-400"}`}>
                            {count} wallet{count !== 1 ? "s" : ""}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {portfolioSummary.by_token?.length > 0 && (
                <div className={`pt-2 border-t ${isDark ? "border-zinc-800" : "border-gray-100"}`}>
                  <p className={`text-xs mb-2 ${isDark ? "text-zinc-500" : "text-gray-400"}`}>Top Holdings</p>
                  <div className="space-y-1.5">
                    {portfolioSummary.by_token.slice(0, 3).map((token: any, i: number) => (
                      <div key={i} className="flex justify-between items-center">
                        <span className={`text-xs font-medium ${isDark ? "text-zinc-300" : "text-gray-700"}`}>
                          {token.symbol}
                        </span>
                        <span className={`text-xs font-numeric ${isDark ? "text-zinc-400" : "text-gray-500"}`}>
                          ${token.total_usd_value?.toFixed(2) ?? "0.00"}
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
