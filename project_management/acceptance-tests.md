# Acceptance Test Plan

Feature-level acceptance tests used for project validation. Each row describes
a reproducible test, the expected behavior, and its current verification status.

Statuses used in this document:

- **PASS** — verified working.
- **FAIL** — known issue or failed acceptance test.
- **FIXED** — previously failed, corrected, and verified again.

Manual gameplay tests are run through `make run`. Static quality checks are run
through `make lint`.

---

## CLI — Usage and launch

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| CLI-01 | Run `make run` | Game launches with `config.json` | PASS | Makefile run target |
| CLI-02 | Run `python3 pac-man.py config.json` in the installed environment | Game launches | PASS | Required CLI form |
| CLI-03 | Run with no config argument | Clear message; no Python traceback | PASS | Argument validation |
| CLI-04 | Run with extra arguments | Clear message; no Python traceback | PASS | Exactly one argument required |

---

## CFG — Configuration

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| CFG-01 | Run with valid `config.json` | Game starts with configured values | PASS | |
| CFG-02 | Add a line starting with `#` | Comment line ignored; config parses | PASS | Required configuration behavior |
| CFG-03 | Use malformed JSON | Warning and safe default config; no traceback | PASS | |
| CFG-04 | Remove a known key | Default used with a clear warning | FIXED Jul 12 | `SCRUM-44` |
| CFG-05 | Set an integer key to a string or boolean | Default value used; no crash | FIXED Jul 12 | Type validation hardened |
| CFG-06 | Add an unknown key | Unknown key is ignored | PASS | Unknown keys are not copied into validated config |
| CFG-07 | Duplicate a top-level key, e.g. two `lives` keys | Duplicate rejected; defaults used | FIXED Jul 13 | `SCRUM-45` |
| CFG-08 | Duplicate a nested level key, e.g. two `width` keys | Duplicate rejected; defaults used | FIXED Jul 13 | `object_pairs_hook` checks nested objects |
| CFG-09 | Configure fewer than 10 levels | Default level list used | PASS | Maintains at least 10 levels |

---

## MAZE — Maze generation

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| MAZE-01 | Start a new game twice with the same first-level seed | First level is reproducible | PASS | Fixed first-level seed |
| MAZE-02 | Advance to later levels | New procedural maze is generated | PASS | Randomized later levels |
| MAZE-03 | Inspect generated map | Walls and corridors are derived from the assigned package output | PASS | `MazeAdaptor` conversion |
| MAZE-04 | Inspect entity placement | Player, ghosts, pacgums, and super-pacgums are placed on reachable cells | FIXED Jul 6 | Reachability hardening |
| MAZE-05 | Trigger the generator error path | Clean warning and fallback behavior; no traceback | FIXED Jul 12 | `SCRUM-44` maze fallback work |
| MAZE-06 | Install the assigned maze package and run the game | Maze generation works without modifying the external package | PASS | Package used through project-side adapter |

---

## PLAYER — Player mechanics

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| PLR-01 | Use arrow keys or WASD | Player changes movement direction | PASS | |
| PLR-02 | Move into a wall | Player does not cross the wall | PASS | |
| PLR-03 | Eat a pacgum | Pacgum disappears and score increases | PASS | |
| PLR-04 | Eat a super-pacgum | Super-pacgum disappears and ghosts become edible | PASS | |
| PLR-05 | Touch a normal ghost | Player loses one life and respawns | PASS | |
| PLR-06 | Lose all lives | Game-over flow starts | PASS | |

---

## GHOST — Ghost mechanics

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| GHO-01 | Play during chase mode | Ghosts autonomously pursue their target tiles | PASS | Junction-based greedy movement |
| GHO-02 | Observe scatter mode | Ghosts change to corner-oriented behavior | FIXED Jul 6 | Chase/scatter pattern restored |
| GHO-03 | Eat a super-pacgum | Ghosts flee and enter frightened mode for a limited time | PASS | |
| GHO-04 | Observe the end of the frightened period | Ghosts flash before returning to normal | FIXED Jul 6 | Visual and game-state polish |
| GHO-05 | Eat an edible ghost | Ghost returns to spawn and later respawns normally | FIXED Jul 11 | Respawn behavior hardened |
| GHO-06 | Compare frightened ghost movement | Frightened ghosts move more slowly while movement remains smooth | FIXED Jul 10 | `SCRUM-39` |
| GHO-07 | Observe the four ghost personalities | Blinky, Pinky, Inky, and Clyde use different chase targets | PASS | Core ghost AI |

---

## PAC — Pacgums and super-pacgums

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| PAC-01 | Start a level | Pacgums appear on reachable corridor cells | PASS | |
| PAC-02 | Inspect maze corners | Four super-pacgums are placed near the four maze corners | PASS | |
| PAC-03 | Change `pacgum` in the configuration | Pacgum placement safely uses the configured count | PASS | Random placement logic |
| PAC-04 | Eat all required pacgums | Level completes | PASS | |

---

## SCORE — Scoring

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| SCR-01 | Eat a pacgum | Score increases by `points_per_pacgum` | PASS | Configuration-backed |
| SCR-02 | Eat a super-pacgum | Score increases by `points_per_super_pacgum` | PASS | Configuration-backed |
| SCR-03 | Eat an edible ghost | Score increases by the configured ghost score value | PASS | Configuration-backed |
| SCR-04 | Observe the HUD during gameplay | Current score remains visible | PASS | |

---

## LVL — Game progression

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| LVL-01 | Eat all required pacgums | Advance to the next level | PASS | |
| LVL-02 | Allow the level timer to expire | Timeout is handled according to game rules without a crash | PASS | Timer integrated into play state |
| LVL-03 | Complete all configured levels | Victory flow is shown | PASS | At least 10 levels |
| LVL-04 | Lose all lives | Game-over flow is shown | PASS | |
| LVL-05 | Finish the victory or game-over flow | Player can enter a name and return to the main menu | PASS | Complete game loop |

---

## HS — Highscores

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| HS-01 | Start with a missing highscore file | Empty highscore board; no crash | PASS | |
| HS-02 | Use malformed highscore JSON | Invalid data is handled safely | PASS | |
| HS-03 | Enter a name longer than 10 characters | Stored name is limited to 10 characters | PASS | |
| HS-04 | Enter symbols in the player name | Only alphanumeric characters and spaces remain | PASS | |
| HS-05 | Add a negative score through manager input | Score is clamped to a non-negative value | PASS | |
| HS-06 | Save more than 10 scores | Only the top 10 remain, sorted in descending order | PASS | |
| HS-07 | Save a score, quit, and relaunch the game | Previous highscore remains available | PASS | JSON persistence |

---

## UI — User interface

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| UI-01 | Launch the game | Main menu is displayed | PASS | |
| UI-02 | Open instructions | Rules and controls are displayed | PASS | |
| UI-03 | Open highscores | Highscore view is displayed | PASS | |
| UI-04 | Start the game | HUD displays score, level, lives, and timer | PASS | |
| UI-05 | Pause the game | Pause state and menu appear | PASS | Pause flow added Jun 26 |
| UI-06 | Resume the game | Game returns to active play | PASS | |
| UI-07 | Trigger game over | Game-over flow is displayed | PASS | |
| UI-08 | Complete the game | Victory flow is displayed | PASS | |
| UI-09 | Toggle fullscreen | Rendering refreshes correctly | FIXED Jul 10 | Fullscreen rendering fix |

---

## CHT — Cheat mode

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| CHT-01 | Use documented cheat controls | Cheat actions are available | PASS | Restored Jul 6 |
| CHT-02 | Open instructions | Cheat controls are documented | FIXED Jul 13 | `SCRUM-46` |
| CHT-03 | Use speed adjustment | Player speed changes while ghost speed remains independent | FIXED Jul 6 | Gameplay polish |
| CHT-04 | Observe the HUD after using a cheat | Active cheat state is visibly indicated | PASS | |

---

## PKG — Packaging and public platform

| ID | Steps | Expected | Status | Notes |
|----|-------|----------|--------|-------|
| PKG-01 | Follow the repository packaging instructions | Game package can be regenerated | PASS | Reproducible packaging workflow |
| PKG-02 | Open the public-platform build | Packaged game launches and is playable | PASS | Public game build |
| PKG-03 | Inspect the package instructions | Controls, options, and configuration guidance are available | PASS | User-facing documentation |

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