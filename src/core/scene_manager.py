from __future__ import annotations

from collections import deque
from typing import Literal

from core.context import GameContext
from core.state import GameState

TransitionKind = Literal["change", "push", "pop", "shutdown"]
Transition = tuple[TransitionKind, GameState | None]


class SceneManager:
    """Stack of game scenes with deferred push, pop, and change."""

    def __init__(self) -> None:
        """Start with an empty scene stack."""
        self._stack: list[GameState] = []
        self._pending: deque[Transition] = deque()
        self.shutdown_requested: bool = False

    def top(self) -> GameState | None:
        """Return the active scene, or None when the stack is empty.

        Returns:
            Topmost scene, if any.
        """
        if not self._stack:
            return None
        return self._stack[-1]

    def stack_bottom_up(self) -> tuple[GameState, ...]:
        """Return all stacked scenes from bottom to top.

        Returns:
            Immutable tuple of scenes in draw order.
        """
        return tuple(self._stack)

    def change(self, state: GameState) -> None:
        """Replace the entire stack with one scene.

        Args:
            state: Scene to show.
        """
        self._enqueue(("change", state))

    def push(self, state: GameState) -> None:
        """Push a scene on top of the current one.

        Args:
            state: Overlay scene to show.
        """
        self._enqueue(("push", state))

    def pop(self) -> None:
        """Remove the top scene and resume the one below."""
        self._enqueue(("pop", None))

    def request_shutdown(self) -> None:
        """Leave every scene and mark the engine for exit."""
        self._enqueue(("shutdown", None))

    def flush(self, context: GameContext) -> None:
        """Apply queued scene transitions.

        Args:
            context: Shared game context passed to enter/leave hooks.
        """
        while self._pending:
            transition = self._pending.popleft()

            kind, state = transition
            match kind:
                case "shutdown":
                    while self._stack:
                        self._leave_top_state(context)
                    self.shutdown_requested = True
                    self._pending.clear()
                    return
                case "pop":
                    self._pop_state(context)
                case "change" | "push":
                    if state is None:
                        raise ValueError("Transition state is required")
                    if kind == "change":
                        self._change_state(context, state)
                    else:
                        self._push_state(context, state)

    def _enqueue(self, transition: Transition) -> None:
        """Queue a transition for the next flush.

        Args:
            transition: Kind and target scene.
        """
        self._pending.append(transition)

    def _change_state(self, context: GameContext, state: GameState) -> None:
        """Leave all scenes, then push the new one.

        Args:
            context: Shared game context.
            state: Replacement scene.
        """
        while self._stack:
            self._leave_top_state(context)
        self._push_state(context, state)

    def _push_state(self, context: GameContext, state: GameState) -> None:
        """Activate a scene on top of the stack.

        Args:
            context: Shared game context.
            state: Scene to activate.
        """
        self._stack.append(state)
        state.enter(context)

    def _pop_state(self, context: GameContext) -> None:
        """Leave the top scene; request shutdown if the stack empties.

        Args:
            context: Shared game context.
        """
        if not self._stack:
            self.shutdown_requested = True
            return
        self._leave_top_state(context)
        if not self._stack:
            self.shutdown_requested = True

    def _leave_top_state(self, context: GameContext) -> None:
        """Call ``leave`` on and remove the top scene.

        Args:
            context: Shared game context.
        """
        state = self._stack.pop()
        state.leave(context)
