from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal

from core.context import GameContext
from core.state import GameState, StatePayload

TransitionKind = Literal["change", "push", "pop", "shutdown"]


@dataclass(frozen=True, slots=True)
class Transition:
    """BOILERPLATE: deferred scene transition applied at frame boundary."""

    kind: TransitionKind
    state: GameState | None = None
    payload: StatePayload | None = None


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
        payload: StatePayload | None = None,
    ) -> None:
        """Replace full stack with a new state."""
        self._enqueue(Transition("change", state, payload))

    def push(
        self,
        state: GameState,
        payload: StatePayload | None = None,
    ) -> None:
        """Push modal state on top of current stack."""
        self._enqueue(Transition("push", state, payload))

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

            if transition.kind == "shutdown":
                while self._stack:
                    self._leave_top_state(context)
                self._shutdown_requested = True
                self._pending.clear()
                return

            if transition.kind == "pop":
                self._pop_state(context)
                continue

            if transition.state is None:
                raise ValueError("Transition state is required")

            if transition.kind == "change":
                self._change_state(context, transition.state, transition.payload)
                continue

            if transition.kind == "push":
                self._push_state(context, transition.state, transition.payload)

    def _enqueue(self, transition: Transition) -> None:
        """Queue a transition for the next flush."""
        self._pending.append(transition)

    def _change_state(
        self,
        context: GameContext,
        state: GameState,
        payload: StatePayload | None,
    ) -> None:
        while self._stack:
            self._leave_top_state(context)
        self._push_state(context, state, payload)

    def _push_state(
        self,
        context: GameContext,
        state: GameState,
        payload: StatePayload | None,
    ) -> None:
        self._stack.append(state)
        state.enter(context, payload)

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
