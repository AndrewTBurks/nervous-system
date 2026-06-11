# /nervous-system explore

## Purpose

Read or update central project knowledge: `.cns/index.md`, `.cns/architecture/index.md`, `.cns/design/index.md`, `.cns/product/index.md`, and `.cns/research/index.md`.

## Preflight

1. Run common preflight.
2. Read the relevant central node(s).
3. Preserve `human_notes` exactly.
4. If writing, read the target immediately before patching.

## Procedure

1. Identify the topic: architecture, design, product, research, or project overview.
2. Read the current CNS node and adjacent links.
3. Answer from CNS + code if the user is asking a question.
4. If the user gives new direction, record it as provenance and synthesize it into the agent-authored body.
5. Bubble meaningful changes upward.
6. Run health.

## Verification

- Target node read back after write.
- Parent consistency checked when changes bubble.
- `validate.py` and `graph.py --check` pass.
