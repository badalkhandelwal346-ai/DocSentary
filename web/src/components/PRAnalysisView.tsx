import React, { useState, useEffect } from "react";
import { SCENARIOS } from "../data/mockScenarios";
import { EvidenceComparison } from "./EvidenceComparison";
import {
  GitPullRequest,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  Download,
  Search,
  AlertCircle,
} from "lucide-react";
import { api, Repository } from "../api/client";

interface PRAnalysisViewProps {
  selectedRepoId?: string;
}

export const PRAnalysisView: React.FC<PRAnalysisViewProps> = ({ selectedRepoId }) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("rw-httpx-653");
  const [expandedFindingId, setExpandedFindingId] = useState<string | null>("DG-0001");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [showJsonModal, setShowJsonModal] = useState<boolean>(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);

  useEffect(() => {
    async function loadRepos() {
      try {
        const repos = await api.listRepositories();
        setRepositories(repos);
      } catch {
        // Fallback
      }
    }
    loadRepos();
  }, []);

  const activeRepo = selectedRepoId ? repositories.find((r) => r.id === selectedRepoId) : null;

  const scenario = SCENARIOS.find((s) => s.id === selectedScenarioId) || SCENARIOS[0];
  const report = scenario.report;

  const filteredFindings = report.findings.filter((f) => {
    if (statusFilter !== "all" && f.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = f.title.toLowerCase().includes(q);
      const matchRule = f.rule_id.toLowerCase().includes(q);
      const matchExpl = f.explanation.toLowerCase().includes(q);
      return matchTitle || matchRule || matchExpl;
    }
    return true;
  });

  const driftCount = report.summary.drift || 0;
  const potentialCount = report.summary.potential_drift || 0;

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4EFE6] text-[#08161B] p-6 lg:p-8 space-y-6 font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Top Selector Card */}
      <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-5 shadow-editorial">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
          <div>
            {activeRepo && (
              <div className="text-xs font-mono text-[#1C354D] mb-1 font-bold">
                Repository Scope: {activeRepo.full_name}
              </div>
            )}
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#4A6B32] font-semibold">
              Pull Request Inspection
            </span>
            <h2 className="font-serif text-2xl font-bold text-[#08161B]">
              Select a Pull Request to Inspect
            </h2>
          </div>
          <button
            onClick={() => setShowJsonModal(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#F4EFE6] hover:bg-[#E2DACB] text-xs font-mono text-[#08161B] border border-[#D8CEBC] transition-colors self-start md:self-auto"
          >
            <Download className="w-3.5 h-3.5 text-[#1C354D]" />
            <span>Inspect report.json</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {SCENARIOS.map((s) => {
            const isSelected = s.id === selectedScenarioId;
            const hasDrift = s.report.summary.drift > 0;
            return (
              <button
                key={s.id}
                onClick={() => {
                  setSelectedScenarioId(s.id);
                  setExpandedFindingId(s.report.findings[0]?.finding_id || null);
                }}
                className={`p-3 text-left rounded border transition-all ${
                  isSelected
                    ? "bg-[#F4EFE6] border-[#1C354D] shadow-sm ring-1 ring-[#1C354D]"
                    : "bg-[#EBE4D8] border-[#D8CEBC] hover:bg-[#F4EFE6]"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center space-x-1.5">
                    <span className="font-mono text-[#6A7E85] text-[11px]">PR #{s.prNumber}</span>
                    {s.category === "real_world" && (
                      <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-[#C87D55]/15 text-[#C87D55] font-bold">
                        REAL-WORLD
                      </span>
                    )}
                  </div>
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold uppercase ${
                      hasDrift
                        ? "bg-red-100 text-red-700 border border-red-300"
                        : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                    }`}
                  >
                    {hasDrift ? "DRIFT" : "NO DRIFT"}
                  </span>
                </div>
                <div className="text-xs font-semibold text-[#08161B] truncate">{s.prTitle}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Pull Request Header Banner */}
      <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-6 space-y-4 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2.5">
              <span className="flex items-center space-x-1.5 px-2.5 py-0.5 rounded text-xs font-mono bg-[#1C354D] text-[#EAE7DC]">
                <GitPullRequest className="w-3.5 h-3.5" />
                <span>PR #{scenario.prNumber}</span>
              </span>
              <h1 className="font-serif text-2xl font-bold text-[#08161B] tracking-tight">
                {scenario.prTitle}
              </h1>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-[#6A7E85] font-mono">
              <span>
                Author: <strong className="text-[#08161B] font-semibold">@{scenario.author}</strong>
              </span>
              <span>•</span>
              <span>
                Branch: <span className="text-[#1C354D] font-bold">{scenario.branch}</span> ➔{" "}
                {scenario.targetBranch}
              </span>
              <span>•</span>
              <span>
                Base: <code className="text-[#08161B]">{report.base_sha.slice(0, 7)}</code>
              </span>
              <span>•</span>
              <span>
                Head: <code className="text-[#1C354D] font-bold">{report.head_sha.slice(0, 7)}</code>
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-2 self-start md:self-auto font-mono">
            <span className="flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs bg-[#F4EFE6] border border-[#D8CEBC] text-[#3D4F55]">
              <Clock className="w-3.5 h-3.5 text-[#6A7E85]" />
              <span>{report.duration_ms} ms</span>
            </span>
            <span
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-bold uppercase tracking-wider ${
                driftCount > 0
                  ? "bg-red-100 text-red-800 border border-red-300"
                  : "bg-emerald-100 text-emerald-800 border border-emerald-300"
              }`}
            >
              {driftCount > 0 ? (
                <>
                  <AlertCircle className="w-4 h-4 text-red-700" />
                  <span>Drift Detected</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                  <span>Docs In Sync</span>
                </>
              )}
            </span>
          </div>
        </div>

        {/* Summary Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-[#D8CEBC]">
          <div className="bg-[#F4EFE6] p-3.5 rounded border border-[#D8CEBC]">
            <div className="text-[10px] font-mono uppercase text-[#6A7E85]">Confirmed Drift</div>
            <div
              className={`text-2xl font-bold font-serif mt-0.5 ${
                driftCount > 0 ? "text-[#C87D55]" : "text-[#08161B]"
              }`}
            >
              {driftCount}
            </div>
          </div>
          <div className="bg-[#F4EFE6] p-3.5 rounded border border-[#D8CEBC]">
            <div className="text-[10px] font-mono uppercase text-[#6A7E85]">Potential Drift</div>
            <div className="text-2xl font-bold font-serif mt-0.5 text-[#C87D55]">
              {potentialCount}
            </div>
          </div>
          <div className="bg-[#F4EFE6] p-3.5 rounded border border-[#D8CEBC]">
            <div className="text-[10px] font-mono uppercase text-[#6A7E85]">Files Changed</div>
            <div className="text-2xl font-bold font-serif mt-0.5 text-[#08161B]">
              {report.summary.changed_files}
            </div>
          </div>
          <div className="bg-[#F4EFE6] p-3.5 rounded border border-[#D8CEBC]">
            <div className="text-[10px] font-mono uppercase text-[#6A7E85]">Docs Inspected</div>
            <div className="text-2xl font-bold font-serif mt-0.5 text-[#4A6B32]">
              {report.summary.doc_spans || 12}
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center space-x-2 w-full sm:w-auto font-mono">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-[#6A7E85]" />
            <input
              type="text"
              placeholder="Search findings or rule ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#EBE4D8] border border-[#D8CEBC] rounded text-[#08161B] placeholder-[#6A7E85] focus:outline-none focus:border-[#1C354D]"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-[#EBE4D8] border border-[#D8CEBC] rounded text-[#08161B] focus:outline-none focus:border-[#1C354D]"
          >
            <option value="all">All Statuses</option>
            <option value="DRIFT">Confirmed Drift</option>
            <option value="POTENTIAL_DRIFT">Potential Drift</option>
            <option value="NO_DRIFT">In Sync</option>
          </select>
        </div>

        <div className="text-xs font-mono text-[#6A7E85]">
          Showing {filteredFindings.length} of {report.findings.length} findings
        </div>
      </div>

      {/* Findings List (Accordion Style) */}
      <div className="space-y-3">
        {filteredFindings.length === 0 ? (
          <div className="p-8 text-center bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg space-y-2">
            <CheckCircle2 className="w-8 h-8 text-[#4A6B32] mx-auto" />
            <div className="font-serif font-bold text-base text-[#08161B]">
              No matching drift findings
            </div>
            <p className="text-xs text-[#3D4F55]">
              All inspected documentation claims match the extracted code AST.
            </p>
          </div>
        ) : (
          filteredFindings.map((finding) => {
            const isExpanded = expandedFindingId === finding.finding_id;
            const isDrift = finding.status === "DRIFT";
            return (
              <div
                key={finding.finding_id}
                className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg overflow-hidden shadow-sm transition-all"
              >
                {/* Header row */}
                <div
                  onClick={() => setExpandedFindingId(isExpanded ? null : finding.finding_id)}
                  className="p-4 cursor-pointer hover:bg-[#E2DACB] transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center space-x-3 truncate">
                    <span
                      className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        isDrift
                          ? "bg-[#C87D55] text-white"
                          : "bg-[#4A6B32] text-white"
                      }`}
                    >
                      {finding.status}
                    </span>
                    <span className="font-mono text-xs text-[#6A7E85]">
                      {finding.rule_id}
                    </span>
                    <span className="font-serif font-bold text-sm text-[#08161B] truncate">
                      {finding.title}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-[11px] font-mono text-[#6A7E85] hidden sm:inline">
                      {finding.evidence.length} evidence anchors
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-[#08161B]" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[#08161B]" />
                    )}
                  </div>
                </div>

                {/* Expanded Cyanotype Inspector */}
                {isExpanded && (
                  <div className="p-4 border-t border-[#D8CEBC] bg-[#F4EFE6]">
                    <EvidenceComparison finding={finding} />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Raw JSON Report Modal */}
      {showJsonModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
          <div className="max-w-3xl w-full bg-[#08161B] text-[#EAE7DC] border border-[#1C354D] rounded-lg p-6 space-y-4 max-h-[80vh] flex flex-col font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[#1C354D] pb-3">
              <span className="font-bold text-sm text-[#5894C4]">
                DocSentry report.json — Schema v0.2
              </span>
              <button
                onClick={() => setShowJsonModal(false)}
                className="text-[#8DA0A8] hover:text-white"
              >
                Close ✕
              </button>
            </div>
            <pre className="overflow-auto flex-1 p-3 bg-[#0D1C29] rounded text-[11px] leading-relaxed text-[#EAE7DC]">
              {JSON.stringify(report, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
