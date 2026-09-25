from datetime import datetime, timedelta

from specification_core import (
    AlwaysFalse,
    AlwaysTrue,
    BooleanDecisionAdapter,
    DateComparisonSpec,
    EvaluationContext,
    FirstMatch,
    MatchResult,
    MaxCountSpec,
    PredicateDecisionSpec,
    PredicateSpec,
    TimeSinceEventSpec,
    TraceOutcome,
    TraceRecorder,
)


def test_composition_short_circuits_and_records_skipped_rule() -> None:
    calls: list[str] = []

    def left(value: object) -> bool:
        calls.append("left")
        return False

    def right(value: object) -> bool:
        calls.append("right")
        return True

    rule = PredicateSpec(left, "left").and_(PredicateSpec(right, "right"))
    recorder = TraceRecorder()

    assert not rule.is_satisfied_by(object(), recorder=recorder)
    assert calls == ["left"]
    assert [event.outcome for event in recorder.events] == [
        TraceOutcome.UNSATISFIED,
        TraceOutcome.UNSATISFIED,
        TraceOutcome.SKIPPED,
    ]


def test_first_match_distinguishes_none_payload_from_no_match() -> None:
    rule: FirstMatch[object, None] = FirstMatch([(PredicateSpec(lambda value: True, "matches"), None)])
    no_match: FirstMatch[object, str] = FirstMatch([])

    selected = rule.decide(object())
    absent = no_match.decide(object())

    assert selected == MatchResult.match(None)
    assert absent == MatchResult.no_match()


def test_first_match_stops_after_first_satisfied_rule() -> None:
    calls: list[str] = []

    def first(value: object) -> bool:
        calls.append("first")
        return True

    def second(value: object) -> bool:
        calls.append("second")
        return True

    rule = FirstMatch(
        [
            (PredicateSpec(first, "first"), "review"),
            (PredicateSpec(second, "second"), "publish"),
        ]
    )

    assert rule.decide(object()) == MatchResult.match("review")
    assert calls == ["first"]


def test_boolean_rules_and_decision_adapters() -> None:
    positive: PredicateSpec[int] = PredicateSpec(lambda value: value > 0, "positive")

    assert (AlwaysTrue[int]() & positive).is_satisfied_by(1)
    assert (AlwaysFalse[int]() | positive).is_satisfied_by(1)
    assert (~positive).is_satisfied_by(-1)
    adapted: BooleanDecisionAdapter[int, None] = positive.returning(None)
    assert adapted.decide(1) == MatchResult.match(None)
    decision: PredicateDecisionSpec[int, str] = PredicateDecisionSpec(lambda value: value > 0, "accept")
    assert decision.decide(1) == MatchResult.match("accept")
    assert decision.decide(-1) == MatchResult.no_match()


def test_first_match_fallback_and_decision_trace() -> None:
    recorder = TraceRecorder()
    fallback: FirstMatch[object, str] = FirstMatch.with_fallback([], "review")
    assert fallback.decide(object()) == MatchResult.match("review")

    route: FirstMatch[object, str] = FirstMatch(
        [
            (PredicateSpec(lambda value: True, "matches"), "publish"),
            (PredicateSpec(lambda value: True, "later"), "review"),
        ]
    )
    assert route.decide(object(), recorder=recorder) == MatchResult.match("publish")
    assert [event.outcome for event in recorder.events] == [
        TraceOutcome.SELECTED,
        TraceOutcome.SATISFIED,
        TraceOutcome.SKIPPED,
    ]


def test_context_and_time_specifications() -> None:
    current = datetime(2026, 1, 1, 12)
    event = current - timedelta(minutes=10)
    counters = {"requests": 2}
    context = EvaluationContext(
        current_date=current,
        counters=counters,
        events={"last_request": event},
        flags={"enabled": True},
        user_data={"tier": "gold"},
    )
    counters["requests"] = 99

    assert context.counter("requests") == 2
    assert context.counter("missing") == 0
    assert context.flag("enabled")
    assert not context.flag("missing")
    assert context.user_data("tier") == "gold"
    assert context.event("missing") is None
    assert MaxCountSpec("requests", 3).is_satisfied_by(context)
    assert DateComparisonSpec("last_request", "before", current).is_satisfied_by(context)
    assert TimeSinceEventSpec("last_request", 300).is_satisfied_by(context)
    assert TimeSinceEventSpec("missing", 300).is_satisfied_by(context)
