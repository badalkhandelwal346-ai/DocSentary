import React, { useState } from "react";
import { Finding } from "../data/mockScenarios";
import {
  FileText,
  Code2,
  ArrowRight,
  ShieldCheck,
  Copy,
  Check,
  Sparkles,
  Cpu,
  CheckCircle2,
  XCircle,
  HelpCircle,
} from "lucide-react";
import { api } from "../api/client";

interface EvidenceComparisonProps {
  finding: Finding;
  onStatusUpdated?: (findingId: string, status: "acknowledged" | "dismissed" | "resolved") => void;
}

export const EvidenceComparison: React.FC<EvidenceComparisonProps> = ({
  finding,
  onStatusUpdated,
}) => {
  const [copiedCode, setCopiedCode] = useState(false);
  const [copiedDoc, setCopiedDoc] = useState(false);
  const [resolutionStatus, setResolutionStatus] = useState<string>("open");
  const [isUpdating, setIsUpdating] = useState(false);

  const codeEvidence = finding.evidence.find((e) => e.role === "code");
  const docEvidence = finding.evidence.find((e) => e.role === "documentation");

  const handleCopy = (text: string, type: "code" | "doc") => {
    navigator.clipboard.writeText(text);
    if (type === "code") {
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } else {
      setCopiedDoc(true);
      setTimeout(() => setCopiedDoc(false), 2000);
    }
  };

  const handleUpdateStatus = async (status: "acknowledged" | "dismissed" | "resolved") => {
    setIsUpdating(true);
    try {
      if (finding.finding_id && !finding.finding_id.startsWith("mock-")) {
        await api.updateFindingStatus(
          finding.finding_id,
          status,
          `User marked as ${status} via dashboard`
        );
      }
      setResolutionStatus(status);
      onStatusUpdated?.(finding.finding_id, status);
    } catch {
      // In local mode, still update UI state cleanly
      setResolutionStatus(status);
      onStatusUpdated?.(finding.finding_id, status);
    } finally {
      setIsUpdating(false);
    }
  };

  const provenance =
    finding.provenance ||
    (finding.verification === "deterministic"
      ? "DETERMINISTIC"
      : finding.verification === "model_assisted"
      ? "QWEN3-8B VERIFIED"
      : "EVIDENCE VALIDATED");

  return (
    <div className="space-y-4 font-sans">
      {/* Cyanotype Provenance Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 bg-[#08161B] border border-[#1C354D] rounded-lg text-xs font-mono text-[#EAE7DC]">
        <div className="flex items-center space-x-2">
          <span className="text-[#8DA0A8] text-[11px] uppercase tracking-wider">Provenance:</span>
          {provenance === "DETERMINISTIC" && (
            <span className="inline-flex items-center space-x-1 text-[#EAE7DC] bg-[#1C354D] px-2.5 py-0.5 rounded border border-[#5894C4] text-[10px] font-bold">
              <Cpu className="w-3 h-3 text-[#5894C4]" />
              <span>DETERMINISTIC RULE ENGINE</span>
            </span>
          )}
          {provenance === "QWEN3-8B VERIFIED" && (
            <span className="inline-flex items-center space-x-1 text-[#EAE7DC] bg-[#1D5B6B] px-2.5 py-0.5 rounded border border-[#5894C4] text-[10px] font-bold">
              <Sparkles className="w-3 h-3 text-[#C87D55]" />
              <span>QWEN3-8B VERIFIED</span>
            </span>
          )}
          {provenance === "EVIDENCE VALIDATED" && (
            <span className="inline-flex items-center space-x-1 text-white bg-[#4A6B32] px-2.5 py-0.5 rounded text-[10px] font-bold">
              <ShieldCheck className="w-3 h-3" />
              <span>EVIDENCE VALIDATED</span>
            </span>
          )}
        </div>

        <div className="flex items-center space-x-4 text-xs">
          <div className="text-[#8DA0A8]">
            <span>Confidence: </span>
            <span className="text-[#5894C4] font-bold">
              {finding.confidence !== null
                ? `${Math.round(finding.confidence * 100)}%`
                : "100% (Deterministic)"}
            </span>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-[#8DA0A8]">Status: </span>
            <span
              className={`px-2 py-0.5 rounded font-semibold text-[10px] uppercase border ${
                resolutionStatus === "resolved"
                  ? "bg-[#4A6B32]/30 border-[#4A6B32] text-white"
                  : resolutionStatus === "acknowledged"
                  ? "bg-[#1C354D] border-[#5894C4] text-[#5894C4]"
                  : resolutionStatus === "dismissed"
                  ? "bg-[#6A7E85]/20 border-[#6A7E85] text-[#8DA0A8]"
                  : "bg-[#C87D55]/20 border-[#C87D55] text-[#C87D55]"
              }`}
            >
              {resolutionStatus}
            </span>
          </div>
        </div>
      </div>

      {/* Side-by-Side Dual-Span Comparison (Cyanotype Dark Surface) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Documentation Evidence */}
        <div className="bg-[#0D1C29] border border-[#1C354D] rounded-lg overflow-hidden flex flex-col shadow-inner">
          <div className="px-4 py-2.5 bg-[#08161B] border-b border-[#1C354D] flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-[#EAE7DC] font-mono">
              <FileText className="w-3.5 h-3.5 text-[#C87D55]" />
              <span className="truncate max-w-[200px]">{docEvidence?.path || "Documentation"}</span>
            </div>
            <div className="flex items-center space-x-2">
              {docEvidence && (
                <span className="font-mono text-[#8DA0A8] text-[11px] bg-[#1C354D] px-2 py-0.5 rounded border border-[#1D5B6B]">
                  Lines {docEvidence.line_start}–{docEvidence.line_end}
                </span>
              )}
              {docEvidence && (
                <button
                  onClick={() => handleCopy(docEvidence.quote, "doc")}
                  className="p-1 hover:bg-[#1C354D] rounded text-[#8DA0A8] hover:text-[#EAE7DC] transition-colors"
                  title="Copy quote"
                >
                  {copiedDoc ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>
          </div>
          <div className="p-4 flex-1 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="text-[11px] font-mono uppercase tracking-wider text-[#C87D55] font-semibold flex items-center justify-between">
                <span>[Outdated Documentation Statement]</span>
                <span className="text-[10px] text-[#C87D55]/80">HEAD Snapshot</span>
              </div>
              <div className="p-3 bg-[#C87D55]/10 border border-[#C87D55]/30 rounded-md text-sm text-[#EAE7DC] leading-relaxed font-serif relative italic">
                <span>&ldquo;{docEvidence?.quote}&rdquo;</span>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#1C354D] text-[11px] text-[#8DA0A8] font-mono flex items-center justify-between">
              <span>Source: Markdown AST claim span</span>
              <span className="text-[#C87D55]">Contradicts Code AST</span>
            </div>
          </div>
        </div>

        {/* Right: Code Evidence */}
        <div className="bg-[#0D1C29] border border-[#1C354D] rounded-lg overflow-hidden flex flex-col shadow-inner">
          <div className="px-4 py-2.5 bg-[#08161B] border-b border-[#1C354D] flex items-center justify-between text-xs">
            <div className="flex items-center space-x-2 text-[#EAE7DC] font-mono">
              <Code2 className="w-3.5 h-3.5 text-[#5894C4]" />
              <span className="truncate max-w-[200px]">{codeEvidence?.path || "Source Code"}</span>
            </div>
            <div className="flex items-center space-x-2">
              {codeEvidence && (
                <span className="font-mono text-[#8DA0A8] text-[11px] bg-[#1C354D] px-2 py-0.5 rounded border border-[#1D5B6B]">
                  Line {codeEvidence.line_start}
                </span>
              )}
              {codeEvidence && (
                <button
                  onClick={() => handleCopy(codeEvidence.quote, "code")}
                  className="p-1 hover:bg-[#1C354D] rounded text-[#8DA0A8] hover:text-[#EAE7DC] transition-colors"
                  title="Copy code quote"
                >
                  {copiedCode ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>
          </div>
          <div className="p-4 flex-1 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="text-[11px] font-mono uppercase tracking-wider text-[#5894C4] font-semibold flex items-center justify-between">
                <span>[Actual Code Evidence in HEAD]</span>
                <span className="text-[10px] text-[#5894C4]/80">AST Verified</span>
              </div>
              <div className="p-3 bg-[#1C354D]/40 border border-[#5894C4]/30 rounded-md text-xs font-mono text-[#EAE7DC]">
                <code>{codeEvidence?.quote}</code>
              </div>
            </div>
            <div className="mt-3 pt-3 border-t border-[#1C354D] text-[11px] text-[#8DA0A8] font-mono flex items-center justify-between">
              <span>Source: Python AST snapshot</span>
              <span className="text-[#5894C4]">Merge-Base vs Head</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Metadata Footer & Resolution Controls */}
      <div className="p-4 bg-[#08161B] border border-[#1C354D] rounded-lg space-y-3 font-mono text-xs text-[#EAE7DC]">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#1C354D]">
          <div className="flex items-center space-x-3 text-xs">
            <span className="text-[#8DA0A8]">Rule:</span>
            <span className="bg-[#1C354D] px-2 py-0.5 rounded border border-[#1D5B6B] text-[#EAE7DC]">
              {finding.rule_id}
            </span>
            <span className="text-[#8DA0A8]">Category:</span>
            <span className="bg-[#1C354D] px-2 py-0.5 rounded border border-[#1D5B6B] text-[#EAE7DC]">
              {finding.category}
            </span>
          </div>

          {/* Action Resolution Buttons */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleUpdateStatus("acknowledged")}
              disabled={isUpdating}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors flex items-center space-x-1 ${
                resolutionStatus === "acknowledged"
                  ? "bg-[#1C354D] text-[#5894C4] border border-[#5894C4]"
                  : "bg-[#0D1C29] hover:bg-[#1C354D] text-[#8DA0A8] border border-[#1C354D]"
              }`}
            >
              <HelpCircle className="w-3 h-3" />
              <span>Acknowledge</span>
            </button>
            <button
              onClick={() => handleUpdateStatus("dismissed")}
              disabled={isUpdating}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors flex items-center space-x-1 ${
                resolutionStatus === "dismissed"
                  ? "bg-[#6A7E85]/30 text-white border border-[#6A7E85]"
                  : "bg-[#0D1C29] hover:bg-[#1C354D] text-[#8DA0A8] border border-[#1C354D]"
              }`}
            >
              <XCircle className="w-3 h-3" />
              <span>Dismiss</span>
            </button>
            <button
              onClick={() => handleUpdateStatus("resolved")}
              disabled={isUpdating}
              className={`px-2.5 py-1 rounded text-xs font-mono transition-colors flex items-center space-x-1 ${
                resolutionStatus === "resolved"
                  ? "bg-[#4A6B32] text-white border border-[#4A6B32]"
                  : "bg-[#4A6B32]/20 hover:bg-[#4A6B32]/40 text-[#EAE7DC] border border-[#4A6B32]"
              }`}
            >
              <CheckCircle2 className="w-3 h-3 text-[#4A6B32]" />
              <span>Mark Resolved</span>
            </button>
          </div>
        </div>

        <div>
          <div className="text-xs font-bold text-[#8DA0A8] mb-1 uppercase tracking-wider">
            Why DocSentry Flagged This
          </div>
          <p className="text-xs text-[#EAE7DC] leading-relaxed font-sans">{finding.explanation}</p>
        </div>

        {finding.suggested_action && (
          <div className="pt-2 flex items-start space-x-2 text-xs text-[#EAE7DC] bg-[#1C354D]/40 p-2.5 rounded border border-[#5894C4]/30">
            <ArrowRight className="w-4 h-4 text-[#5894C4] mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-bold text-[#5894C4]">Recommended Remediation: </span>
              <span>{finding.suggested_action}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
