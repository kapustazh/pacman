# Acceptance Test Plan

Feature-level acceptance tests used for project validation. Each row describes
a reproducible test, the expected behavior, and its verification status.

Statuses used in this document:

- **PASS** — verified working.
- **FAIL** — known issue or failed acceptance test.
- **FIXED** — previously failed, corrected, and verified again.

Manual gameplay tests are run through `make run`. Static quality checks are run
through `make lint`.

---

## CLI — Usage and Launch

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| CLI-01 | Run `make run` | Game launches with `config.json` | PASS |
| CLI-02 | Run `python3 pac-man.py config.json` in the installed environment | Game launches | PASS |
| CLI-03 | Run with no config argument | Clear message; no Python traceback | PASS |
| CLI-04 | Run with extra arguments | Clear message; no Python traceback | PASS |

---

## CFG — Configuration

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| CFG-01 | Run with valid `config.json` | Game starts with configured values | PASS |
| CFG-02 | Add a line starting with `#` | Comment line ignored; config parses | PASS |
| CFG-03 | Use malformed JSON | Warning and safe default config; no traceback | PASS |
| CFG-04 | Remove a known key | Default used with a clear warning | FIXED |
| CFG-05 | Set an integer key to a string or boolean | Default value used; no crash | FIXED |
| CFG-06 | Add an unknown key | Unknown key is ignored | PASS |
| CFG-07 | Duplicate a top-level key, e.g. two `lives` keys | Duplicate rejected; defaults used | FIXED |
| CFG-08 | Duplicate a nested level key, e.g. two `width` keys | Duplicate rejected; defaults used | FIXED |
| CFG-09 | Configure fewer than 10 levels | Default level list used | PASS |

---

## MAZE — Maze Generation

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| MAZE-01 | Start a new game twice with the same first-level seed | First level is reproducible | PASS |
| MAZE-02 | Advance to later levels | New procedural maze is generated | PASS |
| MAZE-03 | Inspect the generated map | Walls and corridors are derived from the assigned package output | PASS |
| MAZE-04 | Inspect entity placement | Player, ghosts, pacgums, and super-pacgums are placed on reachable cells | FIXED |
| MAZE-05 | Trigger the generator error path | Clean warning and fallback behavior; no traceback | FIXED |
| MAZE-06 | Install the assigned maze package and run the game | Maze generation works without modifying the external package | PASS |

---

## PLAYER — Player Mechanics

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| PLR-01 | Use arrow keys or WASD | Player changes movement direction | PASS |
| PLR-02 | Move into a wall | Player does not cross the wall | PASS |
| PLR-03 | Eat a pacgum | Pacgum disappears and score increases | PASS |
| PLR-04 | Eat a super-pacgum | Super-pacgum disappears and ghosts become edible | PASS |
| PLR-05 | Touch a normal ghost | Player loses one life and respawns | PASS |
| PLR-06 | Lose all lives | Game-over flow starts | PASS |

---

## GHOST — Ghost Mechanics

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| GHO-01 | Play during chase mode | Ghosts autonomously pursue their target tiles | PASS |
| GHO-02 | Observe scatter mode | Ghosts change to corner-oriented behavior | FIXED |
| GHO-03 | Eat a super-pacgum | Ghosts flee and enter frightened mode for a limited time | PASS |
| GHO-04 | Observe the end of the frightened period | Ghosts flash before returning to normal | FIXED |
| GHO-05 | Eat an edible ghost | Ghost returns to spawn and later respawns normally | FIXED |
| GHO-06 | Compare frightened ghost movement | Frightened ghosts move more slowly while movement remains smooth | FIXED |
| GHO-07 | Observe the four ghost personalities | Blinky, Pinky, Inky, and Clyde use different chase targets | PASS |

---

## PAC — Pacgums and Super-Pacgums

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| PAC-01 | Start a level | Pacgums appear on reachable corridor cells | PASS |
| PAC-02 | Inspect maze corners | Four super-pacgums are placed near the four maze corners | PASS |
| PAC-03 | Change `pacgum` in the configuration | Pacgum placement safely uses the configured count | PASS |
| PAC-04 | Eat all required pacgums | Level completes | PASS |

---

## SCORE — Scoring

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| SCR-01 | Eat a pacgum | Score increases by `points_per_pacgum` | PASS |
| SCR-02 | Eat a super-pacgum | Score increases by `points_per_super_pacgum` | PASS |
| SCR-03 | Eat an edible ghost | Score increases by the configured ghost score value | PASS |
| SCR-04 | Observe the HUD during gameplay | Current score remains visible | PASS |

---

## LVL — Game Progression

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| LVL-01 | Eat all required pacgums | Advance to the next level | PASS |
| LVL-02 | Allow the level timer to expire | Timeout is handled according to game rules without a crash | PASS |
| LVL-03 | Complete all configured levels | Victory flow is shown | PASS |
| LVL-04 | Lose all lives | Game-over flow is shown | PASS |
| LVL-05 | Finish the victory or game-over flow | Player can enter a name and return to the main menu | PASS |

---

## HS — Highscores

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| HS-01 | Start with a missing highscore file | Empty highscore board; no crash | PASS |
| HS-02 | Use malformed highscore JSON | Invalid data is handled safely | PASS |
| HS-03 | Enter a name longer than 10 characters | Stored name is limited to 10 characters | PASS |
| HS-04 | Enter symbols in the player name | Only alphanumeric characters and spaces remain | PASS |
| HS-05 | Add a negative score through manager input | Score is clamped to a non-negative value | PASS |
| HS-06 | Save more than 10 scores | Only the top 10 remain, sorted in descending order | PASS |
| HS-07 | Save a score, quit, and relaunch the game | Previous highscore remains available | PASS |

---

## UI — User Interface

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| UI-01 | Launch the game | Main menu is displayed | PASS |
| UI-02 | Open instructions | Rules and controls are displayed | PASS |
| UI-03 | Open highscores | Highscore view is displayed | PASS |
| UI-04 | Start the game | HUD displays score, level, lives, and timer | PASS |
| UI-05 | Pause the game | Pause state and menu appear | PASS |
| UI-06 | Resume the game | Game returns to active play | PASS |
| UI-07 | Trigger game over | Game-over flow is displayed | PASS |
| UI-08 | Complete the game | Victory flow is displayed | PASS |
| UI-09 | Toggle fullscreen | Rendering refreshes correctly | FIXED |

---

## CHT — Cheat Mode

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| CHT-01 | Use documented cheat controls | Cheat actions are available | PASS |
| CHT-02 | Open instructions | Cheat controls are documented | FIXED |
| CHT-03 | Use speed adjustment | Player speed changes while ghost speed remains independent | FIXED |
| CHT-04 | Observe the HUD after using a cheat | Active cheat state is visibly indicated | PASS |

---

## PKG — Packaging and Public Platform

| ID | Steps | Expected | Status |
|----|-------|----------|--------|
| PKG-01 | Follow the repository packaging instructions | Game package can be regenerated | PASS |
| PKG-02 | Open the public-platform build | Packaged game launches and is playable | PASS |
| PKG-03 | Inspect the package instructions | Controls, options, and configuration guidance are available | PASS |

---

## Quality Gate

The final project validation uses:

```bash
make install
make lint
make run
```

The interactive acceptance flow covers the complete game cycle:

```text
Main Menu
    ↓
Start Game
    ↓
Move and collect pacgums
    ↓
Collect a super-pacgum and interact with frightened ghosts
    ↓
Lose lives or complete levels
    ↓
Reach the game-over or victory flow
    ↓
Enter a highscore name
    ↓
Return to the Main Menu
    ↓
Relaunch the game
    ↓
Confirm highscore persistence
```