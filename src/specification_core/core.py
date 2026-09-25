"""Synchronous boolean specifications and typed decisions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Generic, TypeVar, cast, final

from ._trace import TraceRecorder, record

T = TypeVar("T")
R = TypeVar("R")


class Specification(ABC, Generic[T]):
    """A named rule that answers whether a candidate satisfies a condition."""

    __slots__ = ("_name", "_sealed")

    def __init__(self, name: str | None = None) -> None:
        self._name = name or type(self).__name__
        self._sealed = False

    def __setattr__(self, key: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError(f"{type(self).__name__} is immutable")
        object.__setattr__(self, key, value)

    def _seal(self) -> None:
        object.__setattr__(self, "_sealed", True)

    @property
    def name(self) -> str:
        return self._name

    def is_satisfied_by(self, candidate: T, *, recorder: TraceRecorder | None = None) -> bool:
        return record(recorder, self.name, lambda: self._evaluate(candidate, recorder))

    @abstractmethod
    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        raise NotImplementedError

    def and_(self, other: Specification[T]) -> AndSpecification[T]:
        return AndSpecification(self, other)

    def or_(self, other: Specification[T]) -> OrSpecification[T]:
        return OrSpecification(self, other)

    def not_(self) -> NotSpecification[T]:
        return NotSpecification(self)

    def returning(self, result: R) -> BooleanDecisionAdapter[T, R]:
        return BooleanDecisionAdapter(self, result)

    def __and__(self, other: Specification[T]) -> AndSpecification[T]:
        return self.and_(other)

    def __or__(self, other: Specification[T]) -> OrSpecification[T]:
        return self.or_(other)

    def __invert__(self) -> NotSpecification[T]:
        return self.not_()


@final
class PredicateSpec(Specification[T]):
    """An immutable rule backed by a predicate."""

    __slots__ = ("_predicate",)

    def __init__(self, predicate: Callable[[T], bool], name: str | None = None) -> None:
        super().__init__(name)
        self._predicate = predicate
        self._seal()

    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        return bool(self._predicate(candidate))


@final
class AlwaysTrue(Specification[T]):
    __slots__ = ()

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._seal()

    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        return True


@final
class AlwaysFalse(Specification[T]):
    __slots__ = ()

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._seal()

    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        return False


@final
class AndSpecification(Specification[T]):
    __slots__ = ("_left", "_right")

    def __init__(self, left: Specification[T], right: Specification[T], name: str = "AND") -> None:
        super().__init__(name)
        self._left, self._right = left, right
        self._seal()

    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        if not self._left.is_satisfied_by(candidate, recorder=recorder):
            if recorder is not None:
                recorder.skipped(self._right.name)
            return False
        return self._right.is_satisfied_by(candidate, recorder=recorder)


@final
class OrSpecification(Specification[T]):
    __slots__ = ("_left", "_right")

    def __init__(self, left: Specification[T], right: Specification[T], name: str = "OR") -> None:
        super().__init__(name)
        self._left, self._right = left, right
        self._seal()

    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        if self._left.is_satisfied_by(candidate, recorder=recorder):
            if recorder is not None:
                recorder.skipped(self._right.name)
            return True
        return self._right.is_satisfied_by(candidate, recorder=recorder)


@final
class NotSpecification(Specification[T]):
    __slots__ = ("_wrapped",)

    def __init__(self, wrapped: Specification[T], name: str = "NOT") -> None:
        super().__init__(name)
        self._wrapped = wrapped
        self._seal()

    def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        return not self._wrapped.is_satisfied_by(candidate, recorder=recorder)


class DecisionSpec(ABC, Generic[T, R]):
    """A specification that yields a typed outcome when it matches."""

    __slots__ = ("_name", "_sealed")

    def __init__(self, name: str | None = None) -> None:
        self._name = name or type(self).__name__
        self._sealed = False

    def __setattr__(self, key: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError(f"{type(self).__name__} is immutable")
        object.__setattr__(self, key, value)

    def _seal(self) -> None:
        object.__setattr__(self, "_sealed", True)

    @property
    def name(self) -> str:
        return self._name

    def decide(self, candidate: T, *, recorder: TraceRecorder | None = None) -> MatchResult[R]:
        return record(recorder, self.name, lambda: self._decide(candidate, recorder))

    @abstractmethod
    def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class MatchResult(Generic[R]):
    """Result of a decision. Inspect ``matched`` before reading ``value``."""

    matched: bool
    value: R | None = None

    @classmethod
    def match(cls, value: R) -> MatchResult[R]:
        return cls(True, value)

    @classmethod
    def no_match(cls) -> MatchResult[R]:
        return cls(False)


@final
class BooleanDecisionAdapter(DecisionSpec[T, R]):
    __slots__ = ("_specification", "_result")

    def __init__(self, specification: Specification[T], result: R) -> None:
        super().__init__()
        self._specification, self._result = specification, result
        self._seal()

    def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        if self._specification.is_satisfied_by(candidate, recorder=recorder):
            return MatchResult.match(self._result)
        return MatchResult.no_match()


@final
class PredicateDecisionSpec(DecisionSpec[T, R]):
    __slots__ = ("_predicate", "_result")

    def __init__(self, predicate: Callable[[T], bool], result: R, name: str | None = None) -> None:
        super().__init__(name)
        self._predicate, self._result = predicate, result
        self._seal()

    def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        return MatchResult.match(self._result) if self._predicate(candidate) else MatchResult.no_match()


@final
class FirstMatch(DecisionSpec[T, R]):
    """Evaluate named rule/result pairs in order and select the first match."""

    __slots__ = ("_pairs", "_fallback", "_has_fallback")

    def __init__(
        self,
        pairs: Iterable[tuple[Specification[T], R]],
        *,
        fallback: R | None = None,
        has_fallback: bool = False,
        name: str = "FirstMatch",
    ) -> None:
        super().__init__(name)
        self._pairs = tuple(pairs)
        self._fallback, self._has_fallback = fallback, has_fallback
        self._seal()

    @classmethod
    def with_fallback(
        cls, pairs: Iterable[tuple[Specification[T], R]], fallback: R, name: str = "FirstMatch"
    ) -> FirstMatch[T, R]:
        return cls(pairs, fallback=fallback, has_fallback=True, name=name)

    def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        for index, (specification, result) in enumerate(self._pairs):
            if specification.is_satisfied_by(candidate, recorder=recorder):
                if recorder is not None:
                    for later, (skipped_spec, _) in enumerate(self._pairs[index + 1 :], start=index + 1):
                        recorder.skipped(f"pair[{later}]:{skipped_spec.name}")
                return MatchResult.match(result)
        return MatchResult.match(cast(R, self._fallback)) if self._has_fallback else MatchResult.no_match()


@final
class EvaluationContext:
    """Immutable snapshot of values consumed by built-in specifications."""

    __slots__ = ("_current_date", "_counters", "_events", "_flags", "_user_data", "_sealed")

    def __init__(
        self,
        *,
        current_date: datetime,
        counters: dict[str, int] | None = None,
        events: dict[str, datetime] | None = None,
        flags: dict[str, bool] | None = None,
        user_data: dict[str, object] | None = None,
    ) -> None:
        if not isinstance(current_date, datetime):
            raise TypeError("current_date must be a datetime")
        self._current_date = current_date
        self._counters = MappingProxyType(dict(counters or {}))
        self._events = MappingProxyType(dict(events or {}))
        self._flags = MappingProxyType(dict(flags or {}))
        self._user_data = MappingProxyType(dict(user_data or {}))
        self._sealed = True

    def __setattr__(self, key: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("EvaluationContext is immutable")
        object.__setattr__(self, key, value)

    @property
    def current_date(self) -> datetime:
        return self._current_date

    def counter(self, key: str) -> int:
        return self._counters.get(key, 0)

    def event(self, key: str) -> datetime | None:
        return self._events.get(key)

    def flag(self, key: str) -> bool:
        return self._flags.get(key, False)

    def user_data(self, key: str) -> object | None:
        return self._user_data.get(key)


@final
class MaxCountSpec(Specification[EvaluationContext]):
    __slots__ = ("_counter_key", "_maximum_count")

    def __init__(self, counter_key: str, maximum_count: int) -> None:
        super().__init__()
        self._counter_key, self._maximum_count = counter_key, maximum_count
        self._seal()

    def _evaluate(self, candidate: EvaluationContext, recorder: TraceRecorder | None) -> bool:
        return candidate.counter(self._counter_key) < self._maximum_count


@final
class DateComparisonSpec(Specification[EvaluationContext]):
    __slots__ = ("_event_key", "_comparison", "_date")

    def __init__(self, event_key: str, comparison: str, date: datetime) -> None:
        super().__init__()
        if comparison not in {"before", "after"}:
            raise ValueError("comparison must be 'before' or 'after'")
        self._event_key, self._comparison, self._date = event_key, comparison, date
        self._seal()

    def _evaluate(self, candidate: EvaluationContext, recorder: TraceRecorder | None) -> bool:
        event_date = candidate.event(self._event_key)
        if event_date is None:
            return False
        return event_date < self._date if self._comparison == "before" else event_date > self._date


@final
class TimeSinceEventSpec(Specification[EvaluationContext]):
    __slots__ = ("_event_key", "_minimum_seconds")

    def __init__(self, event_key: str, minimum_seconds: float) -> None:
        super().__init__()
        if minimum_seconds < 0:
            raise ValueError("minimum_seconds must be non-negative")
        self._event_key, self._minimum_seconds = event_key, minimum_seconds
        self._seal()

    def _evaluate(self, candidate: EvaluationContext, recorder: TraceRecorder | None) -> bool:
        event_date = candidate.event(self._event_key)
        if event_date is None:
            return True
        return (candidate.current_date - event_date).total_seconds() >= self._minimum_seconds
