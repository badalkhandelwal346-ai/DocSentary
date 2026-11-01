import React from "react";
import {
  Shield,
  ArrowRight,
  Code2,
  FileText,
  AlertTriangle,
  Github,
  Compass,
  ExternalLink,
  GitPullRequest,
} from "lucide-react";

interface LandingPageProps {
  onNavigateSignup: () => void;
  onNavigateLogin: () => void;
  onEnterDashboard: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onNavigateSignup,
  onNavigateLogin,
  onEnterDashboard,
}) => {
  return (
    <div className="min-h-screen bg-[#F4EFE6] text-[#08161B] flex flex-col font-sans paper-grain selection:bg-[#1C354D] selection:text-[#EAE7DC]">
      {/* Editorial Masthead Top Header */}
      <header className="border-b border-[#D8CEBC] px-6 lg:px-12 h-20 flex items-center justify-between sticky top-0 bg-[#F4EFE6]/90 backdrop-blur z-50">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={onEnterDashboard}>
          <div className="w-10 h-10 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center shadow-paper border border-[#1D5B6B]">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <span className="font-serif text-2xl font-bold tracking-tight text-[#08161B] block leading-none">
              DocSentry
            </span>
            <span className="text-[10px] font-mono tracking-widest uppercase text-[#3D4F55]">
              Est. 2026 • Documentation Intelligence
            </span>
          </div>
        </div>

        <nav className="hidden md:flex items-center space-x-8 text-xs font-mono text-[#3D4F55]">
          <a href="#problem" className="hover:text-[#08161B] transition-colors">
            01. The Problem
          </a>
          <a href="#workflow" className="hover:text-[#08161B] transition-colors">
            02. Workflow
          </a>
          <a href="#evidence" className="hover:text-[#08161B] transition-colors">
            03. Evidence Engine
          </a>
          <a href="#architecture" className="hover:text-[#08161B] transition-colors">
            04. Architecture
          </a>
          <a
            href="https://github.com/Atharv386/DocSentary"
            target="_blank"
            rel="noreferrer"
            className="hover:text-[#08161B] transition-colors flex items-center space-x-1"
          >
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </nav>

        <div className="flex items-center space-x-3">
          <button
            onClick={onNavigateLogin}
            className="px-3.5 py-1.5 text-xs font-mono text-[#3D4F55] hover:text-[#08161B] transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={onNavigateSignup}
            className="px-4 py-2 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] text-xs font-mono font-semibold tracking-wide shadow-paper transition-all flex items-center space-x-1.5"
          >
            <span>Connect GitHub</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* HERO SECTION */}
      <section className="pt-20 pb-16 px-6 lg:px-12 max-w-6xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded bg-[#EBE4D8] border border-[#D8CEBC] text-[11px] font-mono text-[#4A6B32]">
          <span className="w-2 h-2 rounded-full bg-[#4A6B32] animate-pulse"></span>
          <span>DOCUMENTATION INTELLIGENCE / EST. 2026</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-serif font-bold tracking-tight text-[#08161B] leading-[1.08] max-w-4xl mx-auto">
          Your code changes. <br />
          <span className="italic font-normal text-[#1C354D]">Does your documentation</span> remember?
        </h1>

        <p className="text-base sm:text-lg text-[#3D4F55] max-w-2xl mx-auto leading-relaxed font-sans">
          DocSentry connects code changes to the documentation they may have made incorrect, giving
          developers evidence-backed visibility into documentation drift before it hits production.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <button
            onClick={onNavigateSignup}
            className="w-full sm:w-auto px-7 py-3.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-bold tracking-wide transition-all shadow-paper flex items-center justify-center space-x-2"
          >
            <Github className="w-4 h-4" />
            <span>Connect GitHub Account</span>
            <ArrowRight className="w-4 h-4" />
          </button>
          <a
            href="#problem"
            className="w-full sm:w-auto px-6 py-3.5 rounded bg-[#EBE4D8] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#08161B] font-mono text-xs font-semibold transition-all flex items-center justify-center space-x-2"
          >
            <Compass className="w-4 h-4 text-[#C87D55]" />
            <span>Explore How It Works</span>
          </a>
        </div>

        {/* HERO EDITORIAL SPECIMEN / EVIDENCE SPREAD */}
        <div className="pt-12 max-w-5xl mx-auto text-left">
          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg shadow-editorial overflow-hidden relative">
            {/* Terracotta Stamp */}
            <div className="absolute top-3 right-4 px-2.5 py-0.5 bg-[#C87D55] text-white text-[10px] font-mono uppercase tracking-wider rounded">
              SPECIMEN • PR #42 DRIFT INSPECTOR
            </div>

            {/* Specimen Header */}
            <div className="px-6 py-4 border-b border-[#D8CEBC] bg-[#F4EFE6]/70 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="w-2.5 h-2.5 rounded-full bg-[#C87D55]"></span>
                <span className="font-mono text-xs text-[#08161B] font-bold">
                  Pull Request #42: Refactor Batch Ingestion Parameters
                </span>
              </div>
              <span className="font-mono text-[11px] text-[#4A6B32] font-semibold bg-[#4A6B32]/10 px-2 py-0.5 rounded">
                AST Deterministic Match
              </span>
            </div>

            {/* Side-by-Side Dual-Span Inspector (Cyanotype Contrast) */}
            <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#D8CEBC]">
              {/* Left: Code AST Diff */}
              <div className="p-6 bg-[#08161B] text-[#EAE7DC] font-mono text-xs space-y-3">
                <div className="flex justify-between items-center text-[11px] text-[#8DA0A8] border-b border-[#1C354D] pb-2">
                  <div className="flex items-center space-x-1.5">
                    <Code2 className="w-3.5 h-3.5 text-[#5894C4]" />
                    <span className="text-[#EAE7DC]">src/engine/ingest.py</span>
                  </div>
                  <span className="text-[#5894C4]">lines 42–48</span>
                </div>
                <div className="space-y-1 font-mono text-[11px] leading-relaxed">
                  <div className="text-[#6A7E85]">  def ingest_dataset(</div>
                  <div className="text-red-400 bg-red-950/40 px-1 -mx-1">
                    -     records: List[Dict], max_batch_size: int = 50
                  </div>
                  <div className="text-emerald-400 bg-emerald-950/40 px-1 -mx-1">
                    +     records: List[Dict], batch_limit: int = 100
                  </div>
                  <div className="text-[#6A7E85]">  ) -&gt; IngestResult:</div>
                </div>
                <div className="p-2 rounded bg-[#1C354D]/50 border border-[#1D5B6B] text-[10px] text-[#8DA0A8] space-y-1">
                  <div className="font-bold text-[#5894C4]">AST Symbol Fact:</div>
                  <div>Parameter <code className="text-red-300">max_batch_size</code> renamed to <code className="text-emerald-300">batch_limit</code>; default changed from 50 to 100.</div>
                </div>
              </div>

              {/* Right: Markdown Documentation Drift */}
              <div className="p-6 bg-[#F4EFE6] text-[#08161B] space-y-3">
                <div className="flex justify-between items-center text-[11px] font-mono text-[#6A7E85] border-b border-[#D8CEBC] pb-2">
                  <div className="flex items-center space-x-1.5">
                    <FileText className="w-3.5 h-3.5 text-[#C87D55]" />
                    <span className="text-[#08161B] font-bold">docs/api/ingestion.md</span>
                  </div>
                  <span className="text-[#C87D55]">line 114</span>
                </div>
                <div className="p-3 bg-[#EBE4D8] border-l-2 border-[#C87D55] text-xs font-serif leading-relaxed italic text-[#3D4F55]">
                  &ldquo;The ingestion job processes records in chunks bounded by <mark className="bg-[#C87D55]/20 text-[#08161B] font-mono font-bold not-italic px-1">max_batch_size</mark>, which defaults to 50 items.&rdquo;
                </div>
                <div className="p-2.5 rounded bg-white/70 border border-[#D8CEBC] text-[11px] font-mono space-y-1">
                  <div className="font-bold text-[#C87D55] flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3 text-[#C87D55]" />
                    <span>CONFIRMED DRIFT DETECTED</span>
                  </div>
                  <p className="text-[#3D4F55]">
                    Documentation asserts parameter name <code className="bg-[#EBE4D8] px-1 rounded">max_batch_size</code> and default value 50, but code AST now requires <code className="bg-[#EBE4D8] px-1 rounded">batch_limit</code> with default 100.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 01 — THE PROBLEM */}
      <section id="problem" className="py-20 border-t border-[#D8CEBC] bg-[#EBE4D8]/60">
        <div className="max-w-5xl mx-auto px-6 lg:px-12 space-y-12">
          <div className="space-y-3 text-center max-w-2xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#C87D55]">
              Section 01 / The Inevitable Decay
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#08161B]">
              Code moves at pull-request speed. Documentation stays frozen in time.
            </h2>
            <p className="text-sm text-[#3D4F55] leading-relaxed">
              Every day, engineers refactor function signatures, alter environment variables, and
              rename configuration parameters. Code passes CI unit tests because the tests are
              updated—but documentation sits unnoticed until a user files a bug.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-6 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-3 shadow-sm">
              <div className="w-8 h-8 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center font-mono font-bold text-xs">
                01
              </div>
              <h3 className="font-serif font-bold text-lg text-[#08161B]">Parameter Renames</h3>
              <p className="text-xs text-[#3D4F55] leading-relaxed">
                Functions update their keyword arguments, but quickstarts and README examples
                continue instructing users to pass deleted or renamed arguments.
              </p>
            </div>

            <div className="p-6 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-3 shadow-sm">
              <div className="w-8 h-8 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center font-mono font-bold text-xs">
                02
              </div>
              <h3 className="font-serif font-bold text-lg text-[#08161B]">Return Type Changes</h3>
              <p className="text-xs text-[#3D4F55] leading-relaxed">
                APIs return structured dataclasses instead of dictionaries or tuples. Docs claim a
                primitive return value, breaking downstream client expectations.
              </p>
            </div>

            <div className="p-6 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-3 shadow-sm">
              <div className="w-8 h-8 rounded bg-[#1C354D] text-[#EAE7DC] flex items-center justify-center font-mono font-bold text-xs">
                03
              </div>
              <h3 className="font-serif font-bold text-lg text-[#08161B]">Configuration Shifts</h3>
              <p className="text-xs text-[#3D4F55] leading-relaxed">
                Environment flags like <code className="bg-[#EBE4D8] px-1 rounded">API_TIMEOUT</code> get replaced with nested YAML configs, leaving deployment guides completely obsolete.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 02 — HOW DOCSENTRY WORKS */}
      <section id="workflow" className="py-20 border-t border-[#D8CEBC] bg-[#F4EFE6]">
        <div className="max-w-5xl mx-auto px-6 lg:px-12 space-y-12">
          <div className="space-y-3 text-center max-w-2xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#4A6B32]">
              Section 02 / The Detection Loop
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#08161B]">
              Five deterministic stages. Zero hallucinated drift.
            </h2>
            <p className="text-sm text-[#3D4F55] leading-relaxed">
              DocSentry does not make vague AI guesses. Every finding is anchored directly to an AST
              symbol fact and a verified sentence from your Markdown repository files.
            </p>
          </div>

          <div className="space-y-4">
            {[
              {
                step: "01",
                title: "Git Pull Request Trigger",
                desc: "GitHub webhook delivers pull_request.opened or synchronize event with base and head commit SHAs.",
                tag: "WEBHOOK",
              },
              {
                step: "02",
                title: "Python AST Extraction",
                desc: "Static AST parser walks both revisions, recording exact function signatures, class members, and parameter defaults.",
                tag: "STATIC AST",
              },
              {
                step: "03",
                title: "Markdown Claim Extraction",
                desc: "Documentation parser isolates individual sentence claims mentioning code symbols, API calls, and configurations.",
                tag: "PARSER",
              },
              {
                step: "04",
                title: "Deterministic Rule Matching",
                desc: "Rules check for missing arguments, deleted classes, altered defaults, and type contract violations.",
                tag: "ENGINE v0.2",
              },
              {
                step: "05",
                title: "Evidence Verification & Check Run",
                desc: "Results post as GitHub Check Runs with side-by-side diff hunks and exact doc spans.",
                tag: "CHECK RUN",
              },
            ].map((s) => (
              <div
                key={s.step}
                className="p-5 bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
              >
                <div className="flex items-start space-x-4">
                  <span className="font-serif font-bold text-2xl text-[#1C354D]">{s.step}</span>
                  <div>
                    <h4 className="font-serif font-bold text-base text-[#08161B]">{s.title}</h4>
                    <p className="text-xs text-[#3D4F55] mt-0.5">{s.desc}</p>
                  </div>
                </div>
                <span className="px-2.5 py-1 bg-[#F4EFE6] border border-[#D8CEBC] text-[10px] font-mono text-[#1C354D] rounded font-semibold tracking-wider">
                  {s.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 03 — EVIDENCE NOT GUESSES */}
      <section id="evidence" className="py-20 border-t border-[#D8CEBC] bg-[#EBE4D8]/70">
        <div className="max-w-5xl mx-auto px-6 lg:px-12 space-y-12">
          <div className="space-y-3 text-center max-w-2xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#1C354D]">
              Section 03 / Provenance & Trust
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#08161B]">
              Evidence, not guesses.
            </h2>
            <p className="text-sm text-[#3D4F55] leading-relaxed">
              Developer tools must earn developer trust. When DocSentry raises a warning, you can
              audit the exact AST node and doc span that triggered it.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 font-mono text-xs">
            <div className="p-5 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-2">
              <span className="px-2 py-0.5 bg-[#1C354D] text-[#EAE7DC] text-[9px] rounded uppercase tracking-wider">
                Provenance Badge
              </span>
              <div className="font-serif font-bold text-base text-[#08161B]">DETERMINISTIC</div>
              <p className="text-xs text-[#3D4F55] font-sans">
                Direct AST comparison proves a signature mismatch without requiring AI interpretation. 100% reproducible.
              </p>
            </div>

            <div className="p-5 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-2">
              <span className="px-2 py-0.5 bg-[#C87D55] text-white text-[9px] rounded uppercase tracking-wider">
                Provenance Badge
              </span>
              <div className="font-serif font-bold text-base text-[#08161B]">QWEN3-8B VERIFIED</div>
              <p className="text-xs text-[#3D4F55] font-sans">
                Semantic reasoning identifies prose drift where wording implies behavior that the code AST no longer supports.
              </p>
            </div>

            <div className="p-5 bg-[#F4EFE6] border border-[#D8CEBC] rounded-lg space-y-2">
              <span className="px-2 py-0.5 bg-[#4A6B32] text-white text-[9px] rounded uppercase tracking-wider">
                Provenance Badge
              </span>
              <div className="font-serif font-bold text-base text-[#08161B]">EVIDENCE VALIDATED</div>
              <p className="text-xs text-[#3D4F55] font-sans">
                Independent validator verifies that both the code diff hunk and markdown sentence exist verbatim in repository trees.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 04 — ARCHITECTURE & GITHUB WORKFLOW */}
      <section id="architecture" className="py-20 border-t border-[#D8CEBC] bg-[#F4EFE6]">
        <div className="max-w-5xl mx-auto px-6 lg:px-12 space-y-12">
          <div className="space-y-3 text-center max-w-2xl mx-auto">
            <span className="text-[11px] font-mono uppercase tracking-widest text-[#4A6B32]">
              Section 04 / Developer Workflow
            </span>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-[#08161B]">
              Zero disruption to your engineering routine.
            </h2>
            <p className="text-sm text-[#3D4F55] leading-relaxed">
              DocSentry connects directly to GitHub. Developers keep writing code; DocSentry runs
              silently on pull requests and reports status checks before merge.
            </p>
          </div>

          <div className="bg-[#EBE4D8] border border-[#D8CEBC] rounded-lg p-6 md:p-8 space-y-6">
            <div className="flex items-center space-x-3 text-xs font-mono text-[#08161B] font-bold">
              <GitPullRequest className="w-4 h-4 text-[#1C354D]" />
              <span>DocSentry GitHub PR Check Run Summary</span>
            </div>

            <div className="bg-[#08161B] text-[#EAE7DC] p-4 rounded font-mono text-xs space-y-2 overflow-x-auto">
              <div className="text-emerald-400 font-bold">✓ DocSentry Analysis Complete — 1 Finding Identified</div>
              <div className="text-[#8DA0A8]">Repository: Atharv386/DocSentary • PR #42 • Head: cb6234f</div>
              <div className="pt-2 text-yellow-300">
                [DRIFT] docs/api/ingestion.md:114 — Parameter 'max_batch_size' removed in src/engine/ingest.py
              </div>
              <div className="text-[#8DA0A8] text-[11px]">
                Suggestion: Update documentation sentence to reference 'batch_limit' with default 100.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA SECTION */}
      <section className="py-20 border-t border-[#D8CEBC] bg-[#EBE4D8] text-center">
        <div className="max-w-3xl mx-auto px-6 space-y-6">
          <span className="text-[11px] font-mono uppercase tracking-widest text-[#C87D55]">
            Begin Guarding Your Documentation
          </span>
          <h2 className="font-serif text-4xl sm:text-5xl font-bold text-[#08161B]">
            Keep your documentation as trustworthy as your code.
          </h2>
          <p className="text-sm text-[#3D4F55] leading-relaxed">
            Connect your GitHub repositories in two minutes. Automated drift detection, AST-verified
            precision, and seamless pull request check runs.
          </p>
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={onNavigateSignup}
              className="w-full sm:w-auto px-8 py-3.5 rounded bg-[#1C354D] hover:bg-[#0D1C29] text-[#EAE7DC] font-mono text-xs font-bold tracking-wide transition-all shadow-paper flex items-center justify-center space-x-2"
            >
              <Github className="w-4 h-4" />
              <span>Connect GitHub & Start</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={onNavigateLogin}
              className="w-full sm:w-auto px-6 py-3.5 rounded bg-[#F4EFE6] hover:bg-[#E2DACB] border border-[#D8CEBC] text-[#08161B] font-mono text-xs font-semibold"
            >
              Sign In to Existing Workspace
            </button>
          </div>
        </div>
      </section>

      {/* EDITORIAL COLOPHON FOOTER */}
      <footer className="border-t border-[#D8CEBC] bg-[#F4EFE6] py-12 px-6 lg:px-12 text-xs font-mono text-[#6A7E85]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="space-y-1 text-center md:text-left">
            <div className="font-serif text-lg font-bold text-[#08161B]">DocSentry</div>
            <div>Documentation Drift Detection & Verification Platform</div>
            <div className="text-[10px] text-[#8DA0A8]">
              Designed & engineered for Hacktoberfest 2026 • Sonipat PS5 Edition
            </div>
          </div>

          <div className="flex items-center space-x-6 text-[11px]">
            <a
              href="https://github.com/Atharv386/DocSentary"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[#08161B] transition-colors"
            >
              GitHub Repository
            </a>
            <span className="text-[#D8CEBC]">•</span>
            <button onClick={onNavigateSignup} className="hover:text-[#08161B] transition-colors">
              Sign Up
            </button>
            <span className="text-[#D8CEBC]">•</span>
            <button onClick={onNavigateLogin} className="hover:text-[#08161B] transition-colors">
              Sign In
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
};
