# site-astro: Landing Page Bio Text Workflow

## The Problem

Personal portfolios often have two or more distinct professional contexts (e.g., industry work + academic research). The homepage bio must represent both accurately without generic filler. "Research focuses on..." or "Working at the intersection of..." language is a known anti-pattern — it's abstract, doesn't distinguish one researcher from another, and reads as template text.

## The Workflow

1. **Find the research statement in the codebase.** Search the thesis project (or equivalent primary research repo) for `provenance`, `co-authorship`, `thread`, or look at the architecture doc and coding scheme. These files contain precise, authentic language about the research direction.

2. **Extract the authentic research framing.** From `threadweaver-architecture.html` and `coding-scheme.md`, the research direction is: AI co-authorship produces more branching than unassisted analysis; large display enables cross-branch reasoning; provenance-tracked spatial arrangement functions as a communication channel. This is precise enough to write from directly.

3. **For proprietary work (Epsilon, etc.), ask the user.** The user is the only source for proprietary work details. Do not attempt to write "building analytics systems" from first principles — the user's description of DiME (Digital Marketing Explorer), Ada (NL interface), and their role (product architecture, UI/UX, natural language interface) is what makes the description real. Q&A was: DiME = visual analytics platform synthesizing proprietary identity data + client datasets; users = internal analysts, client teams, direct client access; distinctive = custom visualizations, interactive view connections, proprietary identity network.

4. **Write two clean sentences, no em dashes.** Bio line 1: role + affiliation. Bio sub: what you're building and why it matters, in the user's own words. Order: industry work first, then academic context (user preference: career at Epsilon before PhD research).

5. **Verify with `npm run build` + grep.** Always confirm the updated text appears in `dist/index.html` before declaring done.

## Key Andrew Preferences

- Epsilon comes before UIC PhD in the bio line order
- "Principal Research Scientist & Director of Decision Sciences at Epsilon" is the correct title
- No em dashes in bio text
- Abstract research language from thesis docs; proprietary work from user Q&A

## Verified Patterns

- `grep "Building DiME" dist/index.html` confirms the build picked up the updated sub text
- Removing `src/pages/index.md` was required to fix stale content being served from the MDX version — the Astro version's updates weren't visible until the MDX collision was resolved