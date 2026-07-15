# Risk Register

The table records the main technical and project risks identified during development
and the actions taken to reduce or resolve them.

| # | Risk | Impact | Likelihood | Mitigation | Status |
|---|------|--------|------------|------------|--------|
| R1 | **Backend/frontend integration and regression** — backend gameplay and the graphical frontend used different structures, and parallel changes could break existing integration | High | High | Frontend integration was handled mainly by `mnestere`; small integration changes were adapted directly, while major backend issues were assigned to `wehan` through Jira-linked branches and reviewed pull requests | Mitigated |
| R2 | **External maze package issues** — the assigned package interface and performance were outside team control | High | Medium | Kept `MazeAdaptor` as an isolation layer, used the assigned package without modification, and added clean error handling and fallback behavior | Mitigated |
| R3 | **Large-maze generation delay** — some generated mazes caused long loading or freezing behavior | High | Medium | Adjusted entry and exit handling to avoid unnecessary expensive generation work and improved loading behavior | Closed |
| R4 | **Configuration errors** — malformed values, wrong types, missing keys, or duplicate JSON keys could silently cause incorrect game behavior | High | High | Added defaults and type validation, ignored unknown keys, used safe fallback behavior, and rejected duplicate keys with `object_pairs_hook` | Closed |
| R5 | **Ghost AI becoming too complex** — pathfinding behavior could make ghosts feel too intelligent and unlike classic Pac-Man | Medium | High | Replaced BFS chase behavior with junction-based local greedy movement, deterministic tie-breaking, chase/scatter modes, and separate respawn behavior | Closed |
| R6 | **Highscore file errors** — invalid or unwritable highscore data could break the end-game flow | Medium | Medium | Validated loaded entries, rejected invalid data, kept only the top 10 scores, sanitized player names, and handled file errors cleanly | Closed |
| R7 | **Late discovery of subject-compliance gaps** — configuration, instructions, packaging, or documentation requirements could be overlooked | High | Medium | Rechecked the subject, created focused Jira tasks for identified gaps, reviewed the README and packaging, and added dedicated project management documentation | Mitigated |

## Risk Process

- Risks were identified during implementation, frontend integration, and subject review.
- Small integration issues were handled directly during frontend integration.
- Major backend issues were converted into focused Jira tasks and assigned to `wehan`.
- Fixes were kept traceable through Jira-linked branches, commits, and GitHub pull requests.
- Closed risks have corresponding implementation or fix history.
- Remaining integration and project-level risks are reduced through pull request review, linting, configuration tests, and manual playtesting.