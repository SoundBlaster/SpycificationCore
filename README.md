# SpecificationCore for Python

Typed, composable rules for deterministic decisions, with short-circuit
evaluation, explicit no-match results, async counterparts, and local traces.
Requires Python 3.10 or later.

```python
from dataclasses import dataclass

from specification_core import FirstMatch, PredicateSpec, TraceRecorder


@dataclass(frozen=True)
class Candidate:
    schema_valid: bool
    evidence_present: bool
    contains_private_data: bool
    operator_approved: bool


reviewable = (
    PredicateSpec(lambda item: item.schema_valid, "schema.valid")
    & PredicateSpec(lambda item: item.evidence_present, "evidence.present")
    & PredicateSpec(lambda item: not item.contains_private_data, "privacy.clear")
)

routing = FirstMatch(
    [
        (reviewable & PredicateSpec(lambda item: item.operator_approved, "operator.approved"), "request_promotion"),
        (reviewable, "request_review"),
    ]
)

recorder = TraceRecorder()
decision = routing.decide(
    Candidate(True, True, False, False),
    recorder=recorder,
)
assert decision.matched and decision.value == "request_review"
for event in recorder.events:
    print(event.name, event.outcome.value)
```

Rules compute outcomes and diagnostics. The caller owns side effects such as
publishing a proposal or calling a service. See
[`docs/compatibility.md`](docs/compatibility.md) for adapted and deferred APIs.

The package is licensed under MIT; see [`LICENSE`](LICENSE).
