# Timeline

The project was developed iteratively from May to July 2026. Development was
divided into backend implementation, frontend development, integration, and final
validation.

## Development Phases

### Phase 1 — Backend Prototype

The first playable version focused on configuration, maze integration, player
movement, scoring, ghost logic, levels, and highscores.

### Phase 2 — Parallel Backend and Frontend Development

`wehan` continued developing the backend gameplay systems while `mnestere` built
the pygame frontend, including sprites, rendering, menus, states, and the HUD.

### Phase 3 — Frontend Integration

`mnestere` integrated the frontend with the existing backend gameplay logic.
Small integration changes were handled directly. Major backend changes were
discussed and assigned to `wehan` through separate Jira tasks and GitHub branches.

### Phase 4 — Testing and Hardening

Gameplay, ghost behavior, maze generation, configuration handling, highscores,
and frontend behavior were tested and refined. Larger issues were tracked through
Jira-linked branches and reviewed through GitHub pull requests.

### Phase 5 — Final Validation and Documentation

The team reviewed the project against the subject requirements, completed final
configuration and documentation fixes, prepared the public game package, and
added project management documentation.

## Planned vs Actual Progress

| Area | Initial plan | Actual development |
|------|--------------|-------------------|
| Backend | Build core gameplay first | Developed first and refined throughout the project |
| Frontend | Develop graphical interface in parallel | Built on top of the backend and became the main integration layer |
| Integration | Connect backend and frontend | Required continuous adaptation and pull request review |
| Testing | Validate features during development | Bugs and missing requirements were tracked and fixed iteratively |
| Documentation | Maintain project documentation | README evolved during development; project management documentation was finalized near completion |

For the visual schedule, see [gantt.md](gantt.md). Task tracking and the Jira/GitHub
workflow are described in [tracking.md](tracking.md).