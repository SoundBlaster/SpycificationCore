from specification_core import (
    FirstMatch,
    MatchResult,
    PredicateSpec,
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
