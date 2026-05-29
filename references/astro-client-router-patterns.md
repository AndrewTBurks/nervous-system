# Astro ClientRouter SPA Patterns

Astro's `ClientRouter` (`astro:transitions`) enables client-side page transitions. These patterns govern components that initialize DOM-dependent state.

## White flash on navigation

The browser renders its default white background before global CSS applies `--background` to `html`. Even with `ClientRouter` in place, there is a flash between navigations.

**Fix**: blocking inline `<script is:inline>` in `<head>` BEFORE `<ClientRouter />`:

```astro
<head>
  <!-- Prevent white flash: set background before first paint -->
  <script is:inline>
    document.documentElement.style.background = "#26241f";
  </script>
  <ClientRouter />
  ...
</head>
```

`is:inline` runs synchronously before any paint. This is the general fix for Astro sites using `ClientRouter` with a dark background set via CSS custom property.

## Component scripts not re-running on client navigation

Astro component `<script>` tags are module scripts — they run once on initial page load. When `ClientRouter` does a client-side navigation, the page content updates but the component scripts do not re-execute.

**Symptom**: works on first page load, fails on subsequent navigations. Applies to: scroll listeners, intersection observers, reading progress bars, sticky headers, animation initializations.

**Fix**: listen for `astro:page-load` instead of calling init at top-level:

```astro
<script>
  function initMyComponent() {
    // set up scroll listeners, DOM references, etc.
  }
  // Re-run after every client-side navigation (ClientRouter)
  document.addEventListener('astro:page-load', initMyComponent);
</script>
```

`astro:page-load` fires after every navigation, including the initial page load. Using it as the only event listener (not an additional `DOMContentLoaded`) handles both cases correctly.

## Pattern applies to

- Reading progress indicators
- Scroll-linked animations
- Intersection observer reveals
- Sticky/fixed header state
- Back-to-top buttons
- Any component that reads `document.body` or `window.scrollY`
