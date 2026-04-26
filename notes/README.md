This folder is for notes, artifacts, and things that are not meant to be published as part of the manuscript but are still worth keeping.

Root `notes/` is for author-maintained notes plus lightweight guidance files for repository collaborators.

Agents should only edit these root notes files:
- `README.md`
- `AGENTS.md`

Agent-authored notes, planning documents, simulator design artifacts, and research summaries should live under `notes/agent_generated/`.

Suggested structure:
- `notes/agent_generated/adrs/` for durable project decisions and manuscript policy
- `notes/agent_generated/design/` for agent-authored design and planning notes
- `notes/agent_generated/plans/` for active task lists, open design calls, and production plans
- `notes/agent_generated/research/` for agent-authored research summaries and reading maps

Current agent-generated design notes worth revisiting:

- `agent_generated/design/book_line_plan.md` for the multi-book publishing direction
- `agent_generated/design/simulator_design.md` for the combat-lab architecture
- `agent_generated/design/session_simulation_goals.md` for session attrition and contribution targets
- `agent_generated/design/fictional_resource_model.md` for fiction-first resource design
- `agent_generated/design/spatial_rules_architecture.md` for areas, connections, and optional grid support
- `agent_generated/design/spatial_simulator_implementation_prep.md` for the first area-based simulator migration
- `agent_generated/design/simulator_rules_inventory_pass.md` for the inventory-aware simulator direction
- `agent_generated/design/simulator_canon_drift_log.md` for simulator-vs-manuscript divergences and author checklist items
- `agent_generated/design/combat_and_chase_separation.md` for the decision to split stand-up combat from flee/chase simulation
- `agent_generated/design/agent_driven_workflow.md` for the new author-as-creative-director, agents-as-production-leads workflow
- `agent_generated/design/v0_2_first_pass_report.md` for the first agent-driven manuscript pass and benchmark snapshot
- `agent_generated/adrs/0001-clean-rules-manuscript.md` for the policy that rules files should not include internal design commentary
- `agent_generated/plans/v0_2_open_design_calls.md` for current v0.2 design questions outside the manuscript
