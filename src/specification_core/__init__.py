"""Composable specifications for deterministic, explainable decisions."""

from ._trace import TraceEvent, TraceOutcome, TraceRecorder
from .async_core import (
    AsyncAndSpecification,
    AsyncBooleanDecisionAdapter,
    AsyncDecisionSpec,
    AsyncFirstMatch,
    AsyncNotSpecification,
    AsyncOrSpecification,
    AsyncPredicateDecisionSpec,
    AsyncPredicateSpec,
    AsyncSpecification,
)
from .core import (
    AlwaysFalse,
    AlwaysTrue,
    AndSpecification,
    BooleanDecisionAdapter,
    DateComparisonSpec,
    DecisionSpec,
    EvaluationContext,
    FirstMatch,
    MatchResult,
    MaxCountSpec,
    NotSpecification,
    OrSpecification,
    PredicateDecisionSpec,
    PredicateSpec,
    Specification,
    TimeSinceEventSpec,
)

__all__ = [
    "AlwaysFalse", "AlwaysTrue", "AndSpecification", "AsyncAndSpecification",
    "AsyncBooleanDecisionAdapter", "AsyncDecisionSpec", "AsyncFirstMatch",
    "AsyncNotSpecification", "AsyncOrSpecification", "AsyncPredicateDecisionSpec",
    "AsyncPredicateSpec", "AsyncSpecification", "BooleanDecisionAdapter",
    "DateComparisonSpec", "DecisionSpec", "EvaluationContext", "FirstMatch",
    "MatchResult", "MaxCountSpec", "NotSpecification", "OrSpecification",
    "PredicateDecisionSpec", "PredicateSpec", "Specification", "TimeSinceEventSpec",
    "TraceEvent", "TraceOutcome", "TraceRecorder",
]
