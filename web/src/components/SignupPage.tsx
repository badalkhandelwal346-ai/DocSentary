import React, { useState } from "react";
import { Shield, ArrowRight, Lock, User, Mail, AlertCircle } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface SignupPageProps {
  onNavigateLogin: () => void;
  onNavigateHome: () => void;
  onSignupSuccess: () => void;
}

export const SignupPage: React.FC<SignupPageProps> = ({
  onNavigateLogin,
  onNavigateHome,
  onSignupSuccess,
}) => {
  const { signup, directLogin } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !username || !password) {
      setErrorMsg("Please fill in all required fields.");
      return;
    }
    if (password.length < 8) {
      setErrorMsg("Password must be at least 8 characters.");
      return;
    }
    setLoading(true);
    setErrorMsg(null);
    try {
      await signup({ email, username, password, full_name: fullName });
      onSignupSuccess();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create account");
    } finally {
      setLoading(false);
    }
  };

  const handleDevQuickstart = async (devName: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      await directLogin(devName);
      onSignupSuccess();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4EFE6] text-[#08161B] flex flex-col font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Top Header */}
      <header className="border-b border-[#D8CEBC] px-8 h-20 flex items-center justify-between">
        <div
          onClick={onNavigateHome}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center shadow-paper">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="font-serif text-2xl font-bold tracking-tight text-[#08161B]">
              DocSentry
            </span>
            <span className="block text-[10px] font-mono tracking-widest uppercase text-[#3D4F55]">
              Est. 2026 • Documentation Reliability
            </span>
          </div>
        </div>

        <button
          onClick={onNavigateLogin}
          className="text-xs font-mono text-[#3D4F55] hover:text-[#08161B] underline underline-offset-4 transition-colors"
        >
          Already have an account? Sign In
        </button>
      </header>

      {/* Main Body */}
      <div className="flex-1 flex items-center justify-center p-6 my-8">
        <div className="max-w-md w-full bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 space-y-6 shadow-editorial relative">
          {/* Terracotta Stamp */}
          <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#C87D55] text-white text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
            Developer Registration
          </div>

          <div className="space-y-1">
            <div className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
              New Organization Workspace
            </div>
            <h1 className="font-serif text-3xl font-bold text-[#08161B] leading-tight">
              Create your account.
            </h1>
            <p className="text-xs text-[#3D4F55] leading-relaxed">
              Begin automated, AST-verified documentation drift detection across your pull requests.
            </p>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-start space-x-2 font-mono">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-4 text-xs font-sans">
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#3D4F55] block">
                Work Email <span className="text-[#C87D55]">*</span>
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#6A7E85] absolute left-3 top-2.5" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="developer@company.com"
                  className="w-full pl-9 pr-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] font-mono text-xs focus:outline-none focus:border-[#1C354D]"
                  required
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#3D4F55] block">
                Username <span className="text-[#C87D55]">*</span>
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-[#6A7E85] absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. octocat, ada"
                  className="w-full pl-9 pr-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] font-mono text-xs focus:outline-none focus:border-[#1C354D]"
                  required
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#3D4F55] block">
                Full Name (optional)
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Ada Lovelace"
                className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] text-xs focus:outline-none focus:border-[#1C354D]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono text-[#3D4F55] block">
                Password <span className="text-[#C87D55]">*</span>
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#6A7E85] absolute left-3 top-2.5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="w-full pl-9 pr-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] font-mono text-xs focus:outline-none focus:border-[#1C354D]"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-semibold text-xs font-mono tracking-wide transition-colors flex items-center justify-center space-x-2 shadow-paper mt-2"
            >
              <span>{loading ? "Registering..." : "Create Account & Continue"}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Local Developer Quickstart */}
          <div className="pt-2 border-t border-[#D8CEBC] space-y-2">
            <div className="text-[10px] font-mono text-[#6A7E85] uppercase tracking-wider text-center">
              Or Fast-Track Local Development
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleDevQuickstart("octocat")}
                className="px-3 py-1.5 rounded bg-[#F4EFE6] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[11px] font-mono text-[#08161B] transition-colors"
              >
                Sign in as @octocat
              </button>
              <button
                type="button"
                onClick={() => handleDevQuickstart("admin")}
                className="px-3 py-1.5 rounded bg-[#F4EFE6] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[11px] font-mono text-[#08161B] transition-colors"
              >
                Sign in as @admin
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
