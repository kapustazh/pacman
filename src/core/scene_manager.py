from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

from core.context import GameContext
from core.state import GameState, StateEnterData

TransitionKind = Literal["change", "push", "pop", "shutdown"]


@dataclass(frozen=True, slots=True)
class Transition:
    """BOILERPLATE: deferred scene transition applied at frame boundary."""

    kind: TransitionKind
    state: GameState | None = None
    enter_data: StateEnterData | None = None


class SceneManager:
    """Stack-based scene manager for game states."""

    __slots__ = ("_pending", "_shutdown_requested", "_stack")

    def __init__(self) -> None:
        self._stack: list[GameState] = []
        self._pending: deque[Transition] = deque()
        self._shutdown_requested = False

    @property
    def shutdown_requested(self) -> bool:
        """Return True when engine should stop."""
        return self._shutdown_requested

    def top(self) -> GameState | None:
        """Return active top state."""
        if not self._stack:
            return None
        return self._stack[-1]

    def stack_bottom_up(self) -> tuple[GameState, ...]:
        """Return stack in draw order."""
        return tuple(self._stack)

    def change(
        self,
        state: GameState,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Replace full stack with a new state."""
        self._enqueue(Transition("change", state, enter_data))

    def push(
        self,
        state: GameState,
        enter_data: StateEnterData | None = None,
    ) -> None:
        """Push modal state on top of current stack."""
        self._enqueue(Transition("push", state, enter_data))

    def pop(self) -> None:
        """Pop top state."""
        self._enqueue(Transition("pop"))

    def request_shutdown(self) -> None:
        """Request engine shutdown."""
        self._enqueue(Transition("shutdown"))

    def flush(self, context: GameContext) -> None:
        """Apply pending transitions after event/update processing."""
        while self._pending:
            transition = self._pending.popleft()

            match transition.kind:
                case "shutdown":
                    while self._stack:
                        self._leave_top_state(context)
                    self._shutdown_requested = True
                    self._pending.clear()
                    return
                case "pop":
                    self._pop_state(context)
                case "change" | "push":
                    if transition.state is None:
                        raise ValueError("Transition state is required")
                    if transition.kind == "change":
                        self._change_state(
                            context, transition.state, transition.enter_data
                        )
                    else:
                        self._push_state(
                            context, transition.state, transition.enter_data
                        )

    def _enqueue(self, transition: Transition) -> None:
        """Queue a transition for the next flush."""
        self._pending.append(transition)

    def _change_state(
        self,
        context: GameContext,
        state: GameState,
        enter_data: StateEnterData | None,
    ) -> None:
        while self._stack:
            self._leave_top_state(context)
        self._push_state(context, state, enter_data)

    def _push_state(
        self,
        context: GameContext,
        state: GameState,
        enter_data: StateEnterData | None,
    ) -> None:
        self._stack.append(state)
        state.enter(context, enter_data)

    def _pop_state(self, context: GameContext) -> None:
        if not self._stack:
            self._shutdown_requested = True
            return
        self._leave_top_state(context)
        if not self._stack:
            self._shutdown_requested = True

    def _leave_top_state(self, context: GameContext) -> None:
        state = self._stack.pop()
        state.leave(context)
