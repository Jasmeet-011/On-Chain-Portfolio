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

// ─── Animation hook ────────────────────────────────────────────────────────────
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
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
    icon: <Globe className="w-6 h-6" />,
    color: "#627EEA",
    title: "Multi-Chain in One View",
    desc: "Track balances, tokens, and NFTs across every supported chain simultaneously from a single unified dashboard.",
  },
  {
    icon: <Bell className="w-6 h-6" />,
    color: "#F59E0B",
    title: "Real-Time Price Alerts",
    desc: "Set price targets for any token and receive instant email notifications the moment your conditions are met.",
  },
  {
    icon: <BarChart3 className="w-6 h-6" />,
    color: "#10B981",
    title: "Deep Portfolio Analytics",
    desc: "Visualise chain exposure, token allocation, and historical performance with interactive charts.",
  },
  {
    icon: <Zap className="w-6 h-6" />,
    color: "#9945FF",
    title: "AI-Powered Insights",
    desc: "Ask ChainLens anything about your portfolio. Our AI assistant analyses your on-chain data and answers in plain English.",
  },
  {
    icon: <Wallet className="w-6 h-6" />,
    color: "#F6851B",
    title: "Multi-Wallet Support",
    desc: "Connect multiple wallets from different providers and see your entire portfolio aggregated in real time.",
  },
  {
    icon: <Shield className="w-6 h-6" />,
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
        transition: `opacity 0.5s ease ${delay}ms, transform 0.5s ease ${delay}ms, background 0.5s ease ${delay}ms, border-color 0.5s ease ${delay}ms`,
      }}
      className="border rounded-xl p-5 flex flex-col items-center gap-3 hover:scale-105 transition-transform duration-200 cursor-default"
    >
      <div
        className="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold"
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
        borderColor: visible ? wallet.color + "44" : "transparent",
        background: visible ? wallet.bg : "transparent",
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(24px)",
        transition: `opacity 0.55s ease ${delay}ms, transform 0.55s ease ${delay}ms, background 0.55s ease ${delay}ms, border-color 0.55s ease ${delay}ms`,
      }}
      className="border rounded-xl p-5 flex flex-col gap-3 hover:scale-105 transition-transform duration-200 cursor-default"
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl">{wallet.icon}</span>
        <p className="text-white font-semibold">{wallet.name}</p>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {wallet.chains.map((c) => (
          <span
            key={c}
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ background: wallet.color + "22", color: wallet.color }}
          >
            {c}
          </span>
        ))}
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
        transition: `opacity 0.55s ease ${delay}ms, transform 0.55s ease ${delay}ms`,
      }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex flex-col gap-4 hover:border-zinc-700 transition-colors duration-200"
    >
      <div
        className="w-11 h-11 rounded-lg flex items-center justify-center"
        style={{ background: feature.color + "20", color: feature.color }}
      >
        {feature.icon}
      </div>
      <div>
        <p className="text-white font-semibold mb-1.5">{feature.title}</p>
        <p className="text-zinc-400 text-sm leading-relaxed">{feature.desc}</p>
      </div>
    </div>
  );
};

// ─── Section wrapper with reveal ──────────────────────────────────────────────
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
        transition: "opacity 0.6s ease, transform 0.6s ease",
      }}
      className="text-center mb-12"
    >
      <span className="inline-block text-xs font-semibold uppercase tracking-widest text-zinc-500 mb-3 border border-zinc-800 px-3 py-1 rounded-full">
        {label}
      </span>
      <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">{title}</h2>
      <p className="text-zinc-400 max-w-xl mx-auto text-sm sm:text-base">{sub}</p>
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
        transition: "opacity 0.7s ease, transform 0.7s ease",
      }}
      className="bg-zinc-900 border border-zinc-800 rounded-2xl p-10 sm:p-14 glow-blue"
    >
      <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">
        Ready to take control?
      </h2>
      <p className="text-zinc-400 mb-8 text-base sm:text-lg">
        Join ChainLens today. Free to use, no private key required.
      </p>
      <button
        onClick={onSignUp}
        className="group inline-flex items-center gap-2 bg-white text-black font-semibold px-8 py-4 rounded-xl hover:bg-zinc-200 transition-colors text-base shadow-lg"
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
  // Hero headline animation state
  const [heroVisible, setHeroVisible] = useState(false);
  // Floating particles
  const particles = Array.from({ length: 18 }, (_, i) => i);

  useEffect(() => {
    const t = setTimeout(() => setHeroVisible(true), 80);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 text-white overflow-x-hidden">
      {/* ── Keyframe styles ── */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.3; }
          50% { transform: translateY(-18px) rotate(180deg); opacity: 0.7; }
        }
        @keyframes pulse-ring {
          0% { transform: scale(0.9); opacity: 0.6; }
          70% { transform: scale(1.15); opacity: 0; }
          100% { transform: scale(0.9); opacity: 0; }
        }
        @keyframes gradient-x {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
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
          background: linear-gradient(135deg, #627EEA, #9945FF, #2DD4BF);
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
        }
        .glow-blue {
          box-shadow: 0 0 40px rgba(98,126,234,0.15), 0 0 80px rgba(98,126,234,0.08);
        }
      `}</style>

      {/* ── Navbar ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-zinc-800/60 backdrop-blur-md bg-zinc-950/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Logo size="md" theme="dark" />
          <div className="flex items-center gap-3">
            <button
              onClick={onSignIn}
              className="text-zinc-400 hover:text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-zinc-800 transition-colors"
            >
              Sign In
            </button>
            <button
              onClick={onSignUp}
              className="text-black bg-white hover:bg-zinc-200 text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative min-h-screen flex items-center justify-center px-4 pt-16 overflow-hidden">
        {/* Background particles */}
        {particles.map((i) => (
          <div
            key={i}
            className="particle"
            style={{
              width: `${3 + (i % 5)}px`,
              height: `${3 + (i % 5)}px`,
              background: ["#627EEA", "#9945FF", "#2DD4BF", "#F6851B", "#AB9FF2"][i % 5],
              left: `${5 + (i * 5.3) % 90}%`,
              top: `${10 + (i * 7.1) % 80}%`,
              animationDuration: `${4 + (i % 6)}s`,
              animationDelay: `${(i * 0.4) % 3}s`,
            }}
          />
        ))}

        {/* Radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(98,126,234,0.1) 0%, transparent 70%)",
          }}
        />

        {/* Hero content */}
        <div className="relative z-10 text-center max-w-4xl mx-auto">
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(32px)",
              transition: "opacity 0.8s ease, transform 0.8s ease",
            }}
          >
            <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-zinc-400 border border-zinc-800 px-3 py-1.5 rounded-full mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Multi-Chain Portfolio Tracker
            </span>
          </div>

          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(36px)",
              transition: "opacity 0.85s ease 0.1s, transform 0.85s ease 0.1s",
            }}
          >
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight mb-6">
              <span className="gradient-text">Your Entire</span>
              <br />
              <span className="accent-gradient-text">Web3 Portfolio</span>
              <br />
              <span className="gradient-text">One Dashboard</span>
            </h1>
          </div>

          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(28px)",
              transition: "opacity 0.8s ease 0.25s, transform 0.8s ease 0.25s",
            }}
          >
            <p className="text-zinc-400 text-lg sm:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
              Track balances, prices, and transactions across Ethereum, Polygon,
              Base, Aptos, and Solana — with real-time alerts and AI-powered insights.
            </p>
          </div>

          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transform: heroVisible ? "translateY(0)" : "translateY(24px)",
              transition: "opacity 0.8s ease 0.4s, transform 0.8s ease 0.4s",
            }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button
              onClick={onSignUp}
              className="group inline-flex items-center justify-center gap-2 bg-white text-black font-semibold px-8 py-4 rounded-xl hover:bg-zinc-200 transition-all duration-200 text-base shadow-lg hover:shadow-xl"
            >
              Get Started Free
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </button>
            <button
              onClick={onSignIn}
              className="inline-flex items-center justify-center gap-2 border border-zinc-700 text-zinc-300 font-semibold px-8 py-4 rounded-xl hover:bg-zinc-800 hover:border-zinc-600 transition-all duration-200 text-base"
            >
              Sign In
            </button>
          </div>

          {/* Chain pills */}
          <div
            style={{
              opacity: heroVisible ? 1 : 0,
              transition: "opacity 0.8s ease 0.65s",
            }}
            className="flex flex-wrap justify-center gap-2 mt-12"
          >
            {CHAINS.map((c) => (
              <span
                key={c.name}
                className="text-xs px-3 py-1 rounded-full border font-medium"
                style={{
                  borderColor: c.color + "55",
                  color: c.color,
                  background: c.bg,
                }}
              >
                {c.name}
              </span>
            ))}
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 flex flex-col items-center gap-1 text-zinc-600 animate-bounce">
          <span className="text-xs">Scroll</span>
          <ChevronDown className="w-4 h-4" />
        </div>
      </section>

      {/* ── Supported Chains ── */}
      <section className="py-24 px-4 border-t border-zinc-900">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            label="Multi-Chain"
            title="5 Networks. One Dashboard."
            sub="Connect wallets across every major blockchain ecosystem and see all your assets in one place."
          />
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {CHAINS.map((chain, i) => (
              <ChainCard key={chain.name} chain={chain} delay={i * 80} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Supported Wallets ── */}
      <section className="py-24 px-4 border-t border-zinc-900">
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

      {/* ── Features ── */}
      <section className="py-24 px-4 border-t border-zinc-900">
        <div className="max-w-5xl mx-auto">
          <SectionHeading
            label="Features"
            title="Everything You Need"
            sub="From real-time balances to AI-powered analysis — ChainLens gives you the full picture of your on-chain portfolio."
          />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((feature, i) => (
              <FeatureCard key={feature.title} feature={feature} delay={i * 80} />
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Banner ── */}
      <section className="py-24 px-4 border-t border-zinc-900">
        <div className="max-w-3xl mx-auto text-center">
          <CTABanner onSignUp={onSignUp} />
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-zinc-900 py-8 px-4">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <Logo size="sm" theme="dark" />
          <p className="text-zinc-600 text-xs text-center">
            © {new Date().getFullYear()} ChainLens. Non-custodial — your keys, your crypto.
          </p>
          <div className="flex gap-4 text-zinc-500 text-xs">
            <button onClick={onSignIn} className="hover:text-zinc-300 transition-colors">
              Sign In
            </button>
            <button onClick={onSignUp} className="hover:text-zinc-300 transition-colors">
              Sign Up
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
