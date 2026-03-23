// src/pages/LandingPage.tsx
import React, { useEffect, useRef, useState } from "react";
import Logo from "../components/Logo";
import {
  ArrowRight,
  Bell,
  BarChart3,
  Wallet,
  Globe,
  Shield,
  Zap,
  ChevronDown,
} from "lucide-react";

// ─── prefers-reduced-motion ────────────────────────────────────────────────────
const prefersReducedMotion =
  typeof window !== "undefined"
    ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
    : false;

// ─── Animation hook ────────────────────────────────────────────────────────────
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(prefersReducedMotion);

  useEffect(() => {
    if (prefersReducedMotion) {
      setVisible(true);
      return;
    }
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { threshold: 0.12 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return { ref, visible };
}

// ─── Data ──────────────────────────────────────────────────────────────────────
const CHAINS = [
  { name: "Ethereum", symbol: "ETH", color: "#627EEA", bg: "#627EEA18", desc: "Mainnet & Sepolia" },
  { name: "Polygon",  symbol: "MATIC", color: "#8247E5", bg: "#8247E518", desc: "Mainnet & Amoy" },
  { name: "Base",     symbol: "BASE", color: "#0052FF", bg: "#0052FF18", desc: "Mainnet & Sepolia" },
  { name: "Aptos",    symbol: "APT",  color: "#2DD4BF", bg: "#2DD4BF18", desc: "Mainnet & Testnet" },
  { name: "Solana",   symbol: "SOL",  color: "#9945FF", bg: "#9945FF18", desc: "Mainnet & Devnet" },
];

const WALLETS = [
  {
    name: "MetaMask",
    chains: ["Ethereum", "Polygon", "Base"],
    color: "#F6851B",
    bg: "#F6851B18",
    icon: "🦊",
  },
  {
    name: "Phantom",
    chains: ["Solana", "Ethereum", "Polygon"],
    color: "#AB9FF2",
    bg: "#AB9FF218",
    icon: "👻",
  },
  {
    name: "Petra",
    chains: ["Aptos"],
    color: "#2DD4BF",
    bg: "#2DD4BF18",
    icon: "🔮",
  },
  {
    name: "Coinbase Wallet",
    chains: ["Ethereum", "Base", "Polygon"],
    color: "#0052FF",
    bg: "#0052FF18",
    icon: "💙",
  },
];

const FEATURES = [
  {
    icon: <Globe className="w-5 h-5" />,
    color: "#627EEA",
    title: "Multi-Chain in One View",
    desc: "Track balances, tokens, and NFTs across every supported chain simultaneously from a single unified dashboard.",
  },
  {
    icon: <Bell className="w-5 h-5" />,
    color: "#F59E0B",
    title: "Real-Time Price Alerts",
    desc: "Set price targets for any token and receive instant email notifications the moment your conditions are met.",
  },
  {
    icon: <BarChart3 className="w-5 h-5" />,
    color: "#10B981",
    title: "Deep Portfolio Analytics",
    desc: "Visualise chain exposure, token allocation, and historical performance with interactive charts.",
  },
  {
    icon: <Zap className="w-5 h-5" />,
    color: "#9945FF",
    title: "AI-Powered Insights",
    desc: "Ask ChainLens anything about your portfolio. Our AI assistant analyses your on-chain data and answers in plain English.",
  },
  {
    icon: <Wallet className="w-5 h-5" />,
    color: "#F6851B",
    title: "Multi-Wallet Support",
    desc: "Connect multiple wallets from different providers and see your entire portfolio aggregated in real time.",
  },
  {
    icon: <Shield className="w-5 h-5" />,
    color: "#EF4444",
    title: "Non-Custodial & Secure",
    desc: "We never ask for private keys or seed phrases. Read-only on-chain data keeps your assets fully in your control.",
  },
];

// ─── Sub-components ────────────────────────────────────────────────────────────

const ChainCard: React.FC<{ chain: (typeof CHAINS)[0]; delay: number }> = ({
  chain,
  delay,
}) => {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={{
        borderColor: visible ? chain.color + "44" : "transparent",
        background: visible ? chain.bg : "transparent",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(24px)",
        transition: prefersReducedMotion
          ? "none"
          : `opacity 0.5s ease ${delay}ms, transform 0.5s ease ${delay}ms, background 0.5s ease ${delay}ms, border-color 0.5s ease ${delay}ms`,
      }}
      className="border rounded-2xl p-6 flex flex-col items-center gap-3 hover:border-zinc-700/80 hover:bg-zinc-900/90 transition-all duration-200 cursor-default"
    >
      <div
        className="w-12 h-12 rounded-full flex items-center justify-center text-sm font-bold"
        style={{ background: chain.color + "22", color: chain.color }}
      >
        {chain.symbol.slice(0, 2)}
      </div>
      <p className="text-white font-semibold text-sm">{chain.name}</p>
      <p className="text-zinc-500 text-xs">{chain.desc}</p>
    </div>
  );
};

const WalletCard: React.FC<{ wallet: (typeof WALLETS)[0]; delay: number }> = ({
  wallet,
  delay,
}) => {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(24px)",
        transition: prefersReducedMotion
          ? "none"
          : `opacity 0.55s ease ${delay}ms, transform 0.55s ease ${delay}ms`,
      }}
      className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-5 flex items-center gap-3 hover:border-zinc-700/80 transition-all duration-200 cursor-default"
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
        style={{ background: wallet.color + "22" }}
      >
        {wallet.icon}
      </div>
      <div className="min-w-0">
        <p className="text-sm font-semibold text-white truncate">{wallet.name}</p>
        <p className="text-xs text-zinc-500 truncate">{wallet.chains.join(", ")}</p>
      </div>
    </div>
  );
};

const FeatureCard: React.FC<{
  feature: (typeof FEATURES)[0];
  delay: number;
}> = ({ feature, delay }) => {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(28px)",
        transition: prefersReducedMotion
          ? "none"
          : `opacity 0.55s ease ${delay}ms, transform 0.55s ease ${delay}ms`,
      }}
      className="bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-6 flex flex-col gap-4 hover:border-zinc-700/80 transition-all duration-200"
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center border shrink-0"
        style={{
          background: feature.color + "15",
          color: feature.color,
          borderColor: feature.color + "30",
        }}
      >
        {feature.icon}
      </div>
      <div>
        <p className="text-base font-semibold text-white mb-2">{feature.title}</p>
        <p className="text-sm text-zinc-400 leading-relaxed">{feature.desc}</p>
      </div>
    </div>
  );
};

// ─── Section heading with reveal ───────────────────────────────────────────────
const SectionHeading: React.FC<{ label: string; title: string; sub: string }> = ({
  label,
  title,
  sub,
}) => {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(20px)",
        transition: prefersReducedMotion ? "none" : "opacity 0.6s ease, transform 0.6s ease",
      }}
      className="text-center mb-12"
    >
      <span className="inline-block text-xs font-semibold uppercase tracking-widest text-blue-400 mb-3">
        {label}
      </span>
      <h2 className="text-3xl font-bold text-white mb-4">{title}</h2>
      <p className="text-zinc-400 max-w-xl mx-auto text-sm sm:text-base leading-relaxed">{sub}</p>
    </div>
  );
};

const CTABanner: React.FC<{ onSignUp: () => void }> = ({ onSignUp }) => {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(28px)",
        transition: prefersReducedMotion ? "none" : "opacity 0.7s ease, transform 0.7s ease",
      }}
      className="max-w-3xl mx-auto text-center bg-linear-to-br from-blue-600/10 via-indigo-600/5 to-transparent border border-blue-500/20 rounded-3xl p-12"
    >
      <h2 className="text-3xl font-bold text-white mb-4">
        Ready to take control?
      </h2>
      <p className="text-zinc-400 mb-8 text-base sm:text-lg leading-relaxed">
        Join ChainLens today. Free to use, no private key required.
      </p>
      <button
        onClick={onSignUp}
        className="group inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-8 py-4 rounded-xl border border-blue-600 transition-all duration-200 shadow-lg shadow-blue-500/20 text-base"
      >
        Create Free Account
        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  );
};

// ─── Main component ────────────────────────────────────────────────────────────
type LandingPageProps = {
  onSignIn: () => void;
  onSignUp: () => void;
};

const LandingPage: React.FC<LandingPageProps> = ({ onSignIn, onSignUp }) => {
  const [heroVisible, setHeroVisible] = useState(prefersReducedMotion);
  // Reduced from 18 to 8 particles for performance
  const particles = Array.from({ length: 8 }, (_, i) => i);

  useEffect(() => {
    if (prefersReducedMotion) return;
    const t = setTimeout(() => setHeroVisible(true), 80);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-white overflow-x-hidden">
      {/* ── Keyframe styles ── */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.15; }
          50% { transform: translateY(-20px) rotate(180deg); opacity: 0.4; }
        }
        @keyframes gradient-x {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        @keyframes bounce-soft {
          0%, 100% { transform: translateX(-50%) translateY(0); }
          50% { transform: translateX(-50%) translateY(6px); }
        }
        .gradient-text {
          background: linear-gradient(135deg, #fff 0%, #a1a1aa 40%, #fff 80%);
          background-size: 200% 200%;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          animation: gradient-x 4s ease infinite;
        }
        .accent-gradient-text {
          background: linear-gradient(135deg, #3b82f6, #8b5cf6, #2DD4BF);
          background-size: 200% 200%;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          animation: gradient-x 3s ease infinite;
        }
        .particle {
          position: absolute;
          border-radius: 50%;
          animation: float linear infinite;
          pointer-events: none;
        }
        .hero-grid {
          background-image:
            radial-gradient(circle, rgba(255,255,255,0.03) 1px, transparent 1px);
          background-size: 40px 40px;
        }
        @media (prefers-reduced-motion: reduce) {
          .particle { animation: none !important; }
          .gradient-text { animation: none !important; }
          .accent-gradient-text { animation: none !important; }
        }
      `}</style>

      {/* ── Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <Logo size="md" theme="dark" />
          <div className="flex items-center gap-2">
            <button
              onClick={onSignIn}
              className="text-zinc-400 hover:text-white px-4 py-2 text-sm transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={onSignUp}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 text-center pt-14 overflow-hidden">
        {/* Subtle dot grid */}
        <div className="absolute inset-0 hero-grid pointer-events-none" />

        {/* Radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 70% 55% at 50% 40%, rgba(59,130,246,0.12) 0%, rgba(139,92,246,0.04) 50%, transparent 70%)",
          }}
        />

        {/* Reduced particles — 8 instead of 18 */}
        {particles.map((i) => (
          <div
            key={i}
            className="particle"
            style={{
              width: `${3 + (i % 4)}px`,
              height: `${3 + (i % 4)}px`,
              background: ["#3b82f6", "#8b5cf6", "#2DD4BF", "#F6851B"][i % 4],
              left: `${8 + (i * 12.5) % 84}%`,
              top: `${12 + (i * 11.3) % 76}%`,
              animationDuration: `${5 + (i % 5) * 1.5}s`,
              animationDelay: `${(i * 0.7) % 4}s`,
            }}
          />
        ))}

        {/* Hero content */}
        <div className="relative z-10 max-w-4xl mx-auto">
          {/* Badge */}
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(20px)",
              transition: prefersReducedMotion ? "none" : "opacity 0.7s ease, transform 0.7s ease",
            }}
            className="mb-6"
          >
            <span className="inline-flex items-center gap-2 bg-blue-500/10 text-blue-400 border border-blue-500/20 px-3 py-1 rounded-full text-sm font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              Multi-Chain Portfolio Tracker
            </span>
          </div>

          {/* Headline */}
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(36px)",
              transition: prefersReducedMotion
                ? "none"
                : "opacity 0.85s ease 0.1s, transform 0.85s ease 0.1s",
            }}
          >
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white leading-[1.1] tracking-tight mb-6">
              <span className="gradient-text">Your Entire</span>
              <br />
              <span className="accent-gradient-text">Web3 Portfolio</span>
              <br />
              <span className="gradient-text">One Dashboard</span>
            </h1>
          </div>

          {/* Subheadline */}
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(28px)",
              transition: prefersReducedMotion
                ? "none"
                : "opacity 0.8s ease 0.25s, transform 0.8s ease 0.25s",
            }}
          >
            <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              Track balances, prices, and transactions across Ethereum, Polygon,
              Base, Aptos, and Solana — with real-time alerts and AI-powered insights.
            </p>
          </div>

          {/* CTA buttons */}
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(24px)",
              transition: prefersReducedMotion
                ? "none"
                : "opacity 0.8s ease 0.4s, transform 0.8s ease 0.4s",
            }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button
              onClick={onSignUp}
              className="group inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-7 py-3.5 rounded-xl border border-blue-600 transition-all duration-200 shadow-lg shadow-blue-500/15"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={onSignIn}
              className="inline-flex items-center justify-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-white font-semibold px-7 py-3.5 rounded-xl border border-zinc-700/60 hover:border-zinc-600 transition-all duration-200"
            >
              Sign In
            </button>
          </div>

          {/* Chain pills */}
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transition: prefersReducedMotion ? "none" : "opacity 0.8s ease 0.65s",
            }}
            className="flex flex-wrap justify-center gap-2.5 mt-10"
          >
            {CHAINS.map((c) => (
              <span
                key={c.name}
                className="flex items-center gap-2 bg-zinc-900/60 border border-zinc-800/80 rounded-full px-4 py-1.5 text-sm"
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ background: c.color }}
                />
                <span style={{ color: c.color }} className="font-medium">{c.name}</span>
                <span className="text-zinc-600 text-xs">{c.desc}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div
          className="absolute bottom-10 left-1/2 flex flex-col items-center gap-1 text-zinc-600"
          style={{
            animation: prefersReducedMotion ? "none" : "bounce-soft 2s ease-in-out infinite",
            transform: "translateX(-50%)",
          }}
        >
          <span className="text-xs tracking-wide">Scroll</span>
          <ChevronDown className="w-4 h-4" />
        </div>
      </section>

      {/* ── Supported Chains ── */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <SectionHeading
            label="Multi-Chain"
            title="5 Networks. One Dashboard."
            sub="Connect wallets across every major blockchain ecosystem and see all your assets in one place."
          />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {CHAINS.map((chain, i) => (
              <ChainCard key={chain.name} chain={chain} delay={i * 80} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 px-6 bg-linear-to-b from-transparent via-zinc-900/20 to-transparent">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            label="Features"
            title="Everything You Need"
            sub="From real-time balances to AI-powered analysis — ChainLens gives you the full picture of your on-chain portfolio."
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feature, i) => (
              <FeatureCard key={feature.title} feature={feature} delay={i * 80} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Supported Wallets ── */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            label="Wallet Integrations"
            title="Connect Your Favourite Wallets"
            sub="ChainLens works with the wallets you already use. No new accounts, no friction."
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {WALLETS.map((wallet, i) => (
              <WalletCard key={wallet.name} wallet={wallet} delay={i * 100} />
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className="py-20 px-6">
        <CTABanner onSignUp={onSignUp} />
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-zinc-800/60 py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Logo size="sm" theme="dark" />
            <span className="text-zinc-600 text-sm hidden sm:inline">
              &copy; {new Date().getFullYear()} ChainLens
            </span>
          </div>
          <p className="text-zinc-600 text-sm text-center sm:hidden">
            &copy; {new Date().getFullYear()} ChainLens. Non-custodial — your keys, your crypto.
          </p>
          <p className="text-zinc-600 text-sm hidden sm:block">
            Non-custodial — your keys, your crypto.
          </p>
          <div className="flex gap-4">
            <button
              onClick={onSignIn}
              className="text-sm text-zinc-600 hover:text-zinc-300 transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={onSignUp}
              className="text-sm text-zinc-600 hover:text-zinc-300 transition-colors"
            >
              Sign Up
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
