# Technical Decisions

This document summarizes the main implementation choices made where the project
requirements defined the expected behavior but did not prescribe a specific
technical solution.

---

## D1. State-Based Graphical Architecture

**Context**: The project requires several graphical flows, including the main menu,
gameplay, instructions, highscores, pause, game-over, and victory screens.

**Choice**: Use separate game states managed through the core scene architecture.

**Why**: The subject defines the required game flow but does not prescribe the
internal UI architecture. Separate states keep input, update, and rendering
responsibilities isolated.

---

## D2. Preserve Backend Logic During Frontend Integration

**Context**: Core gameplay logic was developed before the graphical frontend was
fully integrated.

**Choice**: Preserve working backend behavior and adapt it to the graphical layer
instead of rewriting the gameplay systems.

**Why**: This reduced regression risk and retained already tested gameplay behavior.
Adapter layers were used where backend and frontend structures differed.

---

## D3. Isolate Maze Package Integration with `MazeAdaptor`

**Context**: The assigned maze package must be used, but its wall representation
differs from the internal map representation used by the game.

**Choice**: Use `MazeAdaptor` to convert package output into the internal
`TileType` grid.

**Why**: The subject requires use of the assigned package but does not prescribe how
its output must be integrated. The adapter keeps package-specific conversion and
error handling separate from gameplay logic.

---

## D4. Junction-Based Ghost Chase Movement

**Context**: Ghosts must autonomously chase the player. Early BFS-based chase
movement made them too efficient and less similar to classic Pac-Man behavior.

**Choice**: Use local target-based movement at junctions with deterministic
tie-breaking.

**Why**: The subject defines the required chase behavior but does not prescribe a
pathfinding algorithm. Local junction decisions keep the implementation
understandable and allow the four ghosts to use different target strategies.

---

## D5. Standard JSON Parser with Preprocessing and Duplicate Detection

**Context**: The configuration must support `#` comment lines and safely handle
invalid configuration data. Standard JSON parsing also silently accepts duplicate
keys by keeping the last value.

**Choice**: Remove supported comment lines before parsing with Python's standard
`json` module and use a custom `object_pairs_hook` to reject duplicate keys.

**Why**: This satisfies the required configuration behavior without adding another
parser dependency and prevents ambiguous duplicate values from being silently
accepted.

---

## D6. JSON-Based Highscore Storage

**Context**: Highscores must persist between game sessions, but the storage format
is not prescribed.

**Choice**: Store highscores in a JSON file managed by `HighscoreManager`.

**Why**: The leaderboard contains a small amount of structured data. JSON is simple
to persist, inspect, validate, sort, and safely recover when the file is missing or
malformed.