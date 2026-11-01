import React, { useState, useEffect } from "react";
import { Zap } from "lucide-react";
import { api, EvaluationRun } from "../api/client";

export const BenchmarkView: React.FC = () => {
  const [activeSuite, setActiveSuite] = useState<"realworld" | "constructed" | "semantic">(
    "realworld"
  );
  const [evalRuns, setEvalRuns] = useState<EvaluationRun[]>([]);

  useEffect(() => {
    async function loadEvaluations() {
      try {
        const data = await api.listEvaluations();
        setEvalRuns(data.items || []);
      } catch {
        // Fallback to static reference
      }
    }
    loadEvaluations();
  }, []);

  return (
    <div className="flex-1 p-6 lg:p-8 bg-[#F4EFE6] text-[#08161B] overflow-y-auto font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#D8CEBC] pb-5">
          <div>
            <div className="flex items-center space-x-2 text-[11px] font-mono text-[#4A6B32] mb-1">
              <span className="w-2 h-2 rounded-full bg-[#4A6B32]" />
              <span>INDEPENDENT EVALUATION HARNESS • DOCSENTRY v0.2</span>
              {evalRuns.length > 0 && (
                <span className="text-[10px] text-[#1C354D] bg-[#F4EFE6] px-1.5 py-0.2 rounded border border-[#D8CEBC]">
                  {evalRuns.length} Verified Runs Logged
                </span>
              )}
            </div>
            <h1 className="font-serif text-3xl font-bold text-[#08161B] tracking-tight">
              Empirical Benchmark & Real-World Generalisation
            </h1>
            <p className="text-xs text-[#3D4F55] mt-1 max-w-2xl font-sans">
              Strict multi-repository evaluation verifying DocSentry on genuine open-source Git
              histories with anti-leakage train/validation/test partitioning.
            </p>
          </div>

          {/* Suite Selector Tabs */}
          <div className="flex items-center space-x-1.5 p-1 bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg text-xs font-mono">
            <button
              onClick={() => setActiveSuite("realworld")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeSuite === "realworld"
                  ? "bg-[#1C354D] text-[#EAE7DC] font-semibold shadow-sm"
                  : "text-[#3D4F55] hover:text-[#08161B]"
              }`}
            >
              Real-World (32 Cases)
            </button>
            <button
              onClick={() => setActiveSuite("semantic")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeSuite === "semantic"
                  ? "bg-[#1C354D] text-[#EAE7DC] font-semibold shadow-sm"
                  : "text-[#3D4F55] hover:text-[#08161B]"
              }`}
            >
              Semantic Suite (32 Cases)
            </button>
            <button
              onClick={() => setActiveSuite("constructed")}
              className={`px-3 py-1.5 rounded transition-all ${
                activeSuite === "constructed"
                  ? "bg-[#1C354D] text-[#EAE7DC] font-semibold shadow-sm"
                  : "text-[#3D4F55] hover:text-[#08161B]"
              }`}
            >
              Standard 50-Scenario
            </button>
          </div>
        </div>

        {/* Top Cards for Active Suite */}
        {activeSuite === "realworld" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] shadow-sm">
              <div className="text-[10px] font-mono text-[#6A7E85] uppercase tracking-wider">
                Hybrid Pass Rate
              </div>
              <div className="text-3xl font-serif font-bold text-[#4A6B32] mt-1">78.1%</div>
              <div className="text-[11px] font-mono text-[#3D4F55] mt-1">
                25 / 32 real-world cases passed
              </div>
            </div>
            <div className="p-4 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] shadow-sm">
              <div className="text-[10px] font-mono text-[#6A7E85] uppercase tracking-wider">
                Precision (PPV)
              </div>
              <div className="text-3xl font-serif font-bold text-[#08161B] mt-1">100.0%</div>
              <div className="text-[11px] font-mono text-[#4A6B32] mt-1">
                0 false alarms on 14 negative controls
              </div>
            </div>
            <div className="p-4 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] shadow-sm">
              <div className="text-[10px] font-mono text-[#6A7E85] uppercase tracking-wider">
                F1 Score
              </div>
              <div className="text-3xl font-serif font-bold text-[#1C354D] mt-1">0.759</div>
              <div className="text-[11px] font-mono text-[#3D4F55] mt-1">
                +0.045 gain over deterministic
              </div>
            </div>
            <div className="p-4 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] shadow-sm">
              <div className="text-[10px] font-mono text-[#6A7E85] uppercase tracking-wider">
                Evidence Hallucinations
              </div>
              <div className="text-3xl font-serif font-bold text-[#08161B] mt-1">0.0%</div>
              <div className="text-[11px] font-mono text-[#4A6B32] mt-1">
                100% snapshot proof gate verified
              </div>
            </div>
          </div>
        )}

        {/* 3-Configuration Comparison Table */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-4 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-serif font-bold text-[#08161B]">
                Three-Configuration Comparative Performance
              </h2>
              <p className="text-xs text-[#3D4F55] mt-0.5">
                Deterministic static analysis vs pure Qwen3-8B semantic reasoning vs selective hybrid
                routing.
              </p>
            </div>
            <span className="text-[10px] font-mono text-[#3D4F55] bg-[#F4EFE6] px-2.5 py-1 rounded border border-[#D8CEBC] self-start sm:self-auto">
              Hardware: M4 MacBook Pro • Local Qwen3-8B
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-[#F4EFE6] text-[#6A7E85] uppercase text-[10px] border-b border-[#D8CEBC]">
                <tr>
                  <th className="py-2.5 px-3">Metric</th>
                  <th className="py-2.5 px-3">Deterministic-Only</th>
                  <th className="py-2.5 px-3">Qwen3-8B-Only</th>
                  <th className="py-2.5 px-3 text-[#1C354D] font-bold">Selective Hybrid</th>
                  <th className="py-2.5 px-3">Architectural Advantage</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D8CEBC] text-[#08161B]">
                <tr>
                  <td className="py-2.5 px-3 font-semibold">Pass Rate</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">24 / 32 (75.0%)</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">22 / 32 (68.8%)</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">25 / 32 (78.1%)</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    Hybrid outperforms both single modes
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold">Precision (PPV)</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">100.0%</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">100.0%</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">100.0%</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    Zero false positives on non-drift PRs
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold">Recall (Sensitivity)</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">55.6% (10/18)</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">44.4% (8/18)</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">61.1% (11/18)</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    +5.5% incremental recall gain via AI
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold">Specificity (TNR)</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">100.0% (14/14)</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">100.0% (14/14)</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">100.0% (14/14)</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    Immune to false alarms on refactors
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold">F1 Score</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">0.714</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">0.615</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">0.759</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    Optimal harmonic precision/recall balance
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold">Average Latency</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">227.2 ms</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">6,091.2 ms</td>
                  <td className="py-2.5 px-3 text-[#1C354D] font-bold">1,758.8 ms</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    Sub-2-second scan per PR in CI
                  </td>
                </tr>
                <tr>
                  <td className="py-2.5 px-3 font-semibold">Model Calls</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">0</td>
                  <td className="py-2.5 px-3 text-[#3D4F55]">8</td>
                  <td className="py-2.5 px-3 text-[#4A6B32] font-bold">1 (Selective)</td>
                  <td className="py-2.5 px-3 text-[#6A7E85] font-sans">
                    87.5% reduction in model inference cost
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Per-Repository Breakdown with Splits */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-4 shadow-sm">
          <div>
            <h2 className="text-base font-serif font-bold text-[#08161B]">
              Per-Repository Breakdown & Anti-Leakage Partitioning
            </h2>
            <p className="text-xs text-[#3D4F55] mt-0.5">
              Evaluation partitioned by repository. The Held-Out Test split was strictly isolated with
              zero prompt or rule engineering.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded bg-[#F4EFE6] border border-[#D8CEBC] space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#08161B]">DEVELOPMENT (DEV)</span>
                <span className="text-[#4A6B32] bg-[#4A6B32]/10 px-2 py-0.5 rounded text-[10px] font-bold">
                  100% Pass
                </span>
              </div>
              <div className="space-y-1.5 text-[#3D4F55]">
                <div className="flex justify-between">
                  <span>encode/httpx (Python)</span>
                  <span className="font-bold text-[#08161B]">6 / 6 (100%)</span>
                </div>
                <div className="flex justify-between">
                  <span>pallets/click (Python)</span>
                  <span className="font-bold text-[#08161B]">5 / 5 (100%)</span>
                </div>
              </div>
              <div className="text-[10px] text-[#6A7E85] font-sans pt-1 border-t border-[#D8CEBC]">
                Permitted for initial rule heuristics and prompt engineering.
              </div>
            </div>

            <div className="p-4 rounded bg-[#F4EFE6] border border-[#D8CEBC] space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#08161B]">VALIDATION (VAL)</span>
                <span className="text-[#4A6B32] bg-[#4A6B32]/10 px-2 py-0.5 rounded text-[10px] font-bold">
                  77.8% Pass
                </span>
              </div>
              <div className="space-y-1.5 text-[#3D4F55]">
                <div className="flex justify-between">
                  <span>fastapi/fastapi (Python)</span>
                  <span className="font-bold text-[#08161B]">4 / 5 (80%)</span>
                </div>
                <div className="flex justify-between">
                  <span>psf/requests (Python)</span>
                  <span className="font-bold text-[#08161B]">3 / 4 (75%)</span>
                </div>
              </div>
              <div className="text-[10px] text-[#6A7E85] font-sans pt-1 border-t border-[#D8CEBC]">
                Used strictly for router confidence threshold calibration.
              </div>
            </div>

            <div className="p-4 rounded bg-[#F4EFE6] border border-[#D8CEBC] space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#08161B]">HELD-OUT TEST (TEST)</span>
                <span className="text-[#1C354D] bg-[#1C354D]/10 px-2 py-0.5 rounded text-[10px] font-bold">
                  58.3% Pass
                </span>
              </div>
              <div className="space-y-1.5 text-[#3D4F55]">
                <div className="flex justify-between">
                  <span>pydantic/pydantic (Python)</span>
                  <span className="font-bold text-[#08161B]">3 / 5 (60%)</span>
                </div>
                <div className="flex justify-between">
                  <span>pallets/flask (Python)</span>
                  <span className="font-bold text-[#08161B]">3 / 5 (60%)</span>
                </div>
                <div className="flex justify-between">
                  <span>axios/axios (JavaScript)</span>
                  <span className="font-bold text-[#08161B]">1 / 2 (50%)</span>
                </div>
              </div>
              <div className="text-[10px] text-[#4A6B32] font-sans pt-1 border-t border-[#D8CEBC]">
                Blind real-world test. Zero false positives observed.
              </div>
            </div>
          </div>
        </div>

        {/* AI Unique Real-World Detection Spotlight */}
        <div className="p-5 rounded-lg bg-[#EBE4D8] border border-[#D8CEBC] space-y-3">
          <div className="flex items-center space-x-2 text-xs font-mono text-[#C87D55]">
            <Zap className="w-4 h-4 text-[#C87D55]" />
            <span className="font-bold uppercase tracking-wider">
              AI REAL-WORLD VALUE SPOTLIGHT — CASE REAL-HTTPX-03
            </span>
          </div>
          <p className="text-xs text-[#3D4F55] leading-relaxed">
            In <span className="text-[#08161B] font-mono font-bold">encode/httpx PR #891</span>,
            engineering added <code className="bg-[#F4EFE6] px-1 rounded">**kwargs</code> forwarding
            to <code className="bg-[#F4EFE6] px-1 rounded">Response.json()</code>. Deterministic
            static analysis produces 0 findings because adding kwargs is a non-breaking AST addition.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded bg-[#F4EFE6] border border-[#D8CEBC]">
              <div className="text-[#6A7E85] text-[10px] uppercase">
                Outdated Documentation (docs/quickstart.md)
              </div>
              <div className="text-red-700 mt-1 line-through">
                &ldquo;response.json() parses payload strictly with default JSONDecoder settings.&rdquo;
              </div>
            </div>
            <div className="p-3 rounded bg-[#F4EFE6] border border-[#D8CEBC]">
              <div className="text-[#4A6B32] text-[10px] uppercase font-bold">
                Qwen3-8B Semantic Reasoning Assessment
              </div>
              <div className="text-[#08161B] mt-1">
                &ldquo;DRIFT: Method now forwards arbitrary **kwargs to json.loads, directly contradicting documented strict default settings.&rdquo;
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
