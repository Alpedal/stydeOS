:root {
  /* === BASE BACKGROUND === */
  --bg-base: #0f172a;
  --bg-surface: #1e293b;
  --bg-elevated: #263549;
  --bg-hover: #334155;
  --bg-active: #3b4f63;
  /* === ACCENT / BRAND === */
  --accent: #38bdf8;
  --accent-rgb: 56, 189, 248;
  --accent-hover: #7dd3fc;
  --accent-active: #bae6fd;
  --accent-muted: #0c4a6e;
  --accent-soft: #0b304b;
  --accent-text: #0f172a;
  --accent-text-hover: #020617;
  /* === TEXT === */
  --text-primary: #f1f5f9;
  --text-primary-rgb: 241, 245, 249;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --text-inverse: #0f172a;
  --text-link: #38bdf8;
  --text-link-hover: #7dd3fc;
  --text-link-visited: #a78bfa;
  /* === BORDERS === */
  --border: #334155;
  --border-hover: #475569;
  --border-active: #64748b;
  --border-accent: #38bdf8;
  --border-radius-sm: 4px;
  --border-radius-md: 6px;
  --border-radius-lg: 10px;
  --border-radius-xl: 14px;
  --border-radius-full: 9999px;
  /* === SHADOWS === */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.5);
  --shadow-lg: 0 8px 32px rgba(0,0,0,0.6);
  --shadow-xl: 0 16px 48px rgba(0,0,0,0.7);
  --shadow-glow: 0 0 20px rgba(56,189,248,0.15);
  /* === SPACING / RHYTHM SCALE === */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
  /* === TYPOGRAPHY === */
  --font-family: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  --font-size-xs: 11px;
  --font-size-sm: 13px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 30px;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
  --letter-spacing-tight: -0.01em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.04em;
  /* === EASING / ANIMATION === */
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 350ms;
  --duration-slower: 500ms;
  /* === SCROLLBAR === */
  --scrollbar-thumb: #334155;
  --scrollbar-track: transparent;
  --scrollbar-width: 6px;
  /* === FOCUS RING === */
  --focus-ring: 0 0 0 2px #0f172a, 0 0 0 4px #38bdf8;
  /* === OVERLAY / BACKDROP === */
  --overlay: rgba(0,0,0,0.6);
  --backdrop-blur: blur(8px);
  /* === COMPONENT: CARD === */
  --card-bg: #1e293b;
  --card-border: #334155;
  --card-border-hover: #475569;
  --card-radius: 10px;
  --card-padding: 20px;
  --card-shadow: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
  --card-shadow-hover: 0 8px 24px rgba(0,0,0,0.5);
  /* === COMPONENT: BUTTON === */
  --btn-bg: #38bdf8;
  --btn-bg-hover: #7dd3fc;
  --btn-bg-active: #bae6fd;
  --btn-text: #0f172a;
  --btn-text-hover: #020617;
  --btn-radius: 6px;
  --btn-padding-x: 16px;
  --btn-padding-y: 8px;
  --btn-font-weight: 600;
  --btn-outline-bg: transparent;
  --btn-outline-border: #38bdf8;
  --btn-outline-text: #38bdf8;
  --btn-outline-bg-hover: rgba(56,189,248,0.08);
  --btn-ghost-bg-hover: rgba(255,255,255,0.06);
  /* === COMPONENT: INPUT === */
  --input-bg: #1e293b;
  --input-bg-focus: #1e293b;
  --input-border: #334155;
  --input-border-hover: #475569;
  --input-border-focus: #38bdf8;
  --input-text: #f1f5f9;
  --input-text-placeholder: #64748b;
  --input-radius: 6px;
  --input-padding-x: 12px;
  --input-padding-y: 8px;
  --input-font-size: 14px;
  --input-label-color: #94a3b8;
  --input-error-border: #f87171;
  --input-error-shadow: 0 0 0 2px rgba(248,113,113,0.2);
  /* === STATES === */
  --state-error: #f87171;
  --state-error-bg: rgba(248,113,113,0.08);
  --state-error-border: #7f1d1d;
  --state-warning: #fbbf24;
  --state-warning-bg: rgba(251,191,36,0.08);
  --state-warning-border: #78350f;
  --state-success: #34d399;
  --state-success-bg: rgba(52,211,153,0.08);
  --state-success-border: #064e3b;
  --state-info: #38bdf8;
  --state-info-bg: rgba(56,189,248,0.08);
  --state-info-border: #0c4a6e;
  /* === CHART / DATA VIZ === */
  --chart-1: #38bdf8;
  --chart-2: #34d399;
  --chart-3: #fbbf24;
  --chart-4: #f87171;
  --chart-5: #a78bfa;
  --chart-6: #fb923c;
  --chart-7: #e879f9;
  --chart-8: #6ee7b7;
  --chart-grid: #1e293b;
  --chart-axis: #475569;
  --chart-tooltip-bg: #1e293b;
  --chart-tooltip-border: #334155;
}