"""Evaluation-local tracing primitives shared by sync and async objects."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
import asyncio
from threading import RLock
from time import perf_counter_ns
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class TraceOutcome(str, Enum):
    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    SELECTED = "selected"
    NO_MATCH = "no_match"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class TraceEvent:
    event_id: int
    parent_id: int | None
    name: str
    outcome: TraceOutcome
    duration_ns: int
    error_type: str | None = None


@dataclass(frozen=True, slots=True)
class _Frame:
    recorder: TraceRecorder
    event_id: int


_frames: ContextVar[tuple[_Frame, ...]] = ContextVar("specification_trace_frames", default=())


class TraceRecorder:
    """Thread-safe event sink for one logical evaluation."""

    __slots__ = ("_events", "_next_id", "_lock")

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []
        self._next_id = 1
        self._lock = RLock()

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        with self._lock:
            return tuple(sorted(self._events, key=lambda event: event.event_id))

    def evaluate(self, name: str, operation: Callable[[], T]) -> T:
        """Record an operation and preserve its result or exception."""
        frames = _frames.get()
        parent_id = next((frame.event_id for frame in reversed(frames) if frame.recorder is self), None)
        with self._lock:
            event_id = self._next_id
            self._next_id += 1
        token = _frames.set(frames + (_Frame(self, event_id),))
        started = perf_counter_ns()
        outcome = TraceOutcome.FAILED
        error_type: str | None = None
        try:
            result = operation()
            outcome = _outcome(result)
            return result
        except BaseException as error:
            error_type = type(error).__name__
            outcome = TraceOutcome.CANCELLED if isinstance(error, (asyncio.CancelledError, KeyboardInterrupt, SystemExit)) else TraceOutcome.FAILED
            raise
        finally:
            duration = perf_counter_ns() - started
            _frames.reset(token)
            with self._lock:
                self._events.append(TraceEvent(event_id, parent_id, name, outcome, duration, error_type))

    async def evaluate_async(self, name: str, operation: Callable[[], Awaitable[T]]) -> T:
        """Record an awaitable operation through its completion."""
        frames = _frames.get()
        parent_id = next((frame.event_id for frame in reversed(frames) if frame.recorder is self), None)
        with self._lock:
            event_id = self._next_id
            self._next_id += 1
        token = _frames.set(frames + (_Frame(self, event_id),))
        started = perf_counter_ns()
        outcome = TraceOutcome.FAILED
        error_type: str | None = None
        try:
            result = await operation()
            outcome = _outcome(result)
            return result
        except BaseException as error:
            error_type = type(error).__name__
            outcome = TraceOutcome.CANCELLED if isinstance(error, (asyncio.CancelledError, KeyboardInterrupt, SystemExit)) else TraceOutcome.FAILED
            raise
        finally:
            duration = perf_counter_ns() - started
            _frames.reset(token)
            with self._lock:
                self._events.append(TraceEvent(event_id, parent_id, name, outcome, duration, error_type))

    def skipped(self, name: str) -> None:
        frames = _frames.get()
        parent_id = next((frame.event_id for frame in reversed(frames) if frame.recorder is self), None)
        with self._lock:
            event_id = self._next_id
            self._next_id += 1
            self._events.append(TraceEvent(event_id, parent_id, name, TraceOutcome.SKIPPED, 0))


def record(recorder: TraceRecorder | None, name: str, operation: Callable[[], T]) -> T:
    return operation() if recorder is None else recorder.evaluate(name, operation)


async def record_async(recorder: TraceRecorder | None, name: str, operation: Callable[[], Awaitable[T]]) -> T:
    if recorder is None:
        return await operation()
    return await recorder.evaluate_async(name, operation)


def skipped(name: str) -> None:
    frames = _frames.get()
    if frames:
        frames[-1].recorder.skipped(name)


def _outcome(value: object) -> TraceOutcome:
    if isinstance(value, bool):
        return TraceOutcome.SATISFIED if value else TraceOutcome.UNSATISFIED
    matched = getattr(value, "matched", None)
    if matched is False:
        return TraceOutcome.NO_MATCH
    if matched is True:
        return TraceOutcome.SELECTED
    return TraceOutcome.SELECTED
