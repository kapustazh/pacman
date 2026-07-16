*This project has been created as part of the 42 curriculum by mnestere, wehan.*

# PAC-MAN

## Description

This project recreates Pac-Man with a pygame arcade UI, procedural maze generation, original Pac-Man inspired ghost AI, persistent highscores, and modular software architecture.

Play it on [itch.io](https://kapustazh.itch.io/pac-man).

### Features

| Feature | Implementation |
|---------|----------------|
| Maze generation | Uses the assigned A-Maze-ing package through `MazeAdaptor` |
| Levels | 10+ procedural levels |
| Level 1 seed | Fixed seed `42` for reproducibility |
| Later levels | Random seed generated when entering each new level |
| Level retry | Reuses the current level seed, so retries reload the same maze |
| Player movement | WASD movement through corridors only |
| Ghost movement | Autonomous grid-based movement |
| Ghost AI | Junction-based local greedy movement with individual chase targets |
| Frightened mode | Activated by Super Pacgums |
| Respawn | Eaten ghosts temporarily disappear and return after a delay |
| Highscores | Persistent JSON leaderboard |
| Config validation | Missing and invalid values fall back to safe defaults |
| Cheat mode | Invincibility, freeze ghosts, speed adjust, add life, skip level |
| Rendering | Pygame-ce arcade UI with sprite sheets, HUD, and menus |
| Packaging | PyInstaller build for itch.io (`make package-itch`) |
| Static analysis | `flake8` and `mypy` through Makefile |


---

## Instructions

Run all commands from the project root (where the `Makefile` lives).

### Installation

```bash
make install
```

### Run

Development (requires `config.json`):

```bash
make run
```

Packaged build (built-in defaults, no config file):

```bash
make build-itch
make run-release
```

Or directly:

```bash
python3 pac-man.py config.json   # development: config is required
./dist/pac-man/pac-man           # packaged: defaults when no config is passed
```

### Packaging (itch.io)

```bash
make package-itch    # → dist/pac-man-linux.zip
```

Upload the zip to itch.io and set the Linux executable to `pac-man/pac-man`.
In-package instructions ship as `README.TXT` next to the `pac-man` binary.

Live page: [https://kapustazh.itch.io/pac-man](https://kapustazh.itch.io/pac-man)

### Other commands

```bash
make help            # show all available targets
make debug
make lint
make lint-strict
make clean
make re
make build-itch     # build without zipping
make package-itch    # archived build
```

### Controls

| Key | Action |
|-----|--------|
| W A S D / Arrows | Move |
| Esc | Pause |
| F11 | Toggle fullscreen |
| I | Invincibility (cheat) |
| F | Freeze ghosts (cheat) |
| + / - | Speed up / slow down Pac-Man (cheat) |
| N | Skip level (cheat) |
| L | Add life (cheat) |

Menus use Up/Down or W/S to navigate and Enter/Space to confirm.


---

## Configuration

The game uses a JSON configuration file with comment lines beginning with `#`.

| Key | Type | Default | Description |
|------|------|---------|-------------|
| `highscore_filename` | string | `"highscores.json"` | Highscore storage file |
| `lives` | int | `3` | Initial player lives |
| `pacgum` | int | `42` | Number of Pacgums generated |
| `points_per_pacgum` | int | `10` | Score for each Pacgum |
| `points_per_super_pacgum` | int | `50` | Score for each Super Pacgum |
| `points_per_ghost` | int | `200` | Score for eating a ghost |
| `seed` | int | `42` | Seed used for Level 1 |
| `level_max_time` | int | `90` | Maximum seconds allowed per level |
| `levels` | list | `10 levels` | Maze size configuration |

- Development run without a config argument → print usage and exit.
- Packaged build without a config argument → load default configuration.
- Missing or invalid config file when a path is given → load default configuration with warnings.
- Unknown keys → ignored.
- Invalid values → replaced with default values.
- No Python traceback is shown during gameplay.

---

## Highscore

Highscores are stored in JSON format.
The leaderboard is loaded when the game starts and automatically saved after the game ends.
- Top 10 leaderboard
- Automatic descending sort
- Safe loading and saving
- Invalid entries ignored


| Rule | Value |
|--------|--------|
| Maximum Entries | 10 |
| Maximum Name Length | 10 |
| Allowed Characters | Letters, numbers, spaces |
| Score Type | Non-negative integer |

---

## Maze Generation

The project uses the assigned A-Maze-ing package to generate procedural mazes.
MazeGenerator produces a wall-code representation where each cell stores wall information using bitmasks.

### Wall Encoding

| Direction | Value |
|------------|----------|
| NORTH | 1 |
| EAST | 2 |
| SOUTH | 4 |
| WEST | 8 |

### Conversion Pipeline

```text
MazeGenerator
      │
      ▼
MazeAdaptor
      │
      ▼
TileType Grid
      │
      ▼
LevelBuilder
      │
      ▼
GameWorld
```

`MazeAdaptor` is responsible for

- importing the assigned package
- generating a maze
- converting the wall-code representation into the internal grid
- handling generator failures gracefully

---

## Rendering

The game is rendered with **pygame-ce** in a 1920×1080 window (F11 toggles fullscreen).

### Visual pipeline

```text
GameEngine (main loop)
      │
      ▼
Scene stack (MenuState, PlayState, PauseState, …)
      │
      ▼
GameWorld.draw()  →  maze background + sprite layers
      │
      ▼
HudOverlay.draw() →  score, lives, timer, phase text
```

Each frame, `GameEngine` polls input, updates the active scene, clears the screen, and draws the scene stack from the bottom up. Pause and other overlays sit above gameplay without restarting the world.

### Assets and sprites

| Component | Role |
|-----------|------|
| `Assets` | Loads sprite sheets from `assets/` and slices 8×8 cells into 16×16 surfaces |
| `AnimatedSprite` | Pac-Man, ghosts, pellets, fruit, and death animation |
| `WallTilePicker` | Picks wall tile art from neighbour masks (`maze_parts.png`) |
| `ArcadeTextRenderer` | Renders HUD and menu text from the arcade glyph sheet |

Sprite sheets live under `assets/sprites/` and `assets/new_assets/`. `src/core/paths.py` resolves asset paths in both development and PyInstaller builds.

### Layout

`WorldRenderConfig` converts grid cells to pixel coordinates. The maze is centered on screen at 16 px per tile. Actors move on a discrete grid, but sprites are visually interpolated between steps for smoother motion.

### On-screen UI

| Screen | Module |
|--------|--------|
| Main menu | `MenuState` |
| High scores | `HighscoresState` |
| Instructions | `InstructionsState` |
| Gameplay + HUD | `PlayState` + `HudOverlay` |
| Pause overlay | `PauseState` |
| Game over / victory | `GameOverState` |

The in-game HUD shows score, high score, remaining lives, level timer, and phase messages (READY, LEVEL CLEAR, GAME OVER).

---

## Implementation

### Gameplay loop

The game runs in real time at up to 120 FPS. Each frame:

```text
Input
  ↓
Scene update (dt)
  ↓
Player / ghost movement
  ↓
Collisions, pellets, fruit, timers
  ↓
Draw maze + sprites + HUD
```

Grid logic still advances in discrete steps, but movement is time-based and visually smoothed between cells.

The player wins a level after collecting all Pacgums.
Lives and score carry across levels.

## Ghost AI

Ghost behaviour is managed by `GameWorld` and `GameSession`, while each ghost is responsible for selecting its own target and deciding its next movement.

The implementation adopts the original Pac-Man movement philosophy while introducing several project-specific adaptations to satisfy the subject requirements, particularly for frightened behaviour and respawning.

```text

                        Ghost Behaviour Priority

                              Ghost Update
                                   │
                                   ▼
                       Is the ghost active?
                        ┌─────────┴─────────┐
                        │                   │
                       No                  Yes
                        │                   │
              Waiting for Respawn    Is ghost frightened?
                                          │
                               ┌──────────┴──────────┐
                               │                     │
                              Yes                   No
                               │                     │
                      Frightened Behaviour     Global Behaviour
                                                    │
                                         ┌──────────┴──────────┐
                                         │                     │
                                     Scatter               Chase
                                         │                     │
                                         └──────────┬──────────┘
                                                    ▼
                                           Target Selection
                                                    ▼
                                    Junction-Based Local Greedy
                                                    ▼
                                              Move One Tile
```

**Figure 1.** Decision hierarchy of the ghost AI.
Individual ghost states (e.g., frightened and respawning) take priority over the global game behaviour. Chase and Scatter share the same movement algorithm but differ in their target selection strategy.


Ghost behaviour consists of two independent layers.

### Global Behaviour

The global behaviour is controlled by `GameWorld` and affects every active ghost simultaneously.

| Mode | Description |
|------|-------------|
| Chase | Ghosts pursue the player using individual targeting strategies. |
| Scatter | Ghosts temporarily stop chasing the player and return toward their assigned home corner. |

### Individual State

Each ghost also maintains its own individual state.

| State | Description |
|--------|-------------|
| Active | The ghost participates in Chase or Scatter mode. |
| Frightened | Triggered after a Super Pacgum is eaten. The ghost attempts to escape from the player. |
| Respawning | The ghost is temporarily inactive after being eaten and returns after a respawn delay. |

Individual states always have higher priority than the global behaviour.

---

### Chase Mode

Each ghost uses its own target selection strategy.

| Ghost | Personality | Chase Behaviour |
|-------|-------------|-----------------|
| **Blinky** | Aggressive | Directly follows the player. |
| **Pinky** | Ambusher | Tries to intercept the player by aiming ahead of their movement. |
| **Inky** | Unpredictable | Predicts the player's movement but adds randomness to make its behaviour less predictable. |
| **Clyde** | Shy | Chases the player from a distance but retreats to its corner when the player gets too close. |

The chase behaviour is divided into two stages:
1. **Target selection**, where each ghost calculates a different destination according to its personality.
2. **Movement selection**, where every ghost uses the same junction-based local greedy algorithm to move one tile toward its current target.

Instead of computing a complete shortest path every step, ghosts:
1. Continue moving straight through corridors whenever possible.
2. Make decisions only at junctions.
3. Ignore the immediate reverse direction unless no alternative exists.
4. Compare the squared Euclidean distance from each candidate tile to the current target.
5. Choose the direction producing the smallest distance.
6. Resolve equal distances using the original Pac-Man priority:

```
Up → Left → Down → Right
```

This produces smoother and less predictable movement than continuously recomputing a shortest path while remaining computationally lightweight.

---

### Scatter Mode

Ghosts periodically switch between Chase and Scatter mode.

During Scatter mode, each ghost temporarily stops targeting the player and instead moves toward its assigned home corner (which also serves as its spawn position in this implementation).

This periodically reduces the pressure on the player and recreates the alternating offensive and defensive behaviour found in the original Pac-Man.

---

### Frightened Mode

Eating a Super Pacgum makes every active ghost edible.

Unlike the original arcade game, frightened ghosts do not move completely randomly.

Instead, frightened ghosts actively attempt to increase their distance from the player instead of moving completely randomly.

This behaviour was intentionally selected because the project specification explicitly requires edible ghosts to "run away from the player", whereas the original arcade implementation uses purely random movement.

The frightened movement algorithm:

1. Estimates the shortest path between the player and the ghost using Breadth-First Search (BFS).
2. Avoids moving toward the player's approach direction whenever possible.
3. Prevents immediate backtracking unless no alternative exists.
4. Randomly selects from the remaining safe directions.

---

### Respawn

When an edible ghost is captured:

1. The player receives the ghost score bonus.
2. The ghost becomes inactive.
3. A respawn timer begins.
4. After the timer expires, the ghost returns to its original spawn position.
5. The ghost resumes normal behaviour.

This satisfies the project requirement that ghosts respawn after a short delay.

---

### Pathfinding

Different movement algorithms are intentionally used for different gameplay situations.

| Situation | Algorithm |
|-----------|-----------|
| Chase | Junction-based local greedy movement |
| Scatter | Junction-based local greedy movement |
| Frightened | BFS-assisted escape |
| Respawn | Timer-based respawn |

Normal ghost movement does not use Breadth-First Search.

Instead, Chase and Scatter follow an original Pac-Man inspired junction-based local greedy algorithm.

Breadth-First Search is only used during frightened mode to estimate a safe escape direction.

---

## Software Architecture

```text
                    GameEngine
                        │
                 SceneManager
                        │
        ┌───────────────┼───────────────┐
        │               │               │
   MenuState       PlayState      PauseState
                        │
              ┌─────────┴─────────┐
              │                   │
         GameSession           GameWorld
              │                   │
         lives, timer        Player, Ghosts,
         phase flow          pellets, fruit
```

**Figure 2.** High-level architecture of the game modules.

### General Software Architecture

```text
pac-man.py                     -> Program entry point
pacman.spec                    -> PyInstaller packaging spec
src/
├── config/
│   └── config.py              -> Load and validate JSON configuration
│
├── core/
│   ├── engine.py              -> Pygame main loop
│   ├── scene_manager.py       -> Scene stack (push/pop/change)
│   ├── context.py             -> Shared screen, assets, config, scores
│   ├── state.py               -> Base class for all scenes
│   └── paths.py               -> Asset and save paths (dev vs packaged)
│
├── states/
│   ├── menu_state.py          -> Main menu
│   ├── play_state.py          -> Active gameplay scene
│   ├── pause_state.py         -> Pause overlay
│   ├── highscores_state.py    -> Leaderboard screen
│   ├── instructions_state.py  -> Controls screen
│   ├── game_over_state.py     -> End-of-run name entry
│   └── text.py                -> Arcade glyph text renderer
│
├── game/
│   ├── game_world.py          -> World state, collisions, drawing
│   ├── game_session.py        -> Lives, timer, phase flow
│   ├── level_builder.py       -> Populate maze with actors and pellets
│   ├── render_config.py       -> Grid-to-pixel layout
│   ├── ghost_logic.py         -> Ghost movement and frightened mode
│   └── wall_tile_picker.py    -> Maze wall autotiling
│
├── maze/
│   ├── maze_adapter.py        -> Interface to the A-Maze-ing package
│   └── map_data.py            -> Internal TileType grid representation
│
├── entities/
│   ├── player_entity.py       -> Pac-Man sprite and movement
│   ├── ghost_entity.py        -> Ghost sprite and state
│   └── ghost.py               -> Ghost AI and target selection
│
├── sprites/
│   └── assets.py              -> Sprite sheet loading
│
├── rendering/
│   ├── hud_overlay.py         -> In-game HUD
│   └── widgets.py             -> Shared UI drawing helpers
│
└── managers/
    └── highscore_manager.py   -> Load, validate and save highscores
```

### Module Responsibilities

| Module | Responsibility |
|----------|----------------|
| `config` | Loads and validates the JSON configuration file. |
| `core` | Engine loop, scene stack, shared context, and path resolution. |
| `states` | Menu, gameplay, pause, and end-of-run screens. |
| `game` | World simulation, session flow, rendering layout, and ghost logic. |
| `maze` | Generates the maze and converts it into the internal TileType grid. |
| `entities` | Player and ghost behaviour on the grid. |
| `sprites` / `rendering` | Asset loading and on-screen drawing. |
| `managers` | Handles persistent highscore storage. |

### Data Flow

```text
config.json (required in dev; optional in packaged build)
      │
      ▼
load_config() / default_config()
      │
      ▼
GameEngine → MenuState → PlayState
      │
      ▼
MazeAdaptor → LevelBuilder → GameWorld
      │
      ▼
GameSession (lives, timer, phases)
      │
      ▼
HudOverlay + GameWorld.draw()
```

### Class Relationships

- `GameEngine` owns the pygame loop and delegates to `SceneManager`.
- `PlayState` owns a `GameWorld` (simulation) and a `GameSession` (lives, timer, phases).
- `MazeAdaptor` converts the external maze into the internal `TileType` grid.
- `LevelBuilder` populates the maze with the player, ghosts, and collectibles.
- `Ghost` queries the world for valid movement and performs junction-based local greedy movement. Breadth-First Search (BFS) is only used during frightened mode to estimate a safe escape direction.
- `HudOverlay` and scene states read world/session data and render without modifying gameplay logic.

---

## Project Management

- The project was managed through GitHub branches, pull requests, issue tracking, and team discussions.
- Jira is used for planning, task tracking, meeting notes, technical decisions, and project documentation.

---

## Resources

- Pacman Guide (Chinese): https://www.bilibili.com/video/BV1Jr4y1C7mc/?spm_id_from=333.337.search-card.all.click 
- State pattern: https://www.youtube.com/watch?v=OeirQdzYdnc
- Pacman AI ghost explained: https://www.youtube.com/watch?v=ICwzQ0_RCcQ

## AI Usage

AI tools were used for:

- Architecture discussions
- Debugging assistance
- Design reviews
- Documentation drafting
- Code review
- Code Implementation

All generated content was reviewed, understood, and adapted before integration into the project. (or not...)

---

## Future Improvements

- Sound effects and music
- Additional platform builds (Windows, macOS)

---