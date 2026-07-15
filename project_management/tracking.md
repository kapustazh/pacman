# Task Tracking

Project work was tracked through Jira Scrum and GitHub. Jira task IDs were used in
branch names to keep implementation work connected to the corresponding task.

## Workflow

```text
Jira task
    ↓
Assign task
    ↓
Create SCRUM-xx branch from develope
    ↓
Implement and test
    ↓
Push branch
    ↓
Open pull request to develope
    ↓
Review by the other team member
    ↓
Merge
    ↓
Move Jira task to Done
```

## Branch Strategy

- `main` — stable repository branch.
- `develope` — active integration branch.
- `SCRUM-xx-...` — branches linked to Jira tasks.

Development was performed on task branches rather than directly on `main`.
Branches were updated with the latest `develope` changes when required before
final integration.

## Examples of Tracked Work

| Jira task | Work | GitHub evidence |
|-----------|------|-----------------|
| `SCRUM-24` | GUI implementation | Game-state and menu integration |
| `SCRUM-25` | In-game HUD | HUD integration |
| `SCRUM-31` | Sprite parser | PR #1 |
| `SCRUM-32` | Rendering and game scaffold | PR #2 |
| `SCRUM-33` | Asset organization | PR #3 |
| `SCRUM-34` | Victory transition and animation | PR #6 |
| `SCRUM-35` | Backend/frontend integration | PR #8 |
| `SCRUM-38` | Project polishing | PR #13 |
| `SCRUM-39` | Smooth ghost movement | PR #14 |
| `SCRUM-42` | Wall rendering corrections | PR #15 |
| `SCRUM-43` | Code polishing | PR #16 |
| `SCRUM-44` | Configuration, highscore, and maze error handling | PR #17 |
| `SCRUM-45` | Duplicate JSON key validation | PR #18 |
| `SCRUM-28` | README documentation | PR #19 |
| `SCRUM-46` | Cheat control documentation | PR #20 / #21 |

## Progress Review

Jira was used to track task status and remaining work. GitHub branches, commits,
and pull requests provided implementation and review evidence.

Major bugs or missing requirements identified during development were created as
separate Jira tasks and completed through the same branch and pull request
workflow.

## Quality Checks

Static code quality was checked with:

```bash
make lint
```

Gameplay and frontend behavior were checked through manual playtesting before
integration.