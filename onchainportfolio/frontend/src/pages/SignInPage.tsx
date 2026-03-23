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

const PARTICLES = Array.from({ length: 8 }, (_, i) => i);

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

  const inputClass = "w-full bg-zinc-800/80 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-colors";

  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 relative overflow-hidden">
      <style>{`
        @keyframes float-auth {
          0%, 100% { transform: translateY(0px); opacity: 0.2; }
          50% { transform: translateY(-12px); opacity: 0.5; }
        }
        @keyframes gradient-x-auth {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .auth-gradient-text {
          background: linear-gradient(135deg, #60a5fa, #818cf8, #2DD4BF);
          background-size: 200% 200%;
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          animation: gradient-x-auth 4s ease infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .auth-gradient-text { animation: none; }
        }
      `}</style>

      {/* Subtle radial glow */}
      <div className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(96,165,250,0.07) 0%, transparent 70%)" }}
      />

      {/* Particles */}
      {PARTICLES.map((i) => (
        <div key={i} className="absolute rounded-full pointer-events-none" style={{
          width: `${3 + (i % 3)}px`, height: `${3 + (i % 3)}px`,
          background: ["#60a5fa", "#818cf8", "#2DD4BF", "#a78bfa"][i % 4],
          left: `${8 + (i * 11.5) % 84}%`, top: `${10 + (i * 12.3) % 80}%`,
          animation: `float-auth ${5 + (i % 4)}s ease-in-out ${(i * 0.6) % 3}s infinite`,
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

      <div
        className="relative z-10 w-full max-w-sm"
        style={{
          opacity: mounted ? 1 : 0,
          transform: mounted ? "translateY(0)" : "translateY(20px)",
          transition: "opacity 0.5s ease, transform 0.5s ease",
        }}
      >
        <div className="bg-zinc-900/80 backdrop-blur-md border border-zinc-800 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-7">
            <h1 className="text-2xl font-bold text-white mb-1">
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
              <label htmlFor="email" className="block text-xs font-medium text-zinc-400 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input type="email" id="email" name="email"
                  value={formData.email} onChange={handleChange} onKeyDown={handleKeyDown}
                  className={`${inputClass} pl-10 pr-4 py-2.5`}
                  placeholder="you@example.com" />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-medium text-zinc-400 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input type={showPassword ? "text" : "password"} id="password" name="password"
                  value={formData.password} onChange={handleChange} onKeyDown={handleKeyDown}
                  className={`${inputClass} pl-10 pr-12 py-2.5`}
                  placeholder="Enter your password" />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button onClick={handleSubmit} disabled={isLoading}
              className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-1 text-sm flex items-center justify-center gap-2">
              {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in…</> : "Sign In"}
            </button>
          </div>

          <p className="text-zinc-500 text-sm text-center mt-6">
            Don't have an account?{" "}
            <button type="button" onClick={onSwitchToSignUp}
              className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
              Sign Up
            </button>
          </p>
        </div>

        <div className="mt-6 flex justify-center">
          <Logo size="md" theme="dark" />
        </div>
      </div>
    </div>
  );
};

export default SignInPage;
