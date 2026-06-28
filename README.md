*This project has been created as part of the 42 curriculum by mnestere, wehan.*

# PAC-MAN

## Description

This project recreates Pac-Man using procedural maze generation, BFS-based ghost AI, persistent highscores and modular software architecture.

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
| Ghost AI | BFS pathfinding with different chase targets |
| Frightened mode | Activated by Super Pacgums |
| Respawn | Eaten ghosts temporarily disappear and return after a delay |
| Highscores | Persistent JSON leaderboard |
| Config validation | Missing and invalid values fall back to safe defaults |
| Cheat mode | Invincibility, freeze ghosts, add life, skip level |
| Rendering | Terminal-based renderer |
| Static analysis | `flake8` and `mypy` through Makefile |


---

## Instructions

### Installation

```bash
make install
```

### Run

```bash
make run
```
or 
```bash
python3 pac-man.py config.json
```


### Other commands

```bash
make debug
make lint
make lint-strict
make clean
make re
```

### Controls

| Key | Action |
|-----|--------|
| W A S D | Move |
| P | Pause |
| Q | Quit |
| I | Invincibility |
| F | Freeze ghosts |
| N | Skip level |
| L | Add life |


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
| `level_max_time` | int | `10000` | Maximum turns allowed per level |
| `levels` | list | `10 levels` | Maze size configuration |

- Missing configuration file → load default configuration.
- Invalid JSON → load default configuration.
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
MazeAdapter
      │
      ▼
TileType Grid
      │
      ▼
LevelBuilder
      │
      ▼
GameState
```

MazeAdapter is responsible for

- importing the assigned package
- generating a maze
- converting the wall-code representation into the internal grid
- handling generator failures gracefully

---

## Implementation

### Game Play Flow
Turn flow:

```text
Player Input
    ↓
Move Player
    ↓
Collect Items
    ↓
Collision Check
    ↓
Move Ghosts
    ↓
Collision Check
    ↓
Update Timers
    ↓
Render
```
The player wins a level after collecting all Pacgums.
Lives and score carry across levels.

### Ghost AI

Unlike many student implementations where every ghost simply follows the player, this
project assigns each ghost an individual targeting strategy while sharing a common
Breadth-First Search (BFS) pathfinding algorithm.

| Ghost | Behaviour |
|--------|-----------|
| **Blinky** | Directly targets the player's current position. |
| **Pinky** | Predicts the player's movement and targets tiles ahead. |
| **Inky** | Uses predictive targeting with a small random offset. |
| **Clyde** | Switches between chasing the player and returning home based on distance. |

The pathfinding algorithm remains the same for every ghost. Different behaviour is
achieved by changing the target position rather than the search algorithm.

### Behavior States

```text
CHASE
 ↓
SCATTER
 ↓
FRIGHTENED
 ↓
RESPAWN
```

| State | Description |
|-------|-------------|
| **Chase** | Ghosts compute a target and use **Breadth-First Search (BFS)** to follow the shortest path. |
| **Scatter** | Ghosts temporarily return to their home corner, creating alternating pressure similar to the original *Pac-Man*. |
| **Frightened** | Eating a Super Pacgum changes every ghost into frightened mode. Instead of chasing the player, ghosts attempt to move away while avoiding immediate backtracking whenever possible. |
| **Respawn** | After being eaten, a ghost becomes inactive, waits for a respawn delay, returns to its spawn location, and resumes normal behaviour. |


---

## Software Architecture

### General Software Architecture

```text
pac-man.py                     -> Program entry point
src/
├── config/
│   ├── config.py              -> Load and validate JSON configuration
│   └── defaults.py            -> Default game configuration
│
├── game/
│   ├── game_state.py          -> Main game loop and gameplay coordination
│   ├── level_builder.py       -> Populate maze with player, ghosts and pacgums
│   └── level_manager.py       -> Level progression and seed management
│
├── maze/
│   ├── maze_adapter.py        -> Interface to the A-Maze-ing package
│   └── map_data.py            -> Internal TileType grid representation
│
├── entities/
│   ├── player.py              -> Player movement and scoring
│   └── ghost.py               -> Ghost AI, BFS pathfinding and behaviours
│
├── managers/
│   └── highscore_manager.py   -> Load, validate and save highscores
│
└── ui/
    └── terminal_renderer.py   -> Terminal rendering and HUD output
```

### Module Responsibilities

| Module | Responsibility |
|----------|----------------|
| `config` | Loads and validates the JSON configuration file. |
| `maze` | Generates the maze and converts it into the internal TileType grid. |
| `game` | Controls the game loop, player actions and level progression. |
| `entities` | Implements the player and ghost behaviours. |
| `managers` | Handles persistent highscore storage. |
| `ui` | Displays the current game state in the terminal. |

### Data Flow

```text
config.json
      │
      ▼
load_config()
      │
      ▼
LevelManager
      │
      ▼
MazeAdapter
      │
      ▼
MapData
      │
      ▼
LevelBuilder
      │
      ▼
Player + Ghosts
      │
      ▼
GameState
      │
      ▼
TerminalRenderer
```

### Class Relationships

- `GameState` owns the `Player`, `Ghost`, `MapData`, `LevelManager` and `HighscoreManager`.
- `LevelManager` provides the current level configuration and maze seed.
- `MazeAdapter` converts the external maze into the internal `TileType` grid.
- `LevelBuilder` populates the maze with the player, ghosts and collectibles.
- `Ghost` queries `MapData` for valid movement and uses BFS to determine the next step.
- `TerminalRenderer` reads the current game state and renders the board without modifying gameplay logic.

---

## Project Management

- The project was managed through GitHub branches, pull requests, issue tracking, and team discussions.

- Jira is used for planning, task tracking, meeting notes, technical decisions, and project documentation.
(https://kapustazh.atlassian.net/jira/software/projects/SCRUM/boards/1/timeline?selectedIssue=SCRUM-21)

---

## Resources

- Pacman Guide (Chinese): https://www.bilibili.com/video/BV1Jr4y1C7mc/?spm_id_from=333.337.search-card.all.click 

## AI Usage

AI tools were used for:

- Architecture discussions
- Debugging assistance
- Design reviews
- Documentation drafting

All generated content was reviewed, understood, and adapted before integration into the project.

---

## Future Improvements

- Pygame UI + Audio
- Real-time-based instead of turn-based
- Public deployment

---