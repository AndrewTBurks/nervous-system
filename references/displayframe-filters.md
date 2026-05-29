---
name: displayframe-filters
description: DisplayFrame filter chain reference
---

# DisplayFrame filter chain

**DEPRECATED — May 2026: DisplayFrame is now a pass-through div. All CRT/SVG filter code has been removed.**

## Historical (pre-May 2026)

DisplayFrame.astro previously applied a barrel blur + RGB stripe CRT effect via SVG filters:

- `#barrel` filter: `feGaussianBlur` + `feColorMatrix` + `feComposite` for glow/blur edge effect
- `#crt-noise` filter: `feTurbulence` for static noise overlay

The CRT effect was intentionally applied to the profile photo (hero) and slug cover images (single image, one-time cost). It was **killed on grids** because `feDisplacementMap` was not used but the barrel blur still caused compositor issues on animated elements. feDisplacementMap was specifically banned for breaking GPU compositing on animated transforms.

## Current state

DisplayFrame.astro is:
```astro
<div class="frame"><slot /></div>
<style>.frame { position: relative; display: inline-flex; overflow: hidden; }</style>
```

No SVG filters. No blur. No noise. ImageFrame.astro is a plain `<img>` tag.
