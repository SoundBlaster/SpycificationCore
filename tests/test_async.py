import asyncio

from specification_core import AsyncPredicateSpec, PredicateSpec, TraceOutcome, TraceRecorder


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
