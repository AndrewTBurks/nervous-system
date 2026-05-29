---
name: nervous-system
description: A persistent, living knowledge layer for software projects
---

# site-astro project notes

## Bootstrap recovery rule

When the CNS is absent and session_search for "site-astro" returns sparse results, browse recent sessions chronologically and scroll the most active one to find planning context before running bootstrap.

## Overdrive timeout rule

When Andrew uses `/overdrive` or assigns a design review task, the subagent timeout must be set to at least 10 minutes. Andrew expects overdrive-level critique — subagents that time out mid-critique waste the session.

## CRT is dead site-wide (May 2026 kill)

DisplayFrame.astro was stripped of all SVG filters (barrel blur, RGB stripes, feTurbulence noise). ImageFrame.astro no longer wraps in DisplayFrame. DisplayFrame is now a pass-through div. The CRT decision in .cns/design/index.md reflects this.

## feDisplacementMap is banned

Breaks GPU compositing on animated elements. Do not reintroduce.

## Image performance: box-shadow causes repaints

Use the `::after` pseudo-element pattern for GPU-composited shadows on card hovers:
```css
.card { transition: border-color 300ms ease, transform 300ms cubic-bezier(0.16, 1, 0.3, 1); }
.card::after { content: ''; position: absolute; inset: 0; box-shadow: 0 8px 32px rgba(0,0,0,0.4); opacity: 0; transition: opacity 300ms ease; pointer-events: none; z-index: -1; }
.card:hover::after { opacity: 1; }
```

## Date off-by-one

`toLocaleDateString` on `2018-01-01T00:00:00Z` renders as "Dec 31, 2017" in US timezones. Fix: parse from YYYY-MM-DD string directly in the Astro template, never from the Date object's UTC interpretation.

**Year grouping also uses local time (June 2026 fix).** `entry.date.getFullYear()` in the `byYear` grouping loop puts Jan 1 2018 entries into the 2017 bucket in US timezones. Fix: use `entry.date.getUTCFullYear()` for the year key in `byYear` grouping (index.astro line 131). This is a separate code path from date display formatting — both must be checked when fixing date-related bugs.

## Astro class prop forwarding

`class:list` from parent to child via `class={expr}` replaces, not merges. Workaround: use CSS custom property `--crt` on parent set to `1`; children read `var(--crt)`.

## Astro ClientRouter white flash

`ClientRouter` from `astro:transitions` is in `SiteLayout.astro` but the browser still flashes white between navigations. The browser renders its default white background before global.scss applies `--background` to `html`.

Fix: blocking inline `<script is:inline>` in `<head>` BEFORE `<ClientRouter />`:

```astro
<!-- Prevent white flash: set background before first paint -->
<script is:inline>
  document.documentElement.style.background = "#26241f";
</script>
<ClientRouter />
```

`is:inline` runs synchronously before any paint. See `references/astro-client-router-patterns.md`.

## Reading progress not re-initing on client navigation

`ReadingProgress.astro` called `initReadingProgress()` at top-level of `<script>`. That runs only on initial page load. With `ClientRouter`, module scripts do not re-run on subsequent navigations.

Fix: `document.addEventListener('astro:page-load', initReadingProgress)` instead of calling at top-level. Applies to any Astro component that initializes scroll listeners, intersection observers, or DOM-dependent state. See `references/astro-client-router-patterns.md`.

## Image dark screenshot visibility

Screenshots in dark mode blend into dark card backgrounds. Fix: `padding: 2px; background: #fff; border-radius: 4px;` on the screenshot container.

## HTML width/height on img overrides CSS aspect-ratio

Remove HTML width/height attributes from images when CSS aspect-ratio is set.

## CNS structure

Central nodes: .cns/index.md, .cns/architecture/index.md, .cns/design/index.md, .cns/product/index.md, .cns/research/index.md. Plan files live in .cns/plans/. Health gate at session close: run `bun run validate:slugs` then `python3 ~/.hermes/skills/nervous-system/scripts/validate.py .` and `graph.py . --check` — all must pass.

## Content storage

`src/data/` (not `src/content/`). 6-type taxonomy: essay, project, publication, note, update, milestone. blog coverImage is optional; no-image posts need clean full-width layout.

## Garden redesign (June 2026)

Homepage IS the garden feed. CSS columns with break-inside:avoid. Uniform cards. Updates/milestones typography-only. Year watermark: -webkit-text-stroke outline/hollow on section header, not overlaid on cards. 5-card hero grid. Tagline: "Building systems that help people make sense of data." Listing pages (/blog, /projects, /publications) deleted. Nav links removed.

## Year watermark invisible under cards

The `year-watermark` uses `position: absolute` with outline/hollow text. Cards with cover images paint over it (z-index stacking). Fix (TASK-029, revised May 2026): replace with `.year-rule` using `grid-column: 1/-1` `<hr>` + serif label below the line via `::before` + `content: attr(data-year)`. Label: `top: 0.75rem`, `font-size: 1.1rem`, `font-weight: 400`, `color: var(--text-primary)`. Not overlapping the line. Andrew rejected the overlapping label approach (`top: -0.6em`, small, bold, uppercase, opacity 0.5) as "really ugly" and "doesn't work at all right now."

## Hero row-3 height mismatch

`hero-bio` (grid-column: 1) and `hero-description` (grid-column: 2/4) both in row 3 have different natural heights and no baseline alignment. bio is serif body; description is monospace. They need a shared baseline strategy (align-items: baseline or explicit height locking).

## Side-tab border in project detail pages

The abstract callout in `src/pages/projects/[id].astro` uses `border-inline-start: 4px solid var(--primary)` — the canonical "AI slop" side-tab pattern. Replace with a different callout treatment: full-width top border, background tint, or icon.

## Project cover images showing static noise

Despite CRT kill, project cover images in the garden feed still render as visual noise in the browser. Likely causes: CSS filter on `.entry-image img`, or Astro dev server serving a cached old build. Verify in browser with `getComputedStyle(document.querySelector('.entry-image img')).filter`.

## Publications (June 2026)

`src/data/publications/` holds all academic publications. 14 entries added from bibtex (2017-2022). The "Interactive Exploration and Tracking of Ensemble Viscous Fingers" year confirmed as 2016 (SciVis Challenge), not 2019.

**Publication detail page (June 2026).** `[slug].astro` renders `venue` with `IconRow icon="ph ph-buildings"` and `doi` as a link icon pointing to `https://doi.org/{doi}`. Add both fields to the frontmatter of each publication entry. `venue` and `doi` fields already exist in publication frontmatter; they were not being rendered before this fix.

## xref overlap rule

When adding publication entries, check for slug/title overlap with existing projects in `src/data/projects/`. Overlaps found so far:
- `forbes2017-din` ↔ `dynamic-influence-networks` (same work — DIN paper and project)
- `burks2020-vissnippets` ↔ `vis-snippets` (same work — VisSnippets paper and project)
- `burks-interactive-viscousfingers` ↔ `finger-finder` (SciVis Challenge 2016 — the "Interactive Exploration and Tracking of Ensemble Viscous Fingers" paper and the FingerFinder project)
- `politowicz2022-alveolus` ↔ `alveolus-analysis` (same work — Alveolus paper and project)

**Rule**: add `xrefs: ["slug"]` to BOTH the publication AND project frontmatters. Always bidirectional. Use the publication filename slug on the project side, and the project slug on the publication side. `finger-finder` xrefs to `burks-interactive-viscousfingers` as the SciVis Challenge source paper.

## Year rule label (May 2026 — current design)

`.year-rule` uses `::before` with `content: attr(data-year)` to label the section header. The label sits below the horizontal rule, not overlapping it:

```css
.year-rule {
  grid-column: 1 / -1;
  border-top: 1px solid var(--border-subtle);
  position: relative;
}
.year-rule::before {
  content: attr(data-year);
  position: absolute;
  top: 0.75rem;       /* below the line, not overlapping */
  left: 0;
  font-family: var(--font-serif);
  font-size: 1.1rem;   /* larger than the rejected 0.75rem */
  font-weight: 400;   /* normal weight, not bold */
  color: var(--text-primary);
  letter-spacing: 0.02em;
  background: var(--bg-primary);
  padding-right: 0.75em;
}
```

The rejected design: label overlapping the line with `top: -0.6em`, `font-size: 0.75rem`, `font-weight: 600`, `text-transform: uppercase`, `opacity: 0.5`. Andrew called it "really ugly" and "doesn't work at all right now." The current design has label below the line, larger serif, full contrast.

## h1 margin-bottom in [slug].astro detail pages

All h1 instances in `src/pages/[slug].astro` use inline `style="margin-bottom: 0.5em;"` to space the title from the date/meta row below. Prior value `0px` was too tight — Andrew flagged h1 being "really too close to the date below." The same `0.5em` applies across all three h1 variants (generic/essay, publication, project).

## Slug validation (regression prevention)

`scripts/validate-slugs.py` checks for duplicate slugs across all `src/data/` subdirectories. Run with `bun run validate:slugs` or `python3 scripts/validate-slugs.py .`. Exit 0 = unique; exit 1 = duplicates found (prints conflicting files). Always run as part of the CNS health gate at session close and after adding new content files.

## Nav home link excess space fix

"the home link in the nav at the top has a ton of space below it for no reason." Fix: add `padding-bottom: 0; margin-bottom: 0;` to `nav` in `src/components/Header.astro`. Article element in `global.scss` has `padding-top: 5rem` desktop / `1rem` mobile; the gap was compounding nav's default bottom margin behavior with article's top padding. Symptom: visible extra vertical breathing room between nav bottom edge and the "Andrew Burks" h1 in the article. Fix applied 2026-05-28.

## Grid masonry: align-self: start (June 2026)

Entries in the garden feed are placed by JS masonry (`initMasonry` in index.astro) into CSS Grid columns. Without `align-self: start`, grid items default to `stretch` and each entry fills the full column height, creating visual gaps when content is shorter than adjacent entries.

Fix: add `align-self: start` to `.year-feed[data-masonry] .entry`. The JS also sets `gridColumn` per item but does not set alignment — this CSS rule fills that gap.

## Milestone/update date: bottom-left, full date (June 2026)

Update and milestone entries use `.entry--text` (typography-only, no card). The date was previously inline with the title (right-aligned in `.entry-title-row`). Andrew wanted it at the bottom-left of the entry with the full year shown.

Fix: move `<time>` outside `.entry-title-row` to after `.entry-desc`. Container `.entry--text` uses `flex-direction: column` so date stacks below title/desc. Date gets `margin-top: auto` to push it to the bottom. formatDate called with `year: "numeric", month: "short", day: "numeric"`.

## Publications missing abstracts (June 2026 — TASK-052)

All 12 entries in `src/data/publications/*.mdx` have `description` (venue metadata) but no `abstract` field. Publications affected: bharadwaj2021-securing, burks-interactive-viscousfingers, burks2020-vissnippets, Castor2017-MC2, Forbes2017-DIN, Kirilov2017-MC1, Kirshenbaum2021-Traces, Leigh2019-usagepatterns, Luciani2018-detailsfirst, Mahida2017-MC3, Marai2018-precision, Politowicz2022-Alveolus. Task: research each paper, add the full abstract to frontmatter. Two overlaps with projects: `burks-interactive-viscousfingers` ↔ `finger-finder` and `politowicz2022-alveolus` ↔ `alveolus-analysis` — use those project files for context.

## Completed (June 2026)

- **Flat /[slug] routing (TASK-028 + TASK-035 merged)**: `src/pages/[slug].astro` single catch-all for all 6 collections. `index.astro` generates `/{entry.slug}` hrefs. Blog collection removed. 49 pages built (was 11).
- **Year watermark (TASK-029)**: Replaced `outline-text` giant watermark with `grid-column: 1/-1` `<hr>` + small uppercase serif label via `::before` + `content: attr(data-year)`.
- **Milestone label/title separation (TASK-032)**: Wrapped `.entry-title` in `.entry-title-row` (block-level, width: 100%) inside flex parent. Forces title to new line regardless of flex behavior.
- **Publications deduplication (TASK-036)**: Kept `politowicz2022-alveolus` (BMC Pulmonary Medicine, best venue). Removed `belvitch2021-alveolus` and `dong2021-alveolus` (same work, secondary venues). 12 unique publications.
- **Blog collection removed (TASK-045)**: `src/data/blog/` deleted (empty). `blog` from `content.config.ts` removed. All content in essays/notes/projects/publications/updates/milestones.
- **Hero typesetting (TASK-026)**: `align-items: baseline` on hero row 3, year label redesign, nav bottom margin fix.
- **Full typesetting pass (TASK-033)**: `$impeccable critique` score 8.0/10. Card entry-type `display: block`, border-color easing, milestone/update date inline.
- **Detail page h1 margin (May 2026)**: `margin-bottom: 0px` → `0.5em` on all `[slug].astro` h1 instances.

## Astro glob() vs shell ls

When checking for content files in `src/data/` subdirectories, `ls` in the terminal may return empty even when files exist. Astro's content loader uses `glob()` patterns internally — the files ARE present but the shell ls context doesn't reflect Astro's file discovery. Always use `find` or explicit glob patterns in Astro projects: `find src/data/publications -name "*.mdx" | wc -l`.

All TASK-### items from the original Garden redesign plan are now complete (TASK-026, TASK-027, TASK-030, TASK-031, TASK-033, TASK-037, TASK-038, TASK-041, TASK-042). See `.cns/intent.md` for the full record.