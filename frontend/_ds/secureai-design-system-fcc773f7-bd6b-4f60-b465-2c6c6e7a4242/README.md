# SecureAI Design System

**Product:** SecureAI Engine — AI-powered security auditor (SAST · DAST · Auto-Remediation)  
**Version:** v1.0 | April 2026

---

## Product Overview

SecureAI Engine is a next-generation AI security platform targeting developers, security engineers, and DevSecOps teams. It combines static analysis (SAST), dynamic testing (DAST), and AI-powered patch generation into a single autonomous pipeline.

**Core surfaces:**
- **Web Editor App** — 3-panel IDE-like interface: file tree sidebar, Monaco code editor + DAST terminal, vulnerability/chat right panel
- **Security Dashboard** — Analytics view: KPI cards, severity charts, OWASP coverage matrix, file heatmap, GitHub PR review history
- **Android App** — Mobile companion (apps/android)
- **MCP Server** — Model Context Protocol server for Claude integration

**Architecture:** Next.js 15 frontend → Spring Boot 4 backend → Python FastAPI AI engine (LangGraph + Claude API) → MCP Server (Node.js)

---

## Sources

- **Codebase:** `secureai-editor/` (mounted via File System Access API)
  - Frontend: `secureai-editor/apps/frontend/src/`
  - Design System doc: `secureai-editor/docs/09_DESIGN_SYSTEM.md`
  - UI/UX Revisions: `secureai-editor/docs/10_UI_UX_REVISIONS.md`
- **GitHub repo:** `ttogle918/secureai-editor`
- **No Figma link provided**

---

## CONTENT FUNDAMENTALS

**Language:** Korean (한국어) is the primary UI language — all labels, button text, and copy is in Korean. Technical terms (SAST, DAST, CRITICAL, HIGH, CWE-89, etc.) stay in English.

**Tone:** Technical, precise, authoritative. No fluff. Numbers and statuses are always shown exactly (not rounded unless explicitly labeled). The product speaks to engineers who value clarity over warmth.

**Casing:**
- Severity labels: ALL CAPS (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
- Pipeline badges: ALL CAPS (`SAST`, `DAST`, `PATCH`)
- Section titles: mixed case in Korean (e.g. `보안 점수 트렌드`)
- Monospace labels: lowercase paths and file names
- Button CTAs: Short, verb-first in Korean (`분석 시작`, `전체 프로젝트 분석`, `패치 적용`)

**Emoji:** ❌ Strictly forbidden in the UI. All icons must be SVG (lucide-react). Emoji used informally in docs/comments but never in production UI.

**Numbers:** Always exact. Security scores shown as integers (62, not "62.0"). Vulnerability counts always shown even if 0.

**Persona voice:** The AI chat agent introduces itself as "SecureAI 보안 에이전트" — professional, structured responses with numbered findings. No casual language.

---

## VISUAL FOUNDATIONS

### Color Philosophy
OLED-first dark mode. Near-black backgrounds with layered depth. A single warm orange accent (#f97316) cuts through the darkness — chosen for trust and urgency without the purple/pink AI clichés explicitly banned in the design system. Severity colors are semantic and glowing — red for critical exploits, amber/yellow for highs, green for safe.

### Backgrounds (5-layer depth system)
- `--bg-0` #080809 — outermost body, absolute darkest
- `--bg-1` #0d0d0f — sidebar, header
- `--bg-2` #111114 — cards, panels
- `--bg-3` #161619 — hover states, input backgrounds
- `--bg-4` #1c1c20 — code blocks, deepest inputs

### Accent
- Orange primary: `#f97316` (hover), `#ea580c` (resting/brand)
- Orange glow: `rgba(249,115,22,0.12)` background; `rgba(249,115,22,0.25)` stronger glow
- Focus ring: 2px solid `#ea580c`, offset 2px
- Primary button: #ea580c bg + `box-shadow: 0 3px 12px rgba(234,88,12,0.3)`

### Severity Colors (semantic, with glow)
- Critical: `#f04141` / dim `rgba(240,65,65,0.08)` — red
- High: `#f59e0b` / dim `rgba(245,158,11,0.08)` — amber
- Medium: `#eab308` — yellow
- Low: `#22c55e` / dim `rgba(34,197,94,0.08)` — green
- Info: `#569cd6` — blue

### Typography
- **Sans:** Space Grotesk (Google Fonts) — geometric, techy feel
- **Mono:** JetBrains Mono (Google Fonts) — all code, paths, timestamps, badges
- Base body: 14px / 1.6 lh / Space Grotesk
- Code: 13px / 1.7 lh / JetBrains Mono + ligatures enabled
- Smallest UI text: 9–10px (badges, metadata), always mono and uppercase
- No system fonts used in production

### Spacing
4px grid. Tailwind defaults: space-1=4px, space-2=8px, space-3=12px, space-4=16px, space-6=24px, space-8=32px.

### Borders & Dividers
- Subtle: `#1f1f24` (card borders)
- Default: `#2a2a30` (interactive borders)
- Accent: `#ea580c` (active tabs, focus)
- Cards use `border: 1px solid #1f1f24`, `border-radius: 8px`
- Vuln cards use colored left-border `border-left: 2px solid <severity-color>`
- Dividers: `rgba(255,255,255,0.06)` for section separators

### Shadows
- Primary button: `0 3px 12px rgba(234,88,12,0.3)`
- Sidebar analyze button: `0 3px 12px rgba(234,88,12,0.3)`
- Severity glow (exploit labels): `0 0 12px rgba(severity-color, 0.3)`
- No general card shadows — depth via background color contrast only

### Corner Radii
- Cards/panels: 8–10px
- Buttons: 6–8px
- Badges/pills: 3–4px
- Dots: 50% (fully round)

### Animations
- Hover color transitions: 150ms ease-out
- Panel open/close: 250ms cubic-bezier(0.4, 0, 0.2, 1) via Framer Motion
- Spinner: 0.85s linear infinite
- Skeleton shimmer: 1.5s infinite linear
- Glow pulse: 2s ease-in-out infinite
- `prefers-reduced-motion: reduce` → all durations collapse to 0.01ms

### Hover States
- Buttons: color shift (e.g. #ea580c → #f97316), no scale
- Cards: border lightens (#1f1f24 → #2a2a30)
- Sidebar items: bg-3 background (#161619)
- Ghost buttons: bg-3 background on hover
- Active button: scale(0.98) on press

### Scrollbars (custom, webkit + firefox)
- Width: 6px
- Track: #0d0d0f
- Thumb: #2a2a30, hover #404050, radius 3px

### Layout
- Fixed header: 48px
- Sidebar: 220–280px (resizable via drag handle)
- Right panel: ~300px (resizable)
- Terminal: ~180px (resizable)
- 4 responsive breakpoints: 375 / 768 / 1024 / 1440px
- At ≥1024px: 3-panel layout (sidebar + editor + right panel)
- At <768px: single column, bottom tab nav

### Imagery
No photography or illustrations. Data visualizations (AreaChart, BarChart) via Recharts, styled with severity colors on dark bg. No decorative gradients on backgrounds.

### Call Chain Timeline
Vertical timeline UI with colored dots per layer: Frontend=#378ADD, Controller=#7F77DD, Service=#1D9E75, Repository=#E24B4A, Config=#BA7517. Vulnerable node has red glow.

---

## ICONOGRAPHY

**Library:** `lucide-react` (already installed in frontend). Stroke-based, consistent 1.5px weight.

**Emoji:** Strictly forbidden in production UI. All icons must be SVG Lucide components.

**Common icons used:**
- Shield → SecureAI logo/brand icon
- Play / RefreshCw → analysis start/restart
- LayoutDashboard / Code2 → view toggle
- ShieldAlert → vulnerabilities tab
- MessageSquare → AI chat tab
- AlertTriangle → warnings
- CheckCircle2 / XCircle → success/fail states
- Github → GitHub integration
- File / Folder / FolderOpen → file tree
- PanelLeftClose / PanelLeftOpen → sidebar toggle
- ChevronRight / ChevronDown → expand/collapse
- Layers → call chain
- Zap → auto-fix / patch
- ExternalLink → jump to code
- FileJson → export

**No icon font.** No PNG icons. No emoji as icons. No unicode chars as icons.

---

## File Index

```
README.md                        — This file
SKILL.md                         — Agent skill definition
colors_and_type.css              — CSS custom properties (tokens)
assets/                          — No binary assets (no logo files found in codebase)
preview/                         — Design system card previews
  colors-bg.html                 — Background layer swatches
  colors-accent.html             — Brand accent + severity colors
  colors-text.html               — Text & border tokens
  type-sans.html                 — Space Grotesk specimens
  type-mono.html                 — JetBrains Mono specimens
  type-scale.html                — Full type scale
  spacing.html                   — Spacing tokens
  components-buttons.html        — Button variants
  components-badges.html         — Severity badges & dots
  components-cards.html          — Card + panel patterns
  components-inputs.html         — Input fields
  components-tabs.html           — Tab navigation pattern
  brand-pipeline.html            — Pipeline status badges
ui_kits/
  editor/
    index.html                   — Full editor app prototype
    AppHeader.jsx                — Header component
    AppSidebar.jsx               — File tree sidebar
    EditorPanel.jsx              — Code editor + DAST terminal
    RightPanel.jsx               — Vuln list + AI chat
    Dashboard.jsx                — Analytics dashboard
    Shared.jsx                   — Shared tokens/utilities
```
