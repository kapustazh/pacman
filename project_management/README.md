# Project Management

This directory documents the management of the Pac-Man project in line with
Chapter VIII of the subject. The project was managed by a two-person team using
a lightweight Scrum workflow, Jira tasks, Git feature branches, pull requests,
and short integration cycles.

The documents provide evidence of project planning, progress tracking, technical
decisions, risk handling, team organization, and acceptance testing.

## Methodology

- **Approach**: Lightweight Scrum and iterative development for a two-person team.
- **Planning**: Work was divided into Jira tasks using `SCRUM-xx` identifiers.
- **Tracking**: Jira was used to track tasks and progress during development.
- **Branching**: Jira-linked feature branches were created from `develope`.
- **Review flow**: Feature branch → pull request → review by the other team member
  → merge into `develope`.
- **Integration**: Frontend integration was mainly handled by `mnestere` based on
  the backend developed by `wehan`. Major backend changes were discussed and
  handled by `wehan` through separate Jira tasks and pull requests.
- **Quality checks**: `make lint` was used for flake8 and mypy. Manual playtesting
  was used to validate gameplay and graphical behavior.

## Documents

| Document | Purpose |
|----------|---------|
| [team.md](team.md) | Team organization, ownership, and collaboration workflow |
| [timeline.md](timeline.md) | Development phases, Jira timeline, and planned vs actual progress |
| [tracking.md](tracking.md) | Jira, branch, pull-request, and progress tracking workflow |
| [decisions.md](decisions.md) | Main technical implementation choices and their rationale |
| [risks.md](risks.md) | Main project risks and mitigation actions |
| [acceptance-tests.md](acceptance-tests.md) | Feature-level acceptance tests and verification status |