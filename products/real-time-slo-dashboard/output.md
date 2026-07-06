Real Time Slo Dashboard
Domain: dashboard Version: 2
Purpose
Service Level Objective tracking dashboard. Real-time SLO burn-rate alerts: error budget gauge (green/yellow/red), remaining budget %, projected exhaustion date. Latency sparklines for p50/p95/p99 with SLO threshold overlays. Error rate heatmap (time x severity grid). Dependency health tree showing service dependencies with cascading failure visualization. Incident timeline integration: when SLO is breached, show related incidents and resolution timeline. Production-quality data layer with deterministic mocks, cached snapshots, and exportable artifacts.
Persona
SRE dashboard specialist and SLO tracking expert. Expert in error budget theory, burn-rate alerting, multi-percentile latency visualization, and building operations dashboards that surface reliability data clearly.
Skills
  Budget: error budget gauge with burn rate (green=healthy, yellow=warning, red=critical)
  Latency: multi-percentile sparklines (p50/p95/p99) with SLO threshold overlay lines
  Heatmap: time x severity error rate heatmap with drill-down to individual errors
  Dependency: hierarchical service dependency tree with health status and cascading failure highlighting
  SLO: per-service SLO definition with window (24h/7d/30d), target %, and current attainment
  Incidents: timeline of related incidents overlaid on SLO burn-down with resolution markers
  Output: interactive HTML SLO dashboard panel with budget gauge, latency charts, heatmap, and dependency tree
Data Layer
  Deterministic mocks: All visualization data (gauge, heatmap, burndown, latency sparklines) must use seeded pseudo-random generators (e.g., mulberry32 or splitmix32 with a fixed seed) instead of Math.random(). This guarantees identical output across renders and machines for the same seed value.
  Seed convention: Accept a query-string parameter ?seed=<number> or default to 42. Display the active seed in the dashboard footer for reproducibility.
  Fixture JSON: At minimum, latency sparklines and SLO gauge must consume from a fixture JSON file (stubbed endpoint) rather than generating data inline. Fixture files live under /fixtures/ with versioned filenames (e.g., /fixtures/metrics.v1.json).
  Artifact export: The active dashboard dataset must be downloadable as a JSON artifact via a dedicated Export button. The export includes all rendered metric series, timestamps, seed value, and dashboard version.
  Data caching: Generated mock data must be cached once per session (or once at build time) and served identically on all subsequent renders. Implement a singleton cache keyed by seed + version; cache is invalidated only on seed change or dashboard version bump.
Performance and Caching
  Session-scoped cache: Mock data generation runs exactly once per seed per session. Subsequent renders reuse the cached snapshot. Cache lives in a module-level Map or WeakRef structure (no localStorage dependency).
  Build-time snapshot: Optionally pre-generate a snapshot at build time and bundle it as a static JSON asset, eliminating all runtime generation overhead.
  Lazy hydration: Dashboard panels that are not visible (hidden behind tabs or below the fold) defer data hydration until first render.
  Render budget: No single render pass exceeds 16ms (60fps) on a mid-range device. If data transformation exceeds this threshold, move it to a Web Worker.
  Throttle resize handlers: ResizeObserver callbacks are debounced at 100ms. Chart redraws are batched via requestAnimationFrame.
  Export artifact: The downloadable JSON file is the canonical representation of the dashboard state at that moment. The Export button appears in the dashboard toolbar and triggers a browser download with filename slo-dashboard-snapshot-{seed}-{timestamp}.json.
Design Tokens
  CSS custom properties defined in a single :root block at the top of the stylesheet. No hard-coded color, spacing, or radius values anywhere else.
  Colors:
    --color-bg: #0f172a (dark navy)
    --color-surface: #1e293b (card background)
    --color-border: #334155
    --color-text-primary: #f1f5f9
    --color-text-secondary: #94a3b8
    --color-accent: #3b82f6 (blue)
    --color-success: #22c55e (green)
    --color-warning: #eab308 (yellow)
    --color-danger: #ef4444 (red)
    --color-info: #8b5cf6 (purple)
  Spacing:
    --space-xs: 4px
    --space-sm: 8px
    --space-md: 16px
    --space-lg: 24px
    --space-xl: 32px
  Radii:
    --radius-sm: 4px
    --radius-md: 8px
    --radius-lg: 12px
    --radius-full: 9999px
  Typography:
    --font-family: 'Inter', system-ui, sans-serif
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace
    --font-size-xs: 10px
    --font-size-sm: 12px
    --font-size-md: 14px
    --font-size-lg: 18px
    --font-size-xl: 24px
API Integration Layer
  Stubbed endpoints: At minimum, the latency sparklines panel and SLO gauge panel must consume data from a fixture JSON file served via a stubbed endpoint (/api/v1/metrics/latency, /api/v1/slo/gauge) rather than generating data inline. The stub responds with the contents of /fixtures/metrics.v1.json.
  Service layer: All data access must go through a service abstraction (e.g., MetricsService, SloService) that can transparently switch between fixture stubs and real API endpoints without changing panel code. Service methods return Promises.
  Error handling: Services must handle HTTP 500, 429, and network failures gracefully — show a cached-data fallback or an in-place error state (not a blank page or infinite spinner).
  Polling: The dashboard polls the stubbed endpoints every 30 seconds. If a real endpoint someday replaces the stub, the polling interval becomes configurable via the SLO window (24h endpoints poll less frequently than 7d/30d).
  Headers: Stub endpoint responses include a X-Data-Source: fixture header and a X-Seed: {seed} header so the dashboard can verify it is consuming the correct deterministic dataset.
Implementation
  Generate a single self-contained HTML file that renders all panels within a CSS-grid dashboard layout using D3.js (v7) loaded from CDN. The file includes the design-token :root block, the cache layer, service abstraction, seeded PRNG, fixture integration, export button, and all six visualization panels.
  Dashboard layout: a 3-column grid on wide screens, collapsing to 2-column on tablet and single-column on mobile. Header row spans full width with title, active seed display, and Export button.
  Every panel has a small loading state (skeleton shimmer) and an error state (retry button with message) in addition to the data state.
  All animations use CSS transitions or requestAnimationFrame — no setInterval for visual updates.
  Accessibility: panels are keyboard-navigable with aria-labels. Color is never the sole differentiator (patterns or labels accompany severity colors).
Output
  interactive HTML SLO dashboard panel with budget gauge, latency charts, heatmap, and dependency tree