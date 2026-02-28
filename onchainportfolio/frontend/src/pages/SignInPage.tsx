// src/pages/SignInPage.tsx
import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useAppContext } from "../context/AppContext";
import { Eye, EyeOff, Mail, Lock, Loader2, ArrowLeft } from "lucide-react";
import Logo from "../components/Logo";

type SignInPageProps = {
  onSwitchToSignUp: () => void;
  onSignedIn: () => void;
  onBack?: () => void;
};

const PARTICLES = Array.from({ length: 14 }, (_, i) => i);

const SignInPage: React.FC<SignInPageProps> = ({ onSwitchToSignUp, onSignedIn, onBack }) => {
  const { setCurrentUser } = useAppContext();
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async () => {
    setError(null);
    if (!formData.email || !formData.password) {
      setError("Please enter both email and password.");
      return;
    }
    setIsLoading(true);
    try {
      const response = await api.login(formData.email, formData.password);
      localStorage.setItem("user", JSON.stringify({
        id: response.user.id,
        name: response.user.name,
        email: response.user.email,
        access_token: response.access_token,
        token_type: response.token_type,
      }));
      setCurrentUser({ id: response.user.id, name: response.user.name, email: response.user.email });
      onSignedIn();
    } catch (err: any) {
      setError(err.message || "Failed to sign in. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSubmit();
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 relative overflow-hidden">
      <style>{`
        @keyframes float-auth {
          0%, 100% { transform: translateY(0px); opacity: 0.25; }
          50% { transform: translateY(-14px); opacity: 0.55; }
        }
        @keyframes gradient-x-auth {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .auth-gradient-text {
          background: linear-gradient(135deg, #627EEA, #9945FF, #2DD4BF);
          background-size: 200% 200%;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          animation: gradient-x-auth 3s ease infinite;
        }
      `}</style>

      {/* Radial glow */}
      <div className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 55% 45% at 50% 40%, rgba(98,126,234,0.08) 0%, transparent 70%)" }} />

      {/* Particles */}
      {PARTICLES.map((i) => (
        <div key={i} className="absolute rounded-full pointer-events-none" style={{
          width: `${3 + (i % 4)}px`, height: `${3 + (i % 4)}px`,
          background: ["#627EEA", "#9945FF", "#2DD4BF", "#F6851B"][i % 4],
          left: `${6 + (i * 6.5) % 88}%`, top: `${8 + (i * 7.3) % 84}%`,
          animation: `float-auth ${4 + (i % 5)}s ease-in-out ${(i * 0.45) % 3}s infinite`,
        }} />
      ))}

      {/* Back button */}
      {onBack && (
        <button onClick={onBack}
          className="absolute top-6 left-6 flex items-center gap-1.5 text-zinc-500 hover:text-zinc-300 text-sm transition-colors z-20">
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
      )}

      <div className="relative z-10 w-full max-w-md"
        style={{
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateY(0)" : "translateY(24px)",
          transition: "opacity 0.6s ease, transform 0.6s ease",
        }}>
        <div className="bg-zinc-900/80 backdrop-blur-sm border border-zinc-800 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold text-white mb-1">
              Welcome back to <span className="auth-gradient-text">ChainLens</span>
            </h1>
            <p className="text-zinc-500 text-sm">Sign in to your account</p>
          </div>

          {error && (
            <div className="mb-5 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input type="email" id="email" name="email"
                  value={formData.email} onChange={handleChange} onKeyDown={handleKeyDown}
                  className="w-full pl-10 pr-4 py-3 bg-zinc-800/80 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 text-sm focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-zinc-500 transition-colors"
                  placeholder="you@example.com" />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-2">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input type={showPassword ? "text" : "password"} id="password" name="password"
                  value={formData.password} onChange={handleChange} onKeyDown={handleKeyDown}
                  className="w-full pl-10 pr-12 py-3 bg-zinc-800/80 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 text-sm focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-zinc-500 transition-colors"
                  placeholder="Enter your password" />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button onClick={handleSubmit} disabled={isLoading}
              className="w-full py-3 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-2 text-sm">
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" /> Signing in...
                </span>
              ) : "Sign In"}
            </button>
          </div>

          <p className="text-zinc-500 text-sm text-center mt-6">
            Don't have an account?{" "}
            <button type="button" onClick={onSwitchToSignUp}
              className="text-white hover:text-zinc-300 font-medium transition-colors">
              Sign Up
            </button>
          </p>
        </div>

        <div className="mt-8 flex justify-center">
          <Logo size="md" theme="dark" />
        </div>
      </div>
    </div>
  );
};

export default SignInPage;
