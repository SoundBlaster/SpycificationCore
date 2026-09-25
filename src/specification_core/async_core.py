"""Sequential, short-circuiting asynchronous specifications."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Iterable
from typing import Generic, TypeVar, cast, final

from ._trace import TraceRecorder, record_async
from .core import MatchResult, Specification

T = TypeVar("T")
R = TypeVar("R")


async def _evaluate_child(
    specification: Specification[T] | AsyncSpecification[T],
    candidate: T,
    recorder: TraceRecorder | None,
) -> bool:
    if isinstance(specification, AsyncSpecification):
        return await specification.is_satisfied_by(candidate, recorder=recorder)
    return specification.is_satisfied_by(candidate, recorder=recorder)


class AsyncSpecification(ABC, Generic[T]):
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

    async def is_satisfied_by(self, candidate: T, *, recorder: TraceRecorder | None = None) -> bool:
        return await record_async(recorder, self.name, lambda: self._evaluate(candidate, recorder))

    @abstractmethod
    async def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        raise NotImplementedError

    def and_(self, other: Specification[T] | AsyncSpecification[T]) -> AsyncAndSpecification[T]:
        return AsyncAndSpecification(self, other)

    def or_(self, other: Specification[T] | AsyncSpecification[T]) -> AsyncOrSpecification[T]:
        return AsyncOrSpecification(self, other)

    def not_(self) -> AsyncNotSpecification[T]:
        return AsyncNotSpecification(self)

    def __and__(self, other: Specification[T] | AsyncSpecification[T]) -> AsyncAndSpecification[T]:
        return self.and_(other)

    def __or__(self, other: Specification[T] | AsyncSpecification[T]) -> AsyncOrSpecification[T]:
        return self.or_(other)

    def __invert__(self) -> AsyncNotSpecification[T]:
        return self.not_()


@final
class AsyncPredicateSpec(AsyncSpecification[T]):
    __slots__ = ("_predicate",)

    def __init__(self, predicate: Callable[[T], Awaitable[bool]], name: str | None = None) -> None:
        super().__init__(name)
        self._predicate = predicate
        self._seal()

    async def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        return bool(await self._predicate(candidate))


@final
class AsyncAndSpecification(AsyncSpecification[T]):
    __slots__ = ("_left", "_right")

    def __init__(
        self,
        left: Specification[T] | AsyncSpecification[T],
        right: Specification[T] | AsyncSpecification[T],
        name: str = "AND",
    ) -> None:
        super().__init__(name)
        self._left, self._right = left, right
        self._seal()

    async def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        if not await _evaluate_child(self._left, candidate, recorder):
            if recorder is not None:
                recorder.skipped(self._right.name)
            return False
        return await _evaluate_child(self._right, candidate, recorder)


@final
class AsyncOrSpecification(AsyncSpecification[T]):
    __slots__ = ("_left", "_right")

    def __init__(
        self,
        left: Specification[T] | AsyncSpecification[T],
        right: Specification[T] | AsyncSpecification[T],
        name: str = "OR",
    ) -> None:
        super().__init__(name)
        self._left, self._right = left, right
        self._seal()

    async def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        if await _evaluate_child(self._left, candidate, recorder):
            if recorder is not None:
                recorder.skipped(self._right.name)
            return True
        return await _evaluate_child(self._right, candidate, recorder)


@final
class AsyncNotSpecification(AsyncSpecification[T]):
    __slots__ = ("_wrapped",)

    def __init__(self, wrapped: Specification[T] | AsyncSpecification[T], name: str = "NOT") -> None:
        super().__init__(name)
        self._wrapped = wrapped
        self._seal()

    async def _evaluate(self, candidate: T, recorder: TraceRecorder | None) -> bool:
        return not await _evaluate_child(self._wrapped, candidate, recorder)


class AsyncDecisionSpec(ABC, Generic[T, R]):
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

    async def decide(self, candidate: T, *, recorder: TraceRecorder | None = None) -> MatchResult[R]:
        return await record_async(recorder, self.name, lambda: self._decide(candidate, recorder))

    @abstractmethod
    async def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        raise NotImplementedError


@final
class AsyncFirstMatch(AsyncDecisionSpec[T, R]):
    __slots__ = ("_pairs", "_fallback", "_has_fallback")

    def __init__(
        self,
        pairs: Iterable[tuple[Specification[T] | AsyncSpecification[T], R]],
        *,
        fallback: R | None = None,
        has_fallback: bool = False,
        name: str = "AsyncFirstMatch",
    ) -> None:
        super().__init__(name)
        self._pairs = tuple(pairs)
        self._fallback, self._has_fallback = fallback, has_fallback
        self._seal()

    @classmethod
    def with_fallback(
        cls, pairs: Iterable[tuple[Specification[T] | AsyncSpecification[T], R]], fallback: R
    ) -> AsyncFirstMatch[T, R]:
        return cls(pairs, fallback=fallback, has_fallback=True)

    async def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        for index, (specification, result) in enumerate(self._pairs):
            if await _evaluate_child(specification, candidate, recorder):
                if recorder is not None:
                    for later, (omitted, _) in enumerate(self._pairs[index + 1 :], start=index + 1):
                        recorder.skipped(f"pair[{later}]:{omitted.name}")
                return MatchResult.match(result)
        return MatchResult.match(cast(R, self._fallback)) if self._has_fallback else MatchResult.no_match()


@final
class AsyncBooleanDecisionAdapter(AsyncDecisionSpec[T, R]):
    __slots__ = ("_specification", "_result")

    def __init__(self, specification: Specification[T] | AsyncSpecification[T], result: R) -> None:
        super().__init__()
        self._specification, self._result = specification, result
        self._seal()

    async def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        if await _evaluate_child(self._specification, candidate, recorder):
            return MatchResult.match(self._result)
        return MatchResult.no_match()


@final
class AsyncPredicateDecisionSpec(AsyncDecisionSpec[T, R]):
    __slots__ = ("_predicate", "_result")

    def __init__(self, predicate: Callable[[T], Awaitable[bool]], result: R, name: str | None = None) -> None:
        super().__init__(name)
        self._predicate, self._result = predicate, result
        self._seal()

    async def _decide(self, candidate: T, recorder: TraceRecorder | None) -> MatchResult[R]:
        return MatchResult.match(self._result) if await self._predicate(candidate) else MatchResult.no_match()
