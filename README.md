*This project has been created as part of the 42 curriculum by mnestere, wehan.*

# PAC-MAN

## Description

Pac-Man is a clone in Python combining procedural maze generation, BFS-based nulti-targeted ghost AI, configurable gameplay settings, persistent highscores, and robust error handling.

### Features

| Feature | Implementation |
|---------|----------------|
| Maze generation | Uses the assigned A-Maze-ing package through `MazeAdaptor` |
| Levels | At least 10 configured levels |
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
|------|---------|
| W | Move Up |
| A | Move Left |
| S | Move Down |
| D | Move Right |
| Q | Quit |

### Cheats

| Key | Action |
|------|---------|
| I | Toggle Invincibility |
| F | Freeze Ghosts |
| L | Add Life |
| N | Skip Level |

---

## Configuration

The game uses a JSON configuration file.

### Example

```json
{
    "lives": 3,
    "pacgum": 42,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    "level_max_time": 90,
    "highscore_filename": "highscores.json"
}
```

### Parameters

| Parameter | Description |
|------------|------------|
| lives | Initial player lives |
| pacgum | Number of pacgums generated |
| points_per_pacgum | Score gained per pacgum |
| points_per_super_pacgum | Score gained per super pacgum |
| points_per_ghost | Score gained when eating a ghost |
| level_max_time | Maximum time allowed per level |
| highscore_filename | Highscore storage file |

### Validation

- Unknown keys are ignored
- Missing values use safe defaults
- Invalid values are replaced by defaults
- Configuration errors never crash the game

---

## Highscore

Highscores are stored in JSON format.

### Features

- Top 10 leaderboard
- Automatic loading
- Automatic saving
- Input sanitization

### Validation Rules

| Rule | Value |
|--------|--------|
| Maximum Entries | 10 |
| Maximum Name Length | 10 |
| Allowed Characters | Letters, numbers, spaces |
| Score Type | Non-negative integer |

### Design Choice

JSON was chosen because it is:

- Human-readable
- Easy to debug
- Persistent between sessions
- Dependency-free

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
```

MazeAdaptor converts the generated wall-code maze into the internal TileType representation used by the game.

---

## Implementation

### Main Systems

- Maze generation
- Level construction
- Player movement
- Ghost AI
- Collision handling
- Time management
- Highscore persistence

### Ghost AI

Ghosts use Breadth-First Search (BFS) to locate the shortest path toward the player.

When a super-pacgum is eaten, ghosts switch to frightened mode and maximize their Manhattan distance from the player.

### Gameplay Flow

```text
Start Level
      │
      ▼
Collect Pacgums
      │
      ▼
Avoid Ghosts
      │
      ▼
Clear Map
      │
      ▼
Next Level
```

---

## General Software Architecture

```text
MazeGenerator
      │
      ▼
MazeAdaptor
      │
      ▼
LevelBuilder
      │
      ▼
MapData
      │
      ▼
GameState
 ├── Player
 ├── Ghost
 ├── LevelManager
 └── HighscoreManager
```

### Components

| Component | Responsibility |
|------------|------------|
| MazeAdaptor | Converts generated mazes into TileType grids |
| LevelBuilder | Places player, ghosts, pacgums and super-pacgums |
| MapData | Stores and updates map state |
| GameState | Coordinates gameplay logic |
| LevelManager | Handles level progression |
| HighscoreManager | Loads and saves highscores |

---

## Project Management

The project was managed through GitHub branches, pull requests, issue tracking, and team discussions.

Project management documents are available in:

```text
project_management/
```

This directory contains planning, task tracking, meeting notes, technical decisions, and project documentation.

---

## Resources

### References

- Python Documentation
- PEP 8
- PEP 257
- flake8 Documentation
- mypy Documentation
- Breadth-First Search (BFS)
- JSON Documentation

### AI Usage

AI tools were used for:

- Architecture discussions
- Debugging assistance
- Design reviews
- Documentation drafting

All generated content was reviewed, understood, and adapted before integration into the project.