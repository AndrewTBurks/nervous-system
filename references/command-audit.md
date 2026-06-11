# /nervous-system audit

## Purpose

Check whether CNS claims, decisions, and graph structure still match the codebase.

## Preflight

1. Run common preflight.
2. Rebuild graph if stale.
3. Identify audit scope: whole project, central node, package, module, or file.
4. Read relevant CNS nodes and linked code.

## Procedure

Classify each audited decision:

- Implemented: code fully reflects the decision.
- Partial real gap: missing behavior is a contract break.
- Partial wording drift: code is right; CNS wording is stale.
- Unimplemented: no code reflects the decision.
- Cancelled-but-shipped: a cancelled decision still ships.

For public APIs, add a design-check step before fix tasks: mock or inspect real consumer workflows so fixes match the consumer shape, not merely the old decision text.

## Output

Use a tally table and then write consolidated intent tasks if the user asks to plan fixes. Group by coherent change, not by decision ID.
