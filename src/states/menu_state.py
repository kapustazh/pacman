from __future__ import annotations

from typing import ClassVar

from pygame.surface import Surface

from core.context import GameContext
from states.selectable_menu_state import MenuEntry, SelectableMenuState
from states.text import ArcadeTextColor


class MenuState(SelectableMenuState):
    """Main menu scene with keyboard navigation."""

    TITLE_Y: ClassVar[int] = 280
    MENU_START_Y: ClassVar[int] = 520
    TITLE_SCALE: ClassVar[int] = 5
    OPTIONS: ClassVar[tuple[MenuEntry, ...]] = (
        MenuEntry("START GAME", "start"),
        MenuEntry("HIGH SCORES", "highscores"),
        MenuEntry("INSTRUCTIONS", "instructions"),
        MenuEntry("EXIT", "exit"),
    )

    def __init__(self) -> None:
        super().__init__(
            entries=self.OPTIONS,
            menu_start_y=self.MENU_START_Y,
            action_handlers={
                "start": self._start_game,
                "highscores": self._open_highscores,
                "instructions": self._open_instructions,
                "exit": self._exit_game,
            },
        )

    def draw_header(self, surface: Surface, context: GameContext) -> None:
        context.text.draw_centered_arcade_text(
            surface,
            "PAC-MAN",
            self.TITLE_Y,
            ArcadeTextColor.YELLOW,
            self.TITLE_SCALE,
        )

    def _start_game(self, context: GameContext) -> None:
        from states.play_state import PlayState

        context.scene_manager.change(PlayState())

    def _open_highscores(self, context: GameContext) -> None:
        from states.highscores_state import HighscoresState

        context.scene_manager.push(HighscoresState())

    def _open_instructions(self, context: GameContext) -> None:
        from states.instructions_state import InstructionsState

        context.scene_manager.push(InstructionsState())

    def _exit_game(self, context: GameContext) -> None:
        context.scene_manager.request_shutdown()
