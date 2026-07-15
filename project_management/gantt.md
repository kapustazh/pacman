# Gantt Chart

The chart summarizes the actual development phases visible in the repository
history. GitHub renders Mermaid diagrams directly.

```mermaid
gantt
    title Pac-Man — Project Timeline (May 26 – Jul 14, 2026)
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Bootstrap
    Repository & config foundation   :done, p1a, 2026-05-26, 3d
    First playable prototype         :done, p1b, 2026-05-28, 2d

    section Core Gameplay
    Maze integration                 :done, p2a, 2026-05-28, 3d
    Levels, ghosts & scoring         :done, p2b, 2026-05-30, 6d
    Ghost AI iterations              :done, p2c, 2026-06-01, 28d

    section GUI
    Assets & render scaffolding      :done, p3a, 2026-05-29, 19d
    Menu, states & HUD               :done, p3b, 2026-06-21, 8d

    section Integration
    Core and GUI migration           :done, p4a, 2026-06-29, 2d
    Gameplay hardening               :done, p4b, 2026-07-02, 7d

    section Release
    Polish & config robustness       :done, p5a, 2026-07-09, 5d
    Packaging & README               :done, p5b, 2026-07-13, 2d
    Project management docs          :done, p5c, 2026-07-14, 1d
```

## Notes

- Workstreams overlap because the two team members developed core gameplay and
  graphical systems in parallel.
- The long ghost-AI span reflects several design iterations rather than one blocked
  task.
- The Jun 29–30 integration phase was the main convergence point between the two
  workstreams.
- Final robustness tasks were tracked using Jira ticket branches such as
  `SCRUM-44`, `SCRUM-45`, and `SCRUM-46`.
