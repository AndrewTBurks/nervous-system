# Peripheral Node Rules

Peripheral nodes are `index.md` files near code. Create them only for meaningful conceptual boundaries that need durable context.

## Creation

Create a PNS node when a module/package/subsystem will receive decisions or recurring context. Do not create nodes for every leaf helper file.

## Line count

Keep nodes under roughly 350 lines. If a node grows too large, split along a real conceptual boundary and add child links.

## Flat source exception

Sometimes source remains flat while a sibling directory holds `index.md`. This can trigger an orphan warning. Treat it as informational when the node clearly describes nearby flat source and moving files would be an out-of-scope refactor.
