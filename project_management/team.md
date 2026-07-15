# Team Organization

The Pac-Man project was developed by a two-person team with separate backend and
frontend responsibilities.

## Responsibilities

| Team member | Main responsibility | Areas |
|-------------|---------------------|-------|
| `wehan` | Backend | Configuration, maze integration, game logic, player mechanics, ghost AI, levels, scoring, and highscores |
| `mnestere` | Frontend and integration | pygame integration, scenes and states, sprites, rendering, HUD, menus, fullscreen support, and packaging |

The frontend was built by `mnestere` on top of the backend gameplay logic developed
by `wehan`. Backend/frontend integration was therefore handled mainly by `mnestere`.

## Decisions and Issue Handling

Small integration changes were handled directly during frontend integration and
reviewed through GitHub pull requests.

When a larger backend change or bug fix was required, the issue was discussed and
assigned to `wehan`. A separate Jira task and related GitHub branch were created
when necessary. The backend change was implemented by `wehan` and submitted through
a pull request for review by `mnestere`.

Larger frontend bugs or tasks followed the same workflow under `mnestere`'s
ownership.

Changes were reviewed before being merged into `develope`.