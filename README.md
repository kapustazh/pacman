*This project has been created as part of the 42 curriculum by mnestere, wehan.*

# PAC-MAN

## Description

This project recreates Pac-Man using procedural maze generation, original Pac-Man inspired ghost AI, persistent highscores and modular software architecture.

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

## Ghost AI

Ghost behaviour is managed by `GameState`, while each ghost is responsible for selecting its own target and deciding its next movement.

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

The global behaviour is controlled by `GameState` and affects every active ghost simultaneously.

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

Instead of computing a complete shortest path every turn, ghosts:
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
                  GameState
                      │
        ┌─────────────┴─────────────┐
        │                           │
   LevelManager                TerminalRenderer
        │
        ▼
   LevelBuilder
        │
        ▼
 MapData + Player + Ghosts
```
**Figure 2.** High-level architecture of the game modules.

### General Software Architecture

```text
pac-man.py                     -> Program entry point
src/
├── config/
│   └── config.py              -> Load and validate JSON configuration
│                              -> Default game configuration
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
│   └── ghost.py               -> Ghost AI, target selection and movement behaviours
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
- `Ghost` queries `MapData` for valid movement and performs junction-based local greedy movement. Breadth-First Search (BFS) is only used during frightened mode to estimate a safe escape direction.
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
- Executable packaging and public deployment

---