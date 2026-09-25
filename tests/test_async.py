import asyncio

from specification_core import (
    AsyncBooleanDecisionAdapter,
    AsyncFirstMatch,
    AsyncNotSpecification,
    AsyncOrSpecification,
    AsyncPredicateDecisionSpec,
    AsyncPredicateSpec,
    MatchResult,
    PredicateSpec,
    TraceOutcome,
    TraceRecorder,
)


def test_async_composition_accepts_sync_rule_and_short_circuits() -> None:
    calls: list[str] = []

    async def allowed(value: object) -> bool:
        calls.append("async")
        return False

    def sync_rule(value: object) -> bool:
        calls.append("sync")
        return True

    rule = AsyncPredicateSpec(allowed, "async.rule") & PredicateSpec(sync_rule, "sync.rule")
    recorder = TraceRecorder()

    assert not asyncio.run(rule.is_satisfied_by(object(), recorder=recorder))
    assert calls == ["async"]
    assert TraceOutcome.SKIPPED in [event.outcome for event in recorder.events]


def test_async_decisions_and_composition() -> None:
    async def accepted(value: object) -> bool:
        return True

    async def rejected(value: object) -> bool:
        return False

    async def run() -> None:
        good: AsyncPredicateSpec[object] = AsyncPredicateSpec(accepted, "good")
        bad: AsyncPredicateSpec[object] = AsyncPredicateSpec(rejected, "bad")
        allow: AsyncBooleanDecisionAdapter[object, str] = AsyncBooleanDecisionAdapter(good, "allow")
        assert await allow.decide(object()) == MatchResult.match("allow")
        assert await AsyncBooleanDecisionAdapter(bad, "allow").decide(object()) == MatchResult.no_match()
        decision: AsyncPredicateDecisionSpec[object, str] = AsyncPredicateDecisionSpec(accepted, "allow")
        assert await decision.decide(object()) == MatchResult.match("allow")
        rejected_decision: AsyncPredicateDecisionSpec[object, str] = AsyncPredicateDecisionSpec(rejected, "allow")
        assert await rejected_decision.decide(object()) == MatchResult.no_match()
        assert await AsyncOrSpecification(bad, good).is_satisfied_by(object())
        assert await AsyncNotSpecification(bad).is_satisfied_by(object())
        assert await AsyncFirstMatch.with_fallback([(good, "publish")], "review").decide(object()) == MatchResult.match(
            "publish"
        )
        fallback: AsyncFirstMatch[object, str] = AsyncFirstMatch([], fallback="review", has_fallback=True)
        assert await fallback.decide(object()) == MatchResult.match("review")

    asyncio.run(run())
