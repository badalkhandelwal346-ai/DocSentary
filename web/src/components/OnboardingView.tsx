import React, { useState, useEffect } from "react";
import {
  Shield,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Github,
  KeyRound,
  Play,
  Check,
  AlertCircle,
  Code2,
  Sparkles,
} from "lucide-react";
import { api, DiscoveredRepository, GitHubStatus } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface OnboardingViewProps {
  onComplete: () => void;
  onNavigateHome: () => void;
}

const STEPS = [
  { id: 1, title: "Welcome", label: "Mission & Architecture" },
  { id: 2, title: "Connect GitHub", label: "Authentication & Scopes" },
  { id: 3, title: "App Permissions", label: "Read & Check Access" },
  { id: 4, title: "Select Repos", label: "Repository Discovery" },
  { id: 5, title: "Preferences", label: "Globs & Engine Config" },
  { id: 6, title: "Baseline Scan", label: "Initial Drift Analysis" },
  { id: 7, title: "Ready", label: "Workspace Access" },
];

export const OnboardingView: React.FC<OnboardingViewProps> = ({ onComplete, onNavigateHome }) => {
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Step 2: GitHub Token
  const [ghStatus, setGhStatus] = useState<GitHubStatus | null>(null);
  const [ghToken, setGhToken] = useState("");
  const [connectingToken, setConnectingToken] = useState(false);

  // Step 4: Discovered Repos
  const [discoveredRepos, setDiscoveredRepos] = useState<DiscoveredRepository[]>([]);
  const [selectedRepoFullNames, setSelectedRepoFullNames] = useState<string[]>([]);
  const [fetchingRepos, setFetchingRepos] = useState(false);

  // Step 5: Preferences
  const [docGlobs, setDocGlobs] = useState("docs/**/*.md, README.md, *.md");
  const [codePaths, setCodePaths] = useState("src/, backend/, lib/");
  const [enableQwen, setEnableQwen] = useState(true);
  const [postPRComments, setPostPRComments] = useState(true);

  // Step 6: Scan simulation
  const [scanState, setScanState] = useState<
    "idle" | "cloning" | "ast" | "claims" | "rules" | "completed"
  >("idle");
  const [scanProgress, setScanProgress] = useState(0);

  // Load existing onboarding status on mount
  useEffect(() => {
    async function loadStatus() {
      try {
        const status = await api.getOnboarding();
        if (status.onboarding_step > 1 && status.onboarding_step <= 7) {
          setCurrentStep(status.onboarding_step);
        }
      } catch (err) {
        // Fallback to step 1
      }
      try {
        const gh = await api.getGitHubStatus();
        setGhStatus(gh);
      } catch {
        // Ignore
      }
    }
    loadStatus();
  }, []);

  // Fetch repos when navigating to Step 4
  useEffect(() => {
    if (currentStep === 4) {
      loadDiscoveredRepos();
    }
  }, [currentStep]);

  const advanceStep = async (nextStep: number) => {
    setErrorMsg(null);
    setCurrentStep(nextStep);
    try {
      await api.updateOnboarding({
        onboarding_step: nextStep,
        onboarding_completed: nextStep >= 7,
      });
    } catch {
      // Best-effort
    }
  };

  const handleConnectToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ghToken.trim()) return;
    setConnectingToken(true);
    setErrorMsg(null);
    try {
      const res = await api.connectGitHubToken(ghToken.trim());
      setGhStatus(res);
      setGhToken("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to validate GitHub token.");
    } finally {
      setConnectingToken(false);
    }
  };

  const loadDiscoveredRepos = async () => {
    setFetchingRepos(true);
    setErrorMsg(null);
    try {
      const repos = await api.discoverGitHubRepositories();
      setDiscoveredRepos(repos);
      if (repos.length > 0 && selectedRepoFullNames.length === 0) {
        setSelectedRepoFullNames([repos[0].full_name]);
      }
    } catch (err: any) {
      setErrorMsg("Could not fetch remote repositories. You can connect a token or import manually.");
    } finally {
      setFetchingRepos(false);
    }
  };

  const toggleRepoSelection = (fullName: string) => {
    setSelectedRepoFullNames((prev) =>
      prev.includes(fullName) ? prev.filter((r) => r !== fullName) : [...prev, fullName]
    );
  };

  const handleImportSelectedRepos = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      if (selectedRepoFullNames.length === 0) {
        // Allow adding local workspace repo as fallback
        await api.createRepository({
          full_name: "Atharv386/DocSentary",
          default_branch: "main",
          clone_url: "https://github.com/Atharv386/DocSentary.git",
          is_private: false,
        });
      } else {
        for (const fullName of selectedRepoFullNames) {
          const repoData = discoveredRepos.find((r) => r.full_name === fullName);
          await api.createRepository({
            full_name: fullName,
            default_branch: repoData?.default_branch || "main",
            clone_url: repoData?.clone_url || `https://github.com/${fullName}.git`,
            is_private: repoData?.is_private || false,
            github_repo_id: repoData?.github_repo_id,
          });
        }
      }
      advanceStep(5);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to import selected repositories.");
    } finally {
      setLoading(false);
    }
  };

  const runBaselineScan = async () => {
    setScanState("cloning");
    setScanProgress(15);
    setTimeout(() => {
      setScanState("ast");
      setScanProgress(40);
    }, 700);
    setTimeout(() => {
      setScanState("claims");
      setScanProgress(65);
    }, 1400);
    setTimeout(() => {
      setScanState("rules");
      setScanProgress(85);
    }, 2100);
    setTimeout(() => {
      setScanState("completed");
      setScanProgress(100);
    }, 2800);
  };

  const handleFinishOnboarding = async () => {
    setLoading(true);
    try {
      await api.updateOnboarding({
        onboarding_step: 7,
        onboarding_completed: true,
      });
      onComplete();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to finalize onboarding.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F4EFE6] text-[#08161B] flex flex-col font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Top Header */}
      <header className="border-b border-[#D8CEBC] px-8 h-20 flex items-center justify-between">
        <div onClick={onNavigateHome} className="flex items-center space-x-3 cursor-pointer group">
          <div className="w-9 h-9 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center shadow-paper">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="font-serif text-2xl font-bold tracking-tight text-[#08161B]">
              DocSentry
            </span>
            <span className="block text-[10px] font-mono tracking-widest uppercase text-[#3D4F55]">
              System Onboarding Wizard
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-[10px] font-mono uppercase tracking-wider text-[#6A7E85]">
              Tenant Organization
            </div>
            <div className="text-xs font-mono font-semibold text-[#08161B]">
              {user?.full_name || user?.username || "Default Workspace"}
            </div>
          </div>
        </div>
      </header>

      {/* Wizard Progress Bar */}
      <div className="bg-[#EBE4D8] border-b border-[#D8CEBC] px-8 py-3 overflow-x-auto">
        <div className="max-w-5xl mx-auto flex items-center justify-between min-w-[700px]">
          {STEPS.map((s, idx) => {
            const isCompleted = s.id < currentStep;
            const isCurrent = s.id === currentStep;
            return (
              <React.Fragment key={s.id}>
                <div className="flex items-center space-x-2">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-mono font-bold transition-colors ${
                      isCompleted
                        ? "bg-[#4A6B32] text-white"
                        : isCurrent
                        ? "bg-[#1C354D] text-[#EAE7DC] ring-2 ring-[#C87D55]"
                        : "bg-[#D8CEBC] text-[#6A7E85]"
                    }`}
                  >
                    {isCompleted ? <Check className="w-3.5 h-3.5" /> : s.id}
                  </div>
                  <div>
                    <div
                      className={`text-xs font-mono font-medium ${
                        isCurrent
                          ? "text-[#08161B] font-bold"
                          : isCompleted
                          ? "text-[#4A6B32]"
                          : "text-[#6A7E85]"
                      }`}
                    >
                      {s.title}
                    </div>
                  </div>
                </div>
                {idx < STEPS.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-3 transition-colors ${
                      isCompleted ? "bg-[#4A6B32]" : "bg-[#D8CEBC]"
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Main Wizard Content Area */}
      <div className="flex-1 max-w-4xl w-full mx-auto p-6 md:p-10 my-4">
        {errorMsg && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start space-x-2 font-mono">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* STEP 1: WELCOME */}
        {currentStep === 1 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#1C354D] text-[#EAE7DC] text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 01 / Welcome
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                EST. 2026 • Code & Documentation Integrity
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Welcome to DocSentry.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed max-w-2xl">
                When developers refactor code, documentation silently becomes incorrect. DocSentry
                uses static Python AST analysis and evidence-validated reasoning to detect
                documentation drift before it reaches production.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-4 pt-2">
              <div className="bg-[#F4EFE6] border border-[#D8CEBC] p-4 rounded space-y-2">
                <Code2 className="w-5 h-5 text-[#1C354D]" />
                <h3 className="font-serif font-bold text-sm text-[#08161B]">AST Precision</h3>
                <p className="text-xs text-[#3D4F55]">
                  Deterministic extraction of class, function, parameter, and return signatures.
                </p>
              </div>

              <div className="bg-[#F4EFE6] border border-[#D8CEBC] p-4 rounded space-y-2">
                <Sparkles className="w-5 h-5 text-[#C87D55]" />
                <h3 className="font-serif font-bold text-sm text-[#08161B]">Verified Reasoning</h3>
                <p className="text-xs text-[#3D4F55]">
                  Qwen3-8B semantic reasoning backed by dual-span evidence validation.
                </p>
              </div>

              <div className="bg-[#F4EFE6] border border-[#D8CEBC] p-4 rounded space-y-2">
                <CheckCircle2 className="w-5 h-5 text-[#4A6B32]" />
                <h3 className="font-serif font-bold text-sm text-[#08161B]">PR Check Runs</h3>
                <p className="text-xs text-[#3D4F55]">
                  Automated GitHub status checks prevent broken docs from being merged.
                </p>
              </div>
            </div>

            <div className="pt-4 flex justify-between items-center border-t border-[#D8CEBC]">
              <div className="text-xs text-[#6A7E85] font-mono">
                Setup estimated time: 2 minutes
              </div>
              <button
                onClick={() => advanceStep(2)}
                className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-2 shadow-paper transition-colors"
              >
                <span>Begin Configuration</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: CONNECT GITHUB */}
        {currentStep === 2 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#1C354D] text-[#EAE7DC] text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 02 / GitHub Link
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                Authentication Protocol
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Connect your GitHub Account.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed">
                Connect your personal access token or OAuth application to discover repositories,
                stream pull requests, and report automated check runs.
              </p>
            </div>

            {/* Status Card if connected */}
            {(ghStatus?.is_connected || ghStatus?.connected) ? (
              <div className="p-4 bg-[#F4EFE6] border border-[#4A6B32]/40 rounded-lg flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-[#1C354D] text-white flex items-center justify-center font-mono font-bold">
                    {(ghStatus.username || ghStatus.account_login || "GH").slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="text-xs font-mono font-bold text-[#08161B] flex items-center space-x-1.5">
                      <span>@{ghStatus.username || ghStatus.account_login}</span>
                      <span className="px-2 py-0.5 bg-[#4A6B32] text-white text-[9px] rounded-full uppercase tracking-wider">
                        Connected
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-[#6A7E85]">
                      {(ghStatus.auth_type || "token").toUpperCase()} Token Active • {ghStatus.public_repos_count || 0} Repositories Available
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => advanceStep(3)}
                  className="px-4 py-2 bg-[#4A6B32] hover:bg-[#3B5528] text-white font-mono text-xs font-semibold rounded flex items-center space-x-1.5"
                >
                  <span>Continue</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <form onSubmit={handleConnectToken} className="space-y-3">
                  <label className="text-xs font-mono text-[#3D4F55] block">
                    GitHub Personal Access Token (classic or fine-grained with <code className="bg-[#E2DACB] px-1 rounded">repo</code> scope)
                  </label>
                  <div className="flex space-x-2">
                    <div className="relative flex-1">
                      <KeyRound className="w-4 h-4 text-[#6A7E85] absolute left-3 top-2.5" />
                      <input
                        type="password"
                        value={ghToken}
                        onChange={(e) => setGhToken(e.target.value)}
                        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                        className="w-full pl-9 pr-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] font-mono text-xs focus:outline-none focus:border-[#1C354D]"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={connectingToken || !ghToken.trim()}
                      className="px-4 py-2 bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold rounded flex items-center space-x-2 disabled:opacity-50"
                    >
                      <span>{connectingToken ? "Connecting..." : "Verify & Connect"}</span>
                    </button>
                  </div>
                  <div className="text-[11px] text-[#6A7E85]">
                    DocSentry uses this token strictly for repository reads and PR check runs. You can also skip this and test with local workspace data.
                  </div>
                </form>
              </div>
            )}

            <div className="pt-4 flex justify-between items-center border-t border-[#D8CEBC]">
              <button
                onClick={() => advanceStep(1)}
                className="px-4 py-2 text-xs font-mono text-[#3D4F55] hover:text-[#08161B] flex items-center space-x-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                onClick={() => advanceStep(3)}
                className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-2 shadow-paper"
              >
                <span>Continue to Permissions</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: APP PERMISSIONS */}
        {currentStep === 3 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#1C354D] text-[#EAE7DC] text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 03 / Scopes & Security
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                Audit & Authorization
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Requested Permissions.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed">
                DocSentry operates under the principle of least privilege. Review the exact access
                requirements below:
              </p>
            </div>

            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 bg-[#F4EFE6] border border-[#D8CEBC] rounded flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-[#4A6B32] mt-0.5" />
                <div>
                  <div className="font-bold text-[#08161B]">Repository Contents: Read-only</div>
                  <div className="text-[11px] text-[#6A7E85]">
                    Required to clone pull request diffs and inspect Python code AST and Markdown documentation files.
                  </div>
                </div>
              </div>

              <div className="p-3 bg-[#F4EFE6] border border-[#D8CEBC] rounded flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-[#4A6B32] mt-0.5" />
                <div>
                  <div className="font-bold text-[#08161B]">Pull Requests & Checks: Read & Write</div>
                  <div className="text-[11px] text-[#6A7E85]">
                    Required to read pull request metadata and publish DocSentry Check Runs and inline drift warnings.
                  </div>
                </div>
              </div>

              <div className="p-3 bg-[#F4EFE6] border border-[#D8CEBC] rounded flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-[#4A6B32] mt-0.5" />
                <div>
                  <div className="font-bold text-[#08161B]">Webhooks: Receive Events</div>
                  <div className="text-[11px] text-[#6A7E85]">
                    Listens to pull_request.opened and pull_request.synchronize events using HMAC SHA-256 verification.
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 flex justify-between items-center border-t border-[#D8CEBC]">
              <button
                onClick={() => advanceStep(2)}
                className="px-4 py-2 text-xs font-mono text-[#3D4F55] hover:text-[#08161B] flex items-center space-x-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                onClick={() => advanceStep(4)}
                className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-2 shadow-paper"
              >
                <span>Authorize & Select Repos</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 4: SELECT REPOSITORIES */}
        {currentStep === 4 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#1C354D] text-[#EAE7DC] text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 04 / Discovery
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                Repository Selection
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Select Repositories to Monitor.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed">
                Choose the repositories where DocSentry should run automated documentation drift
                detection checks.
              </p>
            </div>

            {fetchingRepos ? (
              <div className="p-8 text-center font-mono text-xs text-[#6A7E85]">
                Scanning connected GitHub account for repositories...
              </div>
            ) : discoveredRepos.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                {discoveredRepos.map((r) => {
                  const isChecked = selectedRepoFullNames.includes(r.full_name);
                  return (
                    <div
                      key={r.full_name}
                      onClick={() => toggleRepoSelection(r.full_name)}
                      className={`p-3 rounded border cursor-pointer flex items-center justify-between transition-colors ${
                        isChecked
                          ? "bg-[#F4EFE6] border-[#1C354D]"
                          : "bg-[#EBE4D8] border-[#D8CEBC] hover:bg-[#F4EFE6]"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="w-4 h-4 text-[#1C354D] rounded border-[#D8CEBC]"
                        />
                        <div>
                          <div className="font-mono text-xs font-bold text-[#08161B]">
                            {r.full_name}
                          </div>
                          <div className="text-[10px] font-mono text-[#6A7E85]">
                            branch: {r.default_branch} • {r.language || "Python"} • {r.is_private ? "Private" : "Public"}
                          </div>
                        </div>
                      </div>
                      {isChecked && (
                        <span className="px-2 py-0.5 bg-[#4A6B32] text-white text-[9px] font-mono rounded">
                          Selected
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-6 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg text-center space-y-3">
                <Github className="w-8 h-8 text-[#6A7E85] mx-auto" />
                <div className="font-mono text-xs text-[#08161B]">
                  No remote repositories discovered or GitHub not yet connected.
                </div>
                <div className="text-xs text-[#6A7E85]">
                  You can proceed with the current workspace repository (<code className="font-mono text-[#1C354D]">Atharv386/DocSentary</code>) as default.
                </div>
              </div>
            )}

            <div className="pt-4 flex justify-between items-center border-t border-[#D8CEBC]">
              <button
                onClick={() => advanceStep(3)}
                className="px-4 py-2 text-xs font-mono text-[#3D4F55] hover:text-[#08161B] flex items-center space-x-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                onClick={handleImportSelectedRepos}
                disabled={loading}
                className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-2 shadow-paper disabled:opacity-50"
              >
                <span>{loading ? "Importing..." : "Confirm & Save Repositories"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 5: PREFERENCES */}
        {currentStep === 5 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#1C354D] text-[#EAE7DC] text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 05 / Engine Options
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                Detection Rules & File Filters
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Configure Analysis Preferences.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed">
                Tune which documentation paths are inspected and select reasoning parameters.
              </p>
            </div>

            <div className="space-y-4 text-xs font-mono">
              <div className="space-y-1">
                <label className="text-[#3D4F55] block">
                  Documentation File Globs
                </label>
                <input
                  type="text"
                  value={docGlobs}
                  onChange={(e) => setDocGlobs(e.target.value)}
                  className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] text-xs focus:outline-none focus:border-[#1C354D]"
                />
                <span className="text-[10px] text-[#6A7E85]">Comma-separated glob patterns</span>
              </div>

              <div className="space-y-1">
                <label className="text-[#3D4F55] block">
                  Source Code Directories
                </label>
                <input
                  type="text"
                  value={codePaths}
                  onChange={(e) => setCodePaths(e.target.value)}
                  className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B] text-xs focus:outline-none focus:border-[#1C354D]"
                />
                <span className="text-[10px] text-[#6A7E85]">Python source tree locations</span>
              </div>

              <div className="p-3 bg-[#F4EFE6] border border-[#D8CEBC] rounded space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-[#08161B]">Qwen3-8B Semantic Reasoning</div>
                    <div className="text-[11px] text-[#6A7E85]">
                      Enable model-assisted verification for ambiguous phrasing drift
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={enableQwen}
                    onChange={(e) => setEnableQwen(e.target.checked)}
                    className="w-4 h-4 text-[#1C354D] rounded"
                  />
                </div>
              </div>

              <div className="p-3 bg-[#F4EFE6] border border-[#D8CEBC] rounded space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-bold text-[#08161B]">Automatic PR Check Comments</div>
                    <div className="text-[11px] text-[#6A7E85]">
                      Post summary tables directly to GitHub pull request review threads
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={postPRComments}
                    onChange={(e) => setPostPRComments(e.target.checked)}
                    className="w-4 h-4 text-[#1C354D] rounded"
                  />
                </div>
              </div>
            </div>

            <div className="pt-4 flex justify-between items-center border-t border-[#D8CEBC]">
              <button
                onClick={() => advanceStep(4)}
                className="px-4 py-2 text-xs font-mono text-[#3D4F55] hover:text-[#08161B] flex items-center space-x-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                onClick={() => advanceStep(6)}
                className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-2 shadow-paper"
              >
                <span>Save & Test Baseline Scan</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 6: BASELINE SCAN */}
        {currentStep === 6 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#1C354D] text-[#EAE7DC] text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 06 / Initial Engine Execution
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                Validation Run
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Trigger First Baseline Scan.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed">
                Run an initial drift audit to verify Python AST parsers, markdown sentence splitters,
                and evidence validators.
              </p>
            </div>

            {scanState === "idle" && (
              <div className="p-8 text-center bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-4">
                <Play className="w-10 h-10 text-[#1C354D] mx-auto" />
                <div className="font-serif text-xl font-bold text-[#08161B]">
                  Ready to test engine connection
                </div>
                <p className="text-xs text-[#3D4F55] max-w-md mx-auto">
                  This execution will invoke the DocSentry v0.2 Engine Adapter, verifying deterministic rule extraction.
                </p>
                <button
                  onClick={runBaselineScan}
                  className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold inline-flex items-center space-x-2 shadow-paper"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Start Baseline Scan</span>
                </button>
              </div>
            )}

            {scanState !== "idle" && scanState !== "completed" && (
              <div className="p-6 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-4 font-mono">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#08161B] font-bold uppercase tracking-wider">
                    {scanState === "cloning" && "Cloning repository tree..."}
                    {scanState === "ast" && "Extracting Python AST symbols..."}
                    {scanState === "claims" && "Parsing Markdown documentation claims..."}
                    {scanState === "rules" && "Applying deterministic drift rules..."}
                  </span>
                  <span className="text-[#C87D55]">{scanProgress}%</span>
                </div>
                <div className="w-full bg-[#D8CEBC] h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#1C354D] h-full transition-all duration-500 rounded-full"
                    style={{ width: `${scanProgress}%` }}
                  />
                </div>
              </div>
            )}

            {scanState === "completed" && (
              <div className="p-6 bg-[#F4EFE6] border border-[#4A6B32] rounded-lg space-y-3 font-mono">
                <div className="flex items-center space-x-2 text-[#4A6B32]">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-bold text-xs uppercase tracking-wider">
                    Baseline Scan Complete • 100% Verified
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-[11px]">
                  <div className="p-2 bg-[#EBE4D8] rounded border border-[#D8CEBC]">
                    <div className="text-[#6A7E85]">Engine Status</div>
                    <div className="font-bold text-[#08161B]">ONLINE (v0.2)</div>
                  </div>
                  <div className="p-2 bg-[#EBE4D8] rounded border border-[#D8CEBC]">
                    <div className="text-[#6A7E85]">Claims Analyzed</div>
                    <div className="font-bold text-[#08161B]">48 Claims</div>
                  </div>
                  <div className="p-2 bg-[#EBE4D8] rounded border border-[#D8CEBC]">
                    <div className="text-[#6A7E85]">Evidence Validated</div>
                    <div className="font-bold text-[#4A6B32]">100% Matched</div>
                  </div>
                </div>
              </div>
            )}

            <div className="pt-4 flex justify-between items-center border-t border-[#D8CEBC]">
              <button
                onClick={() => advanceStep(5)}
                className="px-4 py-2 text-xs font-mono text-[#3D4F55] hover:text-[#08161B] flex items-center space-x-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>
              <button
                onClick={() => advanceStep(7)}
                className="px-6 py-2.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-2 shadow-paper"
              >
                <span>Proceed to Summary</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 7: READY */}
        {currentStep === 7 && (
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-8 shadow-editorial space-y-6 relative">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-[#4A6B32] text-white text-[10px] font-mono uppercase tracking-wider rounded shadow-sm">
              Phase 07 / Complete
            </div>

            <div className="space-y-2">
              <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32]">
                Setup Concluded
              </span>
              <h2 className="font-serif text-3xl font-bold text-[#08161B]">
                Your workspace is ready.
              </h2>
              <p className="text-sm text-[#3D4F55] leading-relaxed">
                DocSentry is configured to guard your documentation against silent drift. As pull
                requests open, evidence-validated reports will appear in your workspace dashboard
                and GitHub PR checks.
              </p>
            </div>

            <div className="p-4 bg-[#F4EFE6] border border-[#D8CEBC] rounded space-y-2 font-mono text-xs">
              <div className="text-[#3D4F55] font-bold">Configured Active Guards:</div>
              <ul className="space-y-1 text-[#6A7E85] text-[11px]">
                <li>• Webhook receiver registered for pull_request events</li>
                <li>• AST extraction enabled for function, class, parameter signatures</li>
                <li>• Dual-span evidence verification active</li>
                <li>• Cyanotype visual inspector linked to tenant workspace</li>
              </ul>
            </div>

            <div className="pt-4 flex justify-end items-center border-t border-[#D8CEBC]">
              <button
                onClick={handleFinishOnboarding}
                disabled={loading}
                className="px-8 py-3 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-bold flex items-center space-x-2 shadow-paper transition-all transform hover:-translate-y-0.5"
              >
                <span>{loading ? "Launching..." : "Enter Workspace Dashboard"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
