# site-astro: Taxonomy vs Folder Structure

## The mismatch (found 2026-05-28)

**Product spec** (`.cns/product/index.md`): 6 content types mapped to folders:
- `essay` → `src/data/essays/`
- `project` → `src/data/projects/`
- `publication` → `src/data/publications/`
- `note` → `src/data/notes/`
- `update` → `src/data/updates/`
- `milestone` → `src/data/milestones/`

**Actual state**:
```
src/data/
  blog/          → collection registered, but folder is being deprecated
  essays/        → folder exists, NO collection registered
  milestones/    → collection registered ✓
  projects/      → collection registered ✓
  publications/  → folder exists, NO collection registered
  updates/       → collection registered ✓
```

**Also**: `notes` collection registered in `src/content.config.ts` but `src/data/notes/` did not exist.

## How to detect silent collection exclusions

1. `ls src/data/` — see all folders
2. Check `src/content.config.ts` — list of `defineCollection` calls
3. Check `index.astro` (or whichever page builds the feed) — what `getCollection()` calls are made
4. Compare: folder vs collection vs queried — any gap = content not showing up

**Detection query**:
```bash
# Folders that exist but have no collection
for dir in src/data/*/; do
  name=$(basename "$dir")
  if ! grep -q "getCollection.*$name\|base:.*$name" src/content.config.ts; then
    echo "MISSING COLLECTION: $name"
  fi
done
```

## Fix applied (TASK-043/044/045)

1. Create `src/data/essays/` collection in `content.config.ts`
2. Create `src/data/publications/` collection in `content.config.ts`
3. Create `src/data/notes/` folder
4. Split `src/data/blog/` into `essays/` (long, 200+ lines) and `notes/` (short, <100 lines)
5. Remove `blog` collection
6. Update `index.astro` to query `essays` and `notes` instead of `blog`

## Key lesson

Astro folder-based collections silently skip folders that are not registered in `config.ts`. No error, no warning — the content just does not appear. Always verify the full chain: folder → collection → getCollection → rendered.