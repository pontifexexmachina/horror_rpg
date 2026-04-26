# ADR 0001: Keep Rules Manuscript Free Of Design Commentary

Date: 2026-04-26

## Status

Accepted

## Context

The first agent-driven v0.2 pass of `game_rules.qmd` mixed playable rules with design commentary, simulator references, open questions, and notes about future drafts.

That made the manuscript less useful as a table-facing document. A rules chapter should tell readers how to play the game. It should not expose the project workflow, simulator status, prior draft history, or next-step planning.

## Decision

`game_rules.qmd` should contain only player- and GM-facing rules text.

Design commentary belongs in generated notes, ADRs, plans, reports, or drift logs.

Allowed in `game_rules.qmd`:

- rules procedures
- play examples
- table guidance
- definitions
- equipment, actions, conditions, and character options
- GM-facing rulings if they are meant to be used during play

Not allowed in `game_rules.qmd`:

- simulator status
- benchmark interpretation
- notes about previous drafts
- internal design rationale
- next-step planning
- unresolved author checklists
- phrases such as "future drafts should" or "current simulator"

## Consequences

Open design questions still need to be tracked, but they should move to `notes/agent_generated/plans/`, `notes/agent_generated/adrs/`, or the existing simulator drift log.

When a rule is provisional, the manuscript should either present the provisional rule cleanly or omit it until it is ready. The uncertainty should be recorded outside the rules text.
