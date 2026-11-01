import React, { useState, useEffect } from "react";
import { Settings, Shield, Github, Sliders, Check, Copy, KeyRound } from "lucide-react";
import { api, GitHubStatus } from "../api/client";

export const SettingsView: React.FC = () => {
  const [modelEnabled, setModelEnabled] = useState(true);
  const [timeoutSecs, setTimeoutSecs] = useState("120");
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [ghStatus, setGhStatus] = useState<GitHubStatus | null>(null);
  const [ghToken, setGhToken] = useState("");
  const [savingToken, setSavingToken] = useState(false);
  const [tokenNotice, setTokenNotice] = useState<string | null>(null);

  const webhookUrl = `${window.location.origin.replace("5173", "8000")}/api/v1/webhooks/github`;

  useEffect(() => {
    async function loadGH() {
      try {
        const status = await api.getGitHubStatus();
        setGhStatus(status);
      } catch {
        // Fallback
      }
    }
    loadGH();
  }, []);

  const handleCopyWebhook = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  const handleConnectToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ghToken.trim()) return;
    setSavingToken(true);
    setTokenNotice(null);
    try {
      const res = await api.connectGitHubToken(ghToken.trim());
      setGhStatus(res);
      setGhToken("");
      setTokenNotice("GitHub access token connected successfully!");
    } catch (err: any) {
      setTokenNotice(err.message || "Failed to validate GitHub token.");
    } finally {
      setSavingToken(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4EFE6] text-[#08161B] p-8 space-y-8 font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC] max-w-4xl">
      <div className="border-b border-[#D8CEBC] pb-6">
        <h1 className="font-serif text-3xl font-bold tracking-tight text-[#08161B] flex items-center space-x-2.5">
          <Settings className="w-6 h-6 text-[#1C354D]" />
          <span>Platform Settings & GitHub Integration</span>
        </h1>
        <p className="text-xs text-[#3D4F55] mt-1 font-sans">
          Configure continuous documentation drift detection, GitHub credentials, inbound webhooks, and engine parameters.
        </p>
      </div>

      {tokenNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 font-mono">
          {tokenNotice}
        </div>
      )}

      {/* GitHub Integration Section */}
      <div className="p-6 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#D8CEBC] pb-3">
          <div className="flex items-center space-x-2.5">
            <Github className="w-5 h-5 text-[#08161B]" />
            <h2 className="font-serif font-bold text-lg text-[#08161B]">GitHub Integration</h2>
          </div>
          <span
            className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
              (ghStatus?.is_connected || ghStatus?.connected)
                ? "bg-[#4A6B32] text-white"
                : "bg-[#D8CEBC] text-[#3D4F55]"
            }`}
          >
            {(ghStatus?.is_connected || ghStatus?.connected) ? "CONNECTED" : "NOT CONNECTED"}
          </span>
        </div>

        {(ghStatus?.is_connected || ghStatus?.connected) ? (
          <div className="p-4 bg-[#F4EFE6] border border-[#4A6B32]/40 rounded font-mono text-xs space-y-1">
            <div className="font-bold text-[#08161B]">
              Authenticated as @{ghStatus.username || ghStatus.account_login}
            </div>
            <div className="text-[11px] text-[#6A7E85]">
              Authentication Mode: {(ghStatus.auth_type || "token").toUpperCase()} • Available Repos: {ghStatus.public_repos_count || 0}
            </div>
          </div>
        ) : (
          <form onSubmit={handleConnectToken} className="space-y-3 font-mono text-xs">
            <label className="text-[#3D4F55] block">
              Connect GitHub Personal Access Token (classic or fine-grained with <code className="bg-[#F4EFE6] px-1 rounded">repo</code> permissions):
            </label>
            <div className="flex space-x-2">
              <div className="relative flex-1">
                <KeyRound className="w-4 h-4 text-[#6A7E85] absolute left-3 top-2.5" />
                <input
                  type="password"
                  value={ghToken}
                  onChange={(e) => setGhToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  className="w-full pl-9 pr-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] text-xs focus:outline-none focus:border-[#1C354D]"
                />
              </div>
              <button
                type="submit"
                disabled={savingToken || !ghToken.trim()}
                className="px-4 py-2 bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] rounded font-semibold disabled:opacity-50"
              >
                {savingToken ? "Connecting..." : "Save Token"}
              </button>
            </div>
          </form>
        )}

        <div className="space-y-3 pt-2">
          <div className="space-y-1.5 font-mono text-xs">
            <label className="text-[#3D4F55]">Inbound Webhook Delivery URL</label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                readOnly
                value={webhookUrl}
                className="flex-1 px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-xs text-[#08161B]"
              />
              <button
                onClick={handleCopyWebhook}
                className="px-3 py-2 bg-[#F4EFE6] hover:bg-[#E2DACB] border border-[#D8CEBC] rounded text-xs text-[#08161B] flex items-center space-x-1.5 transition-colors"
              >
                {copiedUrl ? (
                  <Check className="w-3.5 h-3.5 text-[#4A6B32]" />
                ) : (
                  <Copy className="w-3.5 h-3.5 text-[#1C354D]" />
                )}
                <span>{copiedUrl ? "Copied" : "Copy"}</span>
              </button>
            </div>
          </div>

          <div className="space-y-1.5 font-mono text-xs">
            <label className="text-[#3D4F55]">HMAC Webhook Secret</label>
            <input
              type="text"
              readOnly
              value="••••••••••••••••••••••••••••••••"
              className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-xs text-[#6A7E85]"
            />
            <p className="text-[11px] text-[#6A7E85]">
              Verified automatically via <code className="text-[#1C354D]">DOCSENTRY_GITHUB_WEBHOOK_SECRET</code>.
            </p>
          </div>
        </div>
      </div>

      {/* Analysis Engine & Model Preferences */}
      <div className="p-6 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-4 shadow-sm">
        <div className="flex items-center space-x-2.5 border-b border-[#D8CEBC] pb-3">
          <Sliders className="w-5 h-5 text-[#1C354D]" />
          <h2 className="font-serif font-bold text-lg text-[#08161B]">Detection Engine Configuration</h2>
        </div>

        <div className="space-y-4 text-xs font-mono">
          <div className="flex items-center justify-between p-3 rounded bg-[#F4EFE6] border border-[#D8CEBC]">
            <div>
              <div className="text-[#08161B] font-bold">
                Selective AI Model Verification (Qwen3-8B)
              </div>
              <div className="text-[#6A7E85] text-[11px] mt-0.5">
                Uses local Ollama Qwen3-8B for complex semantic claims while preserving 100% deterministic AST rules.
              </div>
            </div>
            <button
              onClick={() => setModelEnabled(!modelEnabled)}
              className={`w-12 h-6 rounded-full transition-colors relative flex items-center px-1 ${
                modelEnabled ? "bg-[#1C354D]" : "bg-[#D8CEBC]"
              }`}
            >
              <span
                className={`w-4 h-4 rounded-full bg-[#EAE7DC] transition-transform ${
                  modelEnabled ? "translate-x-6" : "translate-x-0"
                }`}
              />
            </button>
          </div>

          <div className="space-y-1.5">
            <label className="text-[#3D4F55] block">Analysis Timeout (seconds)</label>
            <input
              type="number"
              value={timeoutSecs}
              onChange={(e) => setTimeoutSecs(e.target.value)}
              className="w-32 px-3 py-1.5 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B]"
            />
          </div>
        </div>
      </div>

      {/* Security & Code Isolation Banner */}
      <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#4A6B32]/40 flex items-start space-x-3 text-xs">
        <Shield className="w-5 h-5 text-[#4A6B32] flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-bold text-[#4A6B32] font-mono">
            Strict Zero Untrusted Code Execution Guarantee
          </span>
          <p className="text-[#3D4F55] leading-relaxed font-sans">
            DocSentry operates strictly through static AST analysis and Git object parsing. It never imports,
            executes, builds, or runs code from analyzed repositories, eliminating Remote Code Execution (RCE) vectors.
          </p>
        </div>
      </div>
    </div>
  );
};
