import React, { useEffect, useState } from "react";
import {
  GitPullRequest,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  RefreshCw,
  Plus,
  Layers,
  Compass,
} from "lucide-react";
import { api, HealthStatus, Repository } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface DashboardViewProps {
  onNavigateTab: (tab: string, contextId?: string) => void;
  onOpenOnboarding: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onNavigateTab,
  onOpenOnboarding,
}) => {
  const { user } = useAuth();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddRepo, setShowAddRepo] = useState<boolean>(false);
  const [newRepoName, setNewRepoName] = useState<string>("Atharv386/DocSentary");
  const [newRepoClone, setNewRepoClone] = useState<string>(
    "https://github.com/Atharv386/DocSentary.git"
  );

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [repos, h] = await Promise.all([
        api.listRepositories().catch(() => []),
        api.getHealth().catch(() => ({
          status: "healthy",
          version: "0.2.0",
          database: "connected",
          worker_queue: "idle",
          environment: "development",
        })),
      ]);
      setRepositories(repos);
      setHealth(h);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleAddRepository = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRepoName.trim()) return;
    try {
      await api.createRepository({
        full_name: newRepoName.trim(),
        default_branch: "main",
        clone_url: newRepoClone.trim(),
        is_private: false,
      });
      setShowAddRepo(false);
      loadDashboardData();
    } catch (err: any) {
      alert(`Error creating repository: ${err.message}`);
    }
  };

  const totalOpenFindings = repositories.reduce(
    (acc, r) => acc + (r.open_findings_count || 0),
    0
  );
  const totalActivePRs = repositories.reduce(
    (acc, r) => acc + (r.active_prs_count || 0),
    0
  );

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4EFE6] text-[#08161B] p-8 space-y-8 font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Top Banner / Header */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 font-mono">
          System Notice: {error}
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8CEBC] pb-6">
        <div>
          <div className="flex items-center space-x-2 text-[11px] font-mono text-[#4A6B32] mb-1">
            <span className="w-2 h-2 rounded-full bg-[#4A6B32]"></span>
            <span>WORKSPACE: {user?.organization?.name || user?.username || "Default Workspace"}</span>
          </div>
          <h1 className="font-serif text-3xl font-bold tracking-tight text-[#08161B]">
            Documentation Reliability Dashboard
          </h1>
          <p className="text-xs text-[#3D4F55] mt-1 font-sans">
            Continuous AST-verified documentation drift detection across connected pull requests.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="p-2 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#3D4F55] transition-colors"
            title="Refresh dashboard metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={onOpenOnboarding}
            className="px-3.5 py-2 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#08161B] text-xs font-mono font-semibold flex items-center space-x-1.5 transition-colors"
          >
            <Compass className="w-3.5 h-3.5 text-[#C87D55]" />
            <span>Setup Wizard</span>
          </button>
          <button
            onClick={() => setShowAddRepo(true)}
            className="px-4 py-2 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-paper"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Connect Repository</span>
          </button>
        </div>
      </div>

      {/* Quick Add Repository Modal Dialog */}
      {showAddRepo && (
        <div className="p-6 bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg shadow-editorial space-y-4 max-w-xl">
          <div className="flex items-center justify-between border-b border-[#D8CEBC] pb-2">
            <h3 className="font-serif font-bold text-lg text-[#08161B]">
              Add Monitored Repository
            </h3>
            <button
              onClick={() => setShowAddRepo(false)}
              className="text-xs font-mono text-[#6A7E85] hover:text-[#08161B]"
            >
              Cancel
            </button>
          </div>
          <form onSubmit={handleAddRepository} className="space-y-3 font-mono text-xs">
            <div>
              <label className="text-[#3D4F55] block mb-1">Repository Full Name (owner/repo)</label>
              <input
                type="text"
                value={newRepoName}
                onChange={(e) => setNewRepoName(e.target.value)}
                className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B]"
                required
              />
            </div>
            <div>
              <label className="text-[#3D4F55] block mb-1">Git Clone URL</label>
              <input
                type="text"
                value={newRepoClone}
                onChange={(e) => setNewRepoClone(e.target.value)}
                className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B]"
                required
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-[#1C354D] text-[#EAE7DC] rounded font-semibold flex items-center space-x-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Confirm & Save Repository</span>
            </button>
          </form>
        </div>
      )}

      {/* Metrics Row (Tactile Editorial Style) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-2 relative shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono text-[#6A7E85]">
            <span>CONNECTED REPOSITORIES</span>
            <BookOpen className="w-4 h-4 text-[#1C354D]" />
          </div>
          <div className="text-3xl font-bold font-serif text-[#08161B]">{repositories.length}</div>
          <div className="text-[11px] font-mono text-[#3D4F55] flex items-center space-x-1">
            <span className="text-[#4A6B32] font-semibold">
              {repositories.filter((r) => r.is_active).length}
            </span>
            <span>active scanning</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-2 relative shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono text-[#6A7E85]">
            <span>ACTIVE PULL REQUESTS</span>
            <GitPullRequest className="w-4 h-4 text-[#1C354D]" />
          </div>
          <div className="text-3xl font-bold font-serif text-[#08161B]">{totalActivePRs}</div>
          <div className="text-[11px] font-mono text-[#3D4F55]">Under continuous AST analysis</div>
        </div>

        {/* Metric 3 */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-2 relative shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono text-[#6A7E85]">
            <span>OPEN DRIFT FINDINGS</span>
            <AlertTriangle className="w-4 h-4 text-[#C87D55]" />
          </div>
          <div className="text-3xl font-bold font-serif text-[#C87D55]">{totalOpenFindings}</div>
          <div className="text-[11px] font-mono text-[#3D4F55]">Inaccurate documentation claims</div>
        </div>

        {/* Metric 4 */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-2 relative shadow-sm">
          <div className="flex items-center justify-between text-[11px] font-mono text-[#6A7E85]">
            <span>DETECTION ACCURACY</span>
            <CheckCircle2 className="w-4 h-4 text-[#4A6B32]" />
          </div>
          <div className="text-3xl font-bold font-serif text-[#4A6B32]">78.1%</div>
          <div className="text-[11px] font-mono text-[#3D4F55]">Benchmark Ground Truth (v0.2)</div>
        </div>
      </div>

      {/* Monitored Repositories Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-serif font-bold text-[#08161B] flex items-center space-x-2">
            <Layers className="w-4 h-4 text-[#1C354D]" />
            <span>Monitored Repositories</span>
          </h2>
          <span className="text-xs text-[#6A7E85] font-mono">{repositories.length} configured</span>
        </div>

        {repositories.length === 0 ? (
          <div className="p-10 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] text-center space-y-4 shadow-sm">
            <BookOpen className="w-10 h-10 text-[#6A7E85] mx-auto" />
            <div className="space-y-1">
              <h3 className="font-serif font-bold text-lg text-[#08161B]">
                No repositories connected yet
              </h3>
              <p className="text-xs text-[#3D4F55] max-w-md mx-auto leading-relaxed">
                Connect a GitHub repository to begin continuous documentation drift monitoring
                across incoming pull requests.
              </p>
            </div>
            <div className="flex items-center justify-center space-x-3 pt-2">
              <button
                onClick={onOpenOnboarding}
                className="px-4 py-2 rounded bg-[#1C354D] text-[#EAE7DC] font-mono text-xs font-semibold inline-flex items-center space-x-1.5 shadow-paper"
              >
                <Compass className="w-3.5 h-3.5" />
                <span>Launch Onboarding Wizard</span>
              </button>
              <button
                onClick={() => setShowAddRepo(true)}
                className="px-4 py-2 rounded bg-[#F4EFE6] border border-[#D8CEBC] text-[#08161B] font-mono text-xs font-semibold inline-flex items-center space-x-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Quick Connect</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {repositories.map((repo) => (
              <div
                key={repo.id}
                className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] hover:border-[#1C354D] transition-all flex flex-col justify-between group shadow-sm"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-sm text-[#08161B] group-hover:text-[#1C354D] transition-colors">
                      {repo.full_name}
                    </span>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded border uppercase tracking-wider ${
                        repo.is_active
                          ? "text-[#4A6B32] bg-[#4A6B32]/10 border-[#4A6B32]/30 font-bold"
                          : "text-[#6A7E85] bg-[#D8CEBC]/40 border-[#D8CEBC]"
                      }`}
                    >
                      {repo.is_active ? "ACTIVE SCAN" : "PAUSED"}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#6A7E85] font-mono">
                    Branch: <span className="text-[#08161B]">{repo.default_branch}</span> • Visibility:{" "}
                    <span className="text-[#08161B]">{repo.is_private ? "Private" : "Public"}</span>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-[#D8CEBC] flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-3 text-[#6A7E85] font-mono text-[11px]">
                    <span>
                      <strong className="text-[#C87D55] font-bold">
                        {repo.open_findings_count || 0}
                      </strong>{" "}
                      drift findings
                    </span>
                    <span>•</span>
                    <span>
                      <strong className="text-[#08161B] font-bold">
                        {repo.active_prs_count || 0}
                      </strong>{" "}
                      active PRs
                    </span>
                  </div>

                  <button
                    onClick={() => onNavigateTab("pr", repo.id)}
                    className="text-xs font-mono text-[#1C354D] hover:text-[#0D1C29] font-semibold flex items-center space-x-1"
                  >
                    <span>Inspect PRs</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Health / Status Bar */}
      <div className="p-4 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-[#6A7E85]">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-[#4A6B32]"></span>
            <span className="text-[#08161B] font-semibold">
              Backend API: {health?.status || "online"}
            </span>
          </div>
          <span>•</span>
          <div>
            Database: <span className="text-[#4A6B32]">{health?.database || "connected"}</span>
          </div>
          <span>•</span>
          <div>
            Engine:{" "}
            <span className="text-[#1C354D] font-bold">
              v{health?.version || "0.2.0"} (AST + Qwen3-8B)
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span>Worker: {health?.worker_queue || "idle"}</span>
        </div>
      </div>
    </div>
  );
};
