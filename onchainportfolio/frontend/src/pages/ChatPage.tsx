import React, { useState, useEffect } from "react";
import { useAppContext } from "../context/AppContext";
import { api } from "../api";
import BalancesTable from "../components/BalancesTable";
import NFTGallery from "../components/NFTGallery";
import PositionsTable from "../components/PositionsTable";
import QuickActions from "../components/QuickActions";

const ChatPage: React.FC = () => {
  const {
    wallet,
    messages,
    addMessage,
    manualAddress,
    setManualAddress,
    isLoading,
    setIsLoading,
    theme,
  } = useAppContext();

  const [input, setInput] = useState("");
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const walletAddr =
      wallet.connected && wallet.address
        ? wallet.address
        : manualAddress;

    addMessage({ role: "user", text: input });
    setInput("");
    setIsLoading(true);

    try {
      const response = await api.chat(input, walletAddr);
      addMessage({
        role: "assistant",
        text: response.text,
        data: response.data,
      });
    } catch (error) {
      addMessage({
        role: "assistant",
        text: "Sorry, I encountered an error. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (text: string) => {
    setInput(text);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div
        className={`lg:col-span-2 flex flex-col rounded-2xl border backdrop-blur-sm ${
          theme === "dark"
            ? "bg-gray-800/50 border-gray-700"
            : "bg-white/50 border-gray-200"
        }`}
      >
        <div
          className="flex-1 overflow-y-auto p-6 space-y-4"
          style={{ minHeight: "500px", maxHeight: "600px" }}
        >
          {messages.length === 0 && (
            <div className="text-center mt-12">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4">
                <span className="text-3xl">💬</span>
              </div>
              <h3
                className={`text-xl font-bold mb-2 ${
                  theme === "dark"
                    ? "text-gray-200"
                    : "text-gray-900"
                }`}
              >
                Welcome to AptosAI
              </h3>
              <p
                className={`text-sm ${
                  theme === "dark"
                    ? "text-gray-400"
                    : "text-gray-600"
                }`}
              >
                Ask me anything about your Aptos portfolio
              </p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${
                msg.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >
              <div
                className={`max-w-3xl rounded-2xl px-5 py-3 ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-blue-500 to-purple-600 text-white"
                    : theme === "dark"
                    ? "bg-gray-700/70 text-gray-100 border border-gray-600"
                    : "bg-gray-100 text-gray-900 border border-gray-200"
                }`}
              >
                <p className="whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </p>
                {msg.data && (
                  <div className="mt-3">
                    {msg.data.balances && (
                      <BalancesTable
                        balances={msg.data.balances}
                        prices={msg.data.prices}
                      />
                    )}
                    {msg.data.nfts && (
                      <NFTGallery nfts={msg.data.nfts} />
                    )}
                    {msg.data.positions && (
                      <PositionsTable
                        positions={msg.data.positions}
                      />
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div
                className={`rounded-2xl px-5 py-3 ${
                  theme === "dark"
                    ? "bg-gray-700/70 border border-gray-600"
                    : "bg-gray-100 border border-gray-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div
                      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "0ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"
                      style={{ animationDelay: "150ms" }}
                    ></div>
                    <div
                      className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"
                      style={{ animationDelay: "300ms" }}
                    ></div>
                  </div>
                  <p
                    className={
                      theme === "dark"
                        ? "text-gray-300"
                        : "text-gray-600"
                    }
                  >
                    Analyzing...
                  </p>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div
          className={`border-t p-4 ${
            theme === "dark" ? "border-gray-700" : "border-gray-200"
          }`}
        >
          {!wallet.connected && (
            <input
              type="text"
              placeholder="Enter Aptos wallet address (0x...)"
              value={manualAddress}
              onChange={(e) => setManualAddress(e.target.value)}
              className={`w-full px-4 py-3 border rounded-xl mb-3 font-mono text-sm transition-all ${
                theme === "dark"
                  ? "bg-gray-700 border-gray-600 text-white placeholder-gray-500 focus:border-blue-500"
                  : "bg-white border-gray-300 text-gray-900 focus:border-blue-400"
              } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
            />
          )}
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              className={`flex-1 px-4 py-3 border rounded-xl transition-all ${
                theme === "dark"
                  ? "bg-gray-700 border-gray-600 text-white placeholder-gray-500 focus:border-blue-500"
                  : "bg-white border-gray-300 text-gray-900 focus:border-blue-400"
              } focus:outline-none focus:ring-2 focus:ring-blue-500/20`}
            />
            <button
              onClick={handleSend}
              disabled={isLoading}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:shadow-lg hover:shadow-blue-500/50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      <div className="lg:col-span-1">
        <QuickActions onAction={handleQuickAction} />
      </div>
    </div>
  );
};

export default ChatPage;
