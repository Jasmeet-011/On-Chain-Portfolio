import React, { useEffect, useState } from "react";
import { Eye, EyeOff, Mail, Lock, User, Loader2, CheckCircle, RefreshCw, ArrowLeft } from "lucide-react";
import Logo from "../components/Logo";
import { api } from "../api";

type SignUpPageProps = {
  onSwitchToSignIn: () => void;
  onSignedUp: () => void;
  onBack?: () => void;
};

const PARTICLES = Array.from({ length: 8 }, (_, i) => i);

const SignUpPage: React.FC<SignUpPageProps> = ({ onSwitchToSignIn, onSignedUp, onBack }) => {
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingVerification, setPendingVerification] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);
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
    if (!formData.name || !formData.email || !formData.password) {
      setError("Please fill in all fields.");
      return;
    }
    setIsLoading(true);
    try {
      const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
      const response = await fetch(`${apiBase}/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        setError((data && (data.detail || data.message)) || "Failed to sign up.");
        return;
      }
      localStorage.setItem("user", JSON.stringify(data));
      setPendingVerification(true);
    } catch (err: any) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setResendLoading(true);
    setResendMessage(null);
    try {
      await api.resendVerification();
      setResendMessage("Verification email sent! Check your inbox.");
    } catch (err: any) {
      setResendMessage(err.message || "Failed to resend. Try again.");
    } finally {
      setResendLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSubmit();
  };

  const inputClass = "w-full bg-zinc-800/80 border border-zinc-700 rounded-xl text-white placeholder-zinc-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500 transition-colors";

  const bgLayer = (
    <>
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
      <div className="absolute inset-0 pointer-events-none"
        style={{ background: "radial-gradient(ellipse 60% 50% at 50% 40%, rgba(96,165,250,0.07) 0%, transparent 70%)" }}
      />
      {PARTICLES.map((i) => (
        <div key={i} className="absolute rounded-full pointer-events-none" style={{
          width: `${3 + (i % 3)}px`, height: `${3 + (i % 3)}px`,
          background: ["#60a5fa", "#818cf8", "#2DD4BF", "#a78bfa"][i % 4],
          left: `${8 + (i * 11.5) % 84}%`, top: `${10 + (i * 12.3) % 80}%`,
          animation: `float-auth ${5 + (i % 4)}s ease-in-out ${(i * 0.6) % 3}s infinite`,
        }} />
      ))}
    </>
  );

  // ── Verification pending ─────────────────────────────────────────────────────
  if (pendingVerification) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 relative overflow-hidden">
        {bgLayer}
        <div className="relative z-10 w-full max-w-sm">
          <div className="bg-zinc-900/80 backdrop-blur-md border border-zinc-800 rounded-2xl p-8 shadow-2xl text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 mb-5 mx-auto">
              <Mail className="w-7 h-7 text-blue-400" />
            </div>
            <h2 className="text-xl font-bold text-white mb-1.5">Check your email</h2>
            <p className="text-zinc-400 text-sm mb-1">We sent a verification link to</p>
            <p className="text-white font-semibold text-sm mb-5">{formData.email}</p>

            <div className="bg-zinc-800/60 border border-zinc-700/60 rounded-xl p-4 text-left mb-5 space-y-2">
              <p className="text-zinc-300 text-xs flex items-start gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                Click the link in the email to verify your account
              </p>
              <p className="text-zinc-300 text-xs flex items-start gap-2">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400 mt-0.5 shrink-0" />
                After verifying, price alerts will be delivered to your inbox
              </p>
              <p className="text-zinc-600 text-xs pl-5.5">
                Check your spam folder if you don't see it within a few minutes.
              </p>
            </div>

            {resendMessage && (
              <p className={`text-xs mb-4 ${resendMessage.includes("sent") ? "text-emerald-400" : "text-red-400"}`}>
                {resendMessage}
              </p>
            )}

            <button onClick={handleResend} disabled={resendLoading}
              className="w-full py-2.5 border border-zinc-700 text-zinc-300 rounded-xl text-sm font-medium hover:bg-zinc-800 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 mb-3">
              {resendLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Resend verification email
            </button>

            <button onClick={onSignedUp}
              className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-500 transition-colors text-sm">
              Continue to App
            </button>

            <p className="text-zinc-600 text-xs mt-4">
              You can also verify later — alerts won't send until verified.
            </p>
          </div>
          <div className="mt-6 flex justify-center">
            <Logo size="md" theme="dark" />
          </div>
        </div>
      </div>
    );
  }

  // ── Sign-up form ─────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 relative overflow-hidden">
      {bgLayer}

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
              Join <span className="auth-gradient-text">ChainLens</span>
            </h1>
            <p className="text-zinc-500 text-sm">Create your free account</p>
          </div>

          {error && (
            <div className="mb-5 rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-xs font-medium text-zinc-400 mb-1.5">Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input type="text" id="name" name="name"
                  value={formData.name} onChange={handleChange} onKeyDown={handleKeyDown}
                  className={`${inputClass} pl-10 pr-4 py-2.5`}
                  placeholder="Your name" />
              </div>
            </div>

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
                  placeholder="Create a password" />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button onClick={handleSubmit} disabled={isLoading}
              className="w-full py-2.5 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-1 text-sm flex items-center justify-center gap-2">
              {isLoading ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating account…</> : "Create Account"}
            </button>
          </div>

          <p className="text-zinc-500 text-sm text-center mt-6">
            Already have an account?{" "}
            <button type="button" onClick={onSwitchToSignIn}
              className="text-blue-400 hover:text-blue-300 font-medium transition-colors">
              Sign In
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

export default SignUpPage;
