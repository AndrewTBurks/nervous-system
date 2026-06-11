# Plan Lifecycle

Plan files under `.cns/plans/` are scratch working documents. The source of truth after resolution is the CNS graph: central nodes and module/package `index.md` files.

## Default lifecycle

1. Create plan for unresolved work.
2. Resolve design/implementation choices.
3. Shard decisions into durable CNS nodes.
4. Bubble changes upward.
5. Validate graph.
6. Delete the plan only after explicit same-session confirmation.

## Narrow persistence exception

During a multi-session design phase, plan files may remain temporarily while decisions are unresolved. Once the phase closes, propose deletion after confirming decisions are sharded.
