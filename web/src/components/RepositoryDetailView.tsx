import React, { useEffect, useState } from "react";
import {
  BookOpen,
  GitPullRequest,
  History,
  Settings,
  ArrowLeft,
  RefreshCw,
  ExternalLink,
  Shield,
  Play,
} from "lucide-react";
import { api, AnalysisRun, PullRequest, Repository } from "../api/client";

interface RepositoryDetailViewProps {
  repositoryId?: string;
  onBack: () => void;
  onInspectPR: (prId: string) => void;
}

export const RepositoryDetailView: React.FC<RepositoryDetailViewProps> = ({
  repositoryId,
  onBack,
  onInspectPR,
}) => {
  const [repository, setRepository] = useState<Repository | null>(null);
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisRun[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"prs" | "history" | "settings">("prs");
  const [triggeringScan, setTriggeringScan] = useState(false);

  const loadData = async () => {
    if (!repositoryId) return;
    setLoading(true);
    setError(null);
    try {
      const [repo, prs, runs] = await Promise.all([
        api.getRepository(repositoryId).catch(() => null),
        api.listRepositoryPRs(repositoryId).catch(() => []),
        api.listRepositoryAnalyses(repositoryId).catch(() => []),
      ]);
      setRepository(repo);
      setPullRequests(prs);
      setAnalyses(runs);
    } catch (err: any) {
      setError(err.message || "Failed to load repository details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [repositoryId]);

  const handleTriggerAnalysis = async () => {
    if (!repository) return;
    setTriggeringScan(true);
    try {
      if (pullRequests.length > 0) {
        await api.triggerAnalysis(pullRequests[0].id);
        loadData();
      } else {
        alert(
          "No pull requests currently open to trigger. Open or sync a pull request on GitHub to trigger continuous analysis."
        );
      }
    } catch (err: any) {
      alert(`Trigger error: ${err.message}`);
    } finally {
      setTriggeringScan(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4EFE6] text-[#08161B] p-8 space-y-6 font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Back button & Repo Header */}
      <div className="space-y-4">
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 font-mono">
            {error}
          </div>
        )}
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-1.5 text-xs font-mono text-[#6A7E85] hover:text-[#08161B] transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Monitored Repositories</span>
        </button>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8CEBC] pb-6">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <BookOpen className="w-6 h-6 text-[#1C354D]" />
              <h1 className="font-serif text-3xl font-bold text-[#08161B]">
                {repository?.full_name || "Repository Details"}
              </h1>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-[#4A6B32]/10 border border-[#4A6B32]/30 text-[#4A6B32] font-semibold">
                Default: {repository?.default_branch || "main"}
              </span>
            </div>
            <p className="text-xs text-[#6A7E85] font-mono">
              Clone URL: <span className="text-[#08161B]">{repository?.clone_url}</span>
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleTriggerAnalysis}
              disabled={triggeringScan}
              className="px-3.5 py-2 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] text-xs font-mono font-semibold flex items-center space-x-1.5 transition-colors shadow-paper"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{triggeringScan ? "Analyzing..." : "Trigger Drift Scan"}</span>
            </button>
            <button
              onClick={loadData}
              disabled={loading}
              className="p-2 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#3D4F55] transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <a
              href={repository?.clone_url?.replace(".git", "") || "#"}
              target="_blank"
              rel="noreferrer"
              className="px-3 py-2 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-xs font-mono text-[#08161B] flex items-center space-x-1.5 transition-colors"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3.5 h-3.5 text-[#6A7E85]" />
            </a>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-4 border-b border-[#D8CEBC] text-xs font-mono">
        <button
          onClick={() => setActiveTab("prs")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-colors ${
            activeTab === "prs"
              ? "border-[#1C354D] text-[#1C354D] font-bold"
              : "border-transparent text-[#6A7E85] hover:text-[#08161B]"
          }`}
        >
          <GitPullRequest className="w-3.5 h-3.5" />
          <span>Pull Requests ({pullRequests.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("history")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-colors ${
            activeTab === "history"
              ? "border-[#1C354D] text-[#1C354D] font-bold"
              : "border-transparent text-[#6A7E85] hover:text-[#08161B]"
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Scan History ({analyses.length})</span>
        </button>

        <button
          onClick={() => setActiveTab("settings")}
          className={`pb-3 border-b-2 flex items-center space-x-2 transition-colors ${
            activeTab === "settings"
              ? "border-[#1C354D] text-[#1C354D] font-bold"
              : "border-transparent text-[#6A7E85] hover:text-[#08161B]"
          }`}
        >
          <Settings className="w-3.5 h-3.5" />
          <span>Repository Config</span>
        </button>
      </div>

      {/* Tab 1: Pull Requests */}
      {activeTab === "prs" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-[#6A7E85] font-mono">
            <span>Pull requests monitored for documentation drift</span>
          </div>

          {pullRequests.length === 0 ? (
            <div className="p-8 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] text-center space-y-3 font-mono">
              <GitPullRequest className="w-8 h-8 text-[#6A7E85] mx-auto" />
              <div className="font-bold text-sm text-[#08161B]">
                No active pull requests discovered yet
              </div>
              <p className="text-xs text-[#3D4F55] max-w-sm mx-auto font-sans">
                As pull requests open on GitHub or webhook events trigger, they will be listed here
                with automated AST drift inspection.
              </p>
              <button
                onClick={() => onInspectPR("rw-httpx-653")}
                className="px-4 py-2 rounded bg-[#1C354D] text-[#EAE7DC] text-xs font-mono font-semibold inline-flex items-center space-x-1.5"
              >
                <span>Inspect Benchmark PR Reference</span>
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#D8CEBC] bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg overflow-hidden">
              {pullRequests.map((pr) => (
                <div
                  key={pr.id}
                  className="p-4 hover:bg-[#F4EFE6] transition-colors flex items-center justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-[#08161B] text-sm">
                        PR #{pr.pr_number}: {pr.title}
                      </span>
                    </div>
                    <div className="text-xs font-mono text-[#6A7E85] flex items-center space-x-2">
                      <span>Author: {pr.author_username}</span>
                      <span>•</span>
                      <span>
                        Branch: {pr.head_ref} ➔ {pr.base_ref}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => onInspectPR(pr.id)}
                    className="px-3 py-1.5 rounded bg-[#1C354D] text-[#EAE7DC] font-semibold text-xs font-mono flex items-center space-x-1.5"
                  >
                    <Shield className="w-3.5 h-3.5" />
                    <span>Inspect Drift</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Scan History */}
      {activeTab === "history" && (
        <div className="space-y-3">
          {analyses.length === 0 ? (
            <div className="p-8 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] text-center space-y-2 font-mono">
              <History className="w-8 h-8 text-[#6A7E85] mx-auto" />
              <div className="font-bold text-sm text-[#08161B]">No drift analysis runs yet</div>
              <p className="text-xs text-[#3D4F55] font-sans">
                Trigger a scan above or send a GitHub webhook event to produce inspection runs.
              </p>
            </div>
          ) : (
            analyses.map((run) => (
              <div
                key={run.id}
                className="p-4 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] flex items-center justify-between text-xs font-mono"
              >
                <div>
                  <span className="text-[#1C354D] font-bold">{run.id.slice(0, 13)}</span>
                  <span className="text-[#6A7E85] ml-2">
                    • Trigger: {run.trigger_type} • Tool: {run.tool_version}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-[#08161B]">
                  <span>{run.duration_ms} ms</span>
                  <span className="px-2 py-0.5 rounded bg-[#4A6B32] text-white text-[10px] font-bold uppercase">
                    {run.status}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 3: Settings */}
      {activeTab === "settings" && (
        <div className="p-6 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-4 font-mono text-xs">
          <h2 className="font-serif font-bold text-base text-[#08161B]">
            Repository Drift Detection Overrides
          </h2>
          <div className="space-y-3 max-w-lg">
            <div>
              <label className="text-[#3D4F55] block mb-1">Markdown Documentation Path</label>
              <input
                type="text"
                defaultValue="docs/**/*.md, README.md"
                className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B]"
              />
            </div>
            <div>
              <label className="text-[#3D4F55] block mb-1">Source Code Tree</label>
              <input
                type="text"
                defaultValue="src/, backend/"
                className="w-full px-3 py-2 bg-[#F4EFE6] border border-[#D8CEBC] rounded text-[#08161B]"
              />
            </div>
            <button className="px-4 py-2 bg-[#1C354D] text-[#EAE7DC] rounded font-semibold">
              Save Configuration Override
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
