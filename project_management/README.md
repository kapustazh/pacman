# Project Management

This directory documents the management of the Pac-Man project in line with
Chapter VIII of the subject. The project was managed by a two-person team using
a lightweight Scrum workflow, Jira tickets, Git feature branches, pull requests,
and short integration cycles.

The documents below provide evidence of planning, progress tracking, technical
choices, risk handling, team organization, and acceptance testing.

## Methodology

- **Approach**: lightweight Scrum / iterative development for a two-person team.
- **Planning**: work was divided into Jira issues using `SCRUM-xx` identifiers.
- **Cadence**: short implementation cycles; features were integrated as soon as
  they reached a runnable and reviewable state.
- **Branching**: Jira-linked feature branches were created from `develope`.
- **Review flow**: feature branch → pull request → review/integration → merge into
  `develope`; direct feature work on `main` was avoided.
- **Quality gate**: `make lint` runs flake8 and mypy. Manual playtesting was used
  for gameplay, UI, configuration, and game-flow validation.
- **Collaboration**: difficult integration points were discussed jointly, while
  parallel features were implemented by their primary owner.

## Documents

| Document | Purpose |
|----------|---------|
| [team.md](team.md) | Team organization, ownership, and decision-making |
| [timeline.md](timeline.md) | Development phases and progress reconstructed from Git history |
| [gantt.md](gantt.md) | Visual Gantt chart of the project timeline |
| [tracking.md](tracking.md) | Jira, branch, pull-request, and progress tracking workflow |
| [risks.md](risks.md) | Risk register and mitigation actions |
| [decisions.md](decisions.md) | Key technical decisions and their rationale |
| [acceptance-tests.md](acceptance-tests.md) | Feature acceptance test plan and bug/fix evidence |
