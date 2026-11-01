import React, { useEffect, useState } from "react";
import { History, RefreshCw } from "lucide-react";
import { api, AnalysisRun } from "../api/client";

interface AnalysisHistoryViewProps {
  onSelectRun?: (runId: string) => void;
}

export const AnalysisHistoryView: React.FC<AnalysisHistoryViewProps> = ({
  onSelectRun: _onSelectRun,
}) => {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const loadHistory = async () => {
    setLoading(true);
    try {
      const repos = await api.listRepositories().catch(() => []);
      if (repos.length > 0) {
        const allRuns = await Promise.all(
          repos.map((r) => api.listRepositoryAnalyses(r.id).catch(() => []))
        );
        setRuns(allRuns.flat());
      } else {
        setRuns([]);
      }
    } catch {
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const filteredRuns = runs.filter((r) => {
    if (filterStatus === "all") return true;
    return r.status === filterStatus;
  });

  return (
    <div className="flex-1 overflow-y-auto bg-[#F4EFE6] text-[#08161B] p-8 space-y-6 font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8CEBC] pb-6">
        <div>
          <h1 className="font-serif text-3xl font-bold tracking-tight text-[#08161B] flex items-center space-x-2.5">
            <History className="w-6 h-6 text-[#1C354D]" />
            <span>Analysis Run History</span>
          </h1>
          <p className="text-xs text-[#3D4F55] mt-1 font-sans">
            Complete audit trail of all automated documentation drift evaluations.
          </p>
        </div>

        <div className="flex items-center space-x-3 font-mono">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-1.5 bg-[#EBE4D8] border border-[#D8CEBC] rounded text-xs text-[#08161B] focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
          <button
            onClick={loadHistory}
            disabled={loading}
            className="p-2 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#3D4F55] transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* History Table */}
      {filteredRuns.length === 0 ? (
        <div className="p-12 text-center bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg space-y-3 font-mono">
          <History className="w-10 h-10 text-[#6A7E85] mx-auto" />
          <div className="font-serif font-bold text-lg text-[#08161B]">
            No analysis runs recorded yet
          </div>
          <p className="text-xs text-[#3D4F55] max-w-sm mx-auto font-sans">
            Connect repositories and trigger pull requests or baseline scans to view historical drift
            evaluations.
          </p>
        </div>
      ) : (
        <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#F4EFE6] text-[#6A7E85] uppercase text-[10px] border-b border-[#D8CEBC]">
              <tr>
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Trigger</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Commits (Base → Head)</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#D8CEBC] text-[#08161B]">
              {filteredRuns.map((r) => (
                <tr key={r.id} className="hover:bg-[#F4EFE6] transition-colors">
                  <td className="py-3 px-4 font-bold text-[#1C354D]">{r.id.slice(0, 13)}</td>
                  <td className="py-3 px-4 text-[#3D4F55]">{r.trigger_type}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                        r.status === "completed"
                          ? "bg-[#4A6B32] text-white"
                          : r.status === "failed"
                          ? "bg-red-700 text-white"
                          : "bg-[#1C354D] text-[#EAE7DC]"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-[#6A7E85]">
                    <code>{r.base_sha?.slice(0, 7) || "base"}</code> ➔{" "}
                    <code>{r.head_sha?.slice(0, 7) || "head"}</code>
                  </td>
                  <td className="py-3 px-4 text-[#3D4F55]">{r.duration_ms} ms</td>
                  <td className="py-3 px-4 text-[#6A7E85]">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
