# DocSentry Design System — Tactile Pastoral & Analog Editorial
**Version:** 1.0.0-canonical  
**Design Directive:** Part 10 & Part 19 Mandatory Specification

---

## 1. Aesthetic Philosophy

DocSentry bridges the timeless elegance of fine editorial printmaking with the unforgiving precision of static AST analysis. 

The visual contrast is intentional:
> **"The outside feels like a beautifully printed art book. The inside reveals a precise technical instrument."**

- **Warm Editorial Surfaces:** Uncoated paper (`#F4EFE6`), aged parchment undertones, tactile alabaster cards, subtle double-ruled hairpins.
- **Cyanotype & Blueprint Tech:** Rich, deep Prussian/cyanotype blues (`#1C354D`, `#08161B`) for evidence inspection, code diffs, and AST AST fact analysis.
- **Pastoral Resonance:** Muted meadow greens (`#4A6B32`), deep moss (`#233818`), terracotta terracotta stamp accents (`#C87D55`), and towering cloud whites (`#EAE7DC`).
- **Analog Textures:** Halftone dots, subtle paper fiber grain, printmaker registration marks, stamp seals, classical serif typography, and monospaced terminal grids.

---

## 2. Mandatory Palette & Color Tokens

```css
:root {
  /* Paper Surfaces */
  --color-paper: #F4EFE6;
  --color-paper-secondary: #EBE4D8;
  --color-paper-muted: #E2DACB;
  --color-paper-border: #D8CEBC;
  
  /* Ink & Typography */
  --color-deep-ink: #08161B;
  --color-ink-muted: #3D4F55;
  --color-ink-faint: #6A7E85;
  
  /* Cyanotype & Blueprint (Technical / Evidence) */
  --color-cyanotype-deep: #0D1C29;
  --color-cyanotype: #1C354D;
  --color-halftone-teal: #1D5B6B;
  --color-cobalt: #2E6DA4;
  --color-cerulean: #5894C4;
  
  /* Pastoral Accents */
  --color-meadow: #4A6B32;
  --color-moss: #233818;
  --color-terracotta: #C87D55;
  --color-cloud-chalk: #EAE7DC;
}
```

### Prohibited Patterns
- Never use generic neon Tailwind SaaS colors (e.g. purple-indigo gradients, pure `#000000`, neon `#10B981`).
- Never use generic floating rounded glassmorphism cards.
- Surfaces must remain warm, tactile, and legible with high WCAG AAA contrast ratios.

---

## 3. Typography Hierarchy

1. **Display & Editorial Headings:**
   - Font Family: `Newsreader`, `Instrument Serif`, or `Playfair Display`, `serif`
   - Weight: Regular (400), Medium (500), Italic (400i)
   - Tracking: `-0.02em` to `-0.01em`

2. **Body & Interface Text:**
   - Font Family: `Geist`, `Inter`, `-apple-system`, `sans-serif`
   - Weight: Regular (400), Medium (500), Semibold (600)
   - Clean, neutral, high readability on uncoated paper backgrounds.

3. **Technical Metadata & Code:**
   - Font Family: `Geist Mono`, `JetBrains Mono`, `ui-monospace`, `monospace`
   - Weight: Regular (400), Medium (500)
   - Used for AST symbol names, commit SHAs, line numbers, diff blocks, rule IDs.

---

## 4. UI Layer Architecture

| Layer | Surface Treatment | Text Color | Usage |
|---|---|---|---|
| **Public Landing** | Warm Paper (`#F4EFE6`) with Halftone & Pastoral Frames | Deep Ink (`#08161B`) | Editorial storytelling, problem explanation, architecture breakdown. |
| **Auth & Onboarding** | Crisp Uncoated Paper (`#EBE4D8`) with Halftone Seal | Deep Ink & Cobalt | Signup, login, GitHub account connection, repo discovery. |
| **Workspace App** | Calmer Paper Canvas (`#F4EFE6`) & Ivory cards | Deep Ink (`#08161B`) | Repository lists, pull requests, scan history, settings. |
| **Evidence Inspector** | Dark Cyanotype (`#0D1C29` / `#1C354D`) | Cerulean, Chalk & Amber | Code diffs, Markdown spans, AST facts, Provenance stamps. |
