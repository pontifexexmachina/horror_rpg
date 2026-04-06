# AGENTS.md

This repository is for creating a horror tabletop RPG and turning that writing into a readable book.

Right now, the writing matters more than the packaging. Agents should optimize first for helping develop the game text itself, then for making that text publishable in the current Quarto workflow.

## Mission

An agent working in this repo can contribute in two main ways:

1. Help write and refine the RPG.
2. Help package, structure, and present that writing as a book-like artifact such as a PDF or website.

Quarto is the current stack because it is already in use and good enough to move quickly. Treat it as the present toolchain, not a permanent product decision.

## Current Project Shape

- Quarto book project configured in [`_quarto.yml`](C:\projects\horror_rpg\_quarto.yml)
- Main manuscript files:
  - [`index.qmd`](C:\projects\horror_rpg\index.qmd)
  - [`game_rules.qmd`](C:\projects\horror_rpg\game_rules.qmd)
  - [`appendix_n.qmd`](C:\projects\horror_rpg\appendix_n.qmd)
- Rendered outputs currently land in [`docs/`](C:\projects\horror_rpg\docs)
- Supporting assets include [`character_sheet.html`](C:\projects\horror_rpg\character_sheet.html) and [`cover.png`](C:\projects\horror_rpg\cover.png)

## Priority Order

When choosing what to optimize for, prefer this order:

1. Clarify, strengthen, or extend the game's written content.
2. Improve structure, consistency, and readability across the manuscript.
3. Improve book presentation and export quality in the existing Quarto setup.
4. Explore alternative packaging only when it unblocks the writing or solves a concrete publishing problem.

## Agent Roles

### 1. RPG Writing Agent

This is the default role and should usually be treated as the primary one.

Use this role for:

- drafting rules text
- revising tone, setting, or voice
- tightening explanations and procedures
- designing mechanics, play loops, or character options
- checking consistency between sections
- identifying missing content, unclear assumptions, or rule gaps
- shaping appendices, examples, tables, and reference material

Guidance:

- Favor clear, playable prose over clever wording.
- Preserve the project's horror tone while keeping rules understandable.
- When inventing mechanics, explain them in a way that can survive later layout changes.
- If a section is incomplete, move it toward usable draft quality rather than leaving only notes.

### 2. Book Production Agent

Use this role to help the manuscript behave like a book or deliverable.

Use this role for:

- Quarto structure and configuration
- chapter organization and navigation
- PDF and HTML output improvements
- front matter, appendix, references, and metadata
- styling and presentation changes that improve legibility
- making assets work cleanly in current exports

Guidance:

- Do not let formatting work crowd out writing progress.
- Prefer simple, maintainable Quarto changes over elaborate publishing infrastructure.
- Treat PDF and website output as current delivery formats, not fixed product commitments.
- If proposing a larger platform shift, frame it as a future option and keep the repo usable in Quarto now.

## Working Style

- Assume the author values momentum and workable drafts over premature system design.
- Prefer editing existing manuscript files unless there is a clear reason to add new files.
- Keep structural changes legible so the manuscript remains easy to navigate by hand.
- When making major content changes, preserve author intent and tone as much as possible.
- If a request is ambiguous, bias toward helping the writing itself.

## Quarto Expectations

- Keep the book renderable through the existing Quarto project.
- Update [`_quarto.yml`](C:\projects\horror_rpg\_quarto.yml) only when the change clearly supports the manuscript or output quality.
- Treat [`docs/`](C:\projects\horror_rpg\docs) as generated output unless the task specifically requires touching rendered files.
- Avoid introducing a new build stack unless explicitly asked.

## Good Contributions

Strong contributions in this repo usually look like:

- turning rough notes into draft-ready rules text
- identifying contradictions between chapters
- improving chapter order or section headings
- adding examples that make mechanics easier to run at the table
- improving PDF or HTML output in a minimal, reversible way
- making the project easier to read, revise, and publish without overengineering it

## Avoid

- treating packaging decisions as more important than the manuscript
- introducing large tooling changes without a concrete need
- rewriting the author's voice into generic game-text boilerplate
- making generated output edits in `docs/` when the source `.qmd` files should be updated instead
- assuming Quarto is the forever solution

## Default Heuristic

If there is a choice between:

- improving the RPG text, or
- improving the machinery around the text

choose the RPG text first unless the machinery is actively blocking progress.
