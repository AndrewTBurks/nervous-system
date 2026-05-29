# API Integration Debugging Reference

Quick diagnostic checklist when an LLM provider integration fails in the orchestrator.

---

## Diagnostic Sequence (use this order)

### Step 1: Identify the provider from the key format

**Never assume which provider a key belongs to.** Key format hints:

| Prefix | Provider | Endpoint | Notes |
|--------|----------|----------|-------|
| `sk-cp-` | MiniMax Anthropic-compatible API | `api.minimax.io/anthropic/v1` | The `sk-cp-` format is accepted at MiniMax's Anthropic-compatible endpoint |
| `sk-ant-` | Anthropic (legacy) | `api.anthropic.com` | Older Anthropic keys |
| `sk-proj-` | OpenAI project key | `api.openai.com` | OpenAI project-scoped keys |
| `eyJ` | MiniMax native (JWT) | `api.minimax.chat` | MiniMax native keys are JWT tokens, not `sk-` prefixed |

### Step 2: Verify the API key is valid — curl first

Always confirm with a direct curl before touching code:

```bash
# MiniMax Anthropic-compatible endpoint
curl -s "https://api.minimax.io/anthropic/v1/messages" \
  -H "Authorization: Bearer $ANTHROPIC_API_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Anthropic-version: 2023-06-01" \
  -d '{"model": "MiniMax-M2.7", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}'
```

**Error code taxonomy — MiniMax Anthropic-compatible endpoint (`api.minimax.io/anthropic/v1`):**
| HTTP code | `error.message` | Meaning | Fix |
|-----------|-----------------|---------|-----|
| 401 | `login fail: Please carry the API secret key... (1004)` | Key not recognized by MiniMax | Key is not a valid MiniMax key |
| 401 | `invalid api key (2049)` | Key format recognized but key invalid | Wrong key or key expired |
| 404 | `Page not found` | Wrong endpoint URL | Use `https://api.minimax.io/anthropic/v1/messages` |
| 200 | success | Auth OK | Move to model name verification |

**Error code taxonomy — Anthropic (`api.anthropic.com`):**
| HTTP code | `error.type` | Meaning | Fix |
|-----------|-------------|---------|-----|
| 401 | `authentication_error` | Invalid bearer token | Check key is correct |
| 401 | `invalid x-api-key` | Wrong header used | Use `Authorization: Bearer`, not `x-api-key` |

### Step 3: Check the model name

MiniMax Anthropic-compatible model:
- `MiniMax-M2.7` — current supported model

### Step 4: Verify .env is loaded at runtime

In Bun (which auto-loads `.env`), verify with:
```bash
node -e "console.log('KEY_SET:', !!process.env.ANTHROPIC_API_TOKEN)"
```

If the key contains quotes in `.env` (e.g., `KEY="value"`), the quotes become part of the value — strip them in code:
```ts
const token = process.env.KEY?.replace(/^"|"$/g, '');
```

### Step 5: SDK usage — MiniMax Anthropic-compatible API

**For `@ai-sdk/anthropic` with MiniMax's Anthropic-compatible endpoint:**
```ts
import { createAnthropic } from "@ai-sdk/anthropic";

const anthropic = createAnthropic({
  baseURL: "https://api.minimax.io/anthropic/v1",  // MiniMax's Anthropic-compatible endpoint
  apiKey: process.env.ANTHROPIC_API_TOKEN,
});

const { object } = await generateObject({
  model: anthropic("MiniMax-M2.7"),
  system: "...",
  prompt: "...",
  schema: mySchema,
});
```

Note: `@ai-sdk/anthropic`'s `createAnthropic()` accepts `baseURL` — it does NOT hardcode `api.anthropic.com` (that was a pre-1.0 behavior). Test with a direct curl first to confirm the endpoint works before integrating with the SDK.

**For `@ai-sdk/openai` with custom base URL (OpenAI-compatible):**
```ts
import { createOpenAI } from "@ai-sdk/openai";

const provider = createOpenAI({
  baseURL: "https://<provider-url>/v1",  // must end in /v1
  apiKey: process.env.API_KEY,
});
```

---

## Common Failure Patterns

| Failure | Root cause | Fix |
|---------|-----------|-----|
| `404 Page not found` from MiniMax | Wrong endpoint URL | Use `https://api.minimax.io/anthropic/v1/messages` (Messages API, not chat completions) |
| `login fail (1004)` from MiniMax | Key not recognized as MiniMax key | Key is wrong format or wrong provider — `sk-cp-` keys work at MiniMax's Anthropic-compatible endpoint |
| `invalid api key (2049)` from MiniMax | Key format right but key invalid | Key expired or wrong key |
| `authentication_error` / `invalid x-api-key` from Anthropic | Wrong header or wrong key | Use `Authorization: Bearer` header |
| Orchestrator returns 404 in client UI | API call failed, error broadcast to WS client | Check server logs for the actual error |
| Key works in curl but not in code | `.env` not loaded, or quotes included in value | Verify `process.env.KEY` at runtime |
| `generateObject is not a function` | Wrong SDK import | Use `import { generateObject } from "ai"` (Vercel AI SDK) |

---

## Key Lessons from This Session

**Lesson 1: `sk-cp-` keys work at MiniMax's Anthropic-compatible endpoint.**
The key in `.env` had the `sk-cp-` prefix (Anthropic format). MiniMax accepts this key format at `https://api.minimax.io/anthropic/v1/messages`.

**Lesson 2: Two distinct 401 errors from MiniMax mean different things.**
- `login fail (1004)` = MiniMax doesn't recognize the key format at all (not a MiniMax key)
- `invalid api key (2049)` = key format recognized but key is invalid/expired

**Lesson 3: Test at the right layer.**
Use `curl` to test the raw HTTP API before touching SDK code. If curl fails with auth error, the SDK will fail too — don't debug the SDK until the raw API works.

**Lesson 4: When `generateObject` fails with auth error in `@ai-sdk/anthropic`, the error message from the SDK may differ from curl.**
Always add try/catch and log the full error:
```ts
try {
  const { object } = await generateObject({ model: anthropic(MODEL), ... });
} catch (err) {
  console.error("generateObject failed:", err?.message, err?.cause);
}
```

---

## Related CNS Decisions

- `DEC-SRV-012`: MiniMax via Anthropic-compatible endpoint (`https://api.minimax.io/anthropic/v1`)
- `DEC-ARCH-007`: MiniMax Anthropic-compatible API in orchestrator
