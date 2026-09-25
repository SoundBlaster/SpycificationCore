# Swift SpecificationCore compatibility

This Python package follows the behavior of Swift SpecificationCore at the
source revision recorded in `PLAN.md`. It is an idiomatic port, not a source
translation. This table describes the first Python implementation.

| Swift capability | Python status | Notes |
| --- | --- | --- |
| `Specification`, predicate, AND/OR/NOT | Equivalent behavior | `Specification`, `PredicateSpec`, and composition classes; `&`, `|`, `~` operators. Evaluation is left-to-right and short-circuited. |
| `DecisionSpec`, boolean adapter | Adapted | `MatchResult[R]` distinguishes a matching `None` payload from no match. |
| `FirstMatchSpec` | Adapted | Ordered immutable pairs, explicit optional fallback, and `MatchResult`. |
| Async composition and decisions | Equivalent core behavior | Sequential awaits, short-circuiting, exception propagation, and task cancellation. Async composition accepts sync or async child rules. No branch is scheduled in advance. |
| Trace recorder | Adapted | Explicit per-evaluation recorder; event tree, outcomes, duration and skipped branches. No process-wide default recorder or timeline integration. |
| `EvaluationContext` | Adapted | Immutable snapshot with current datetime, counters, events, flags and user data. A naive/aware datetime mismatch raises Python's standard `TypeError`. |
| `MaxCountSpec`, `DateComparisonSpec`, `TimeSinceEventSpec` | Partial | Equivalent core comparisons. Specialized cooldown and date-range specs can be added after their full boundary contracts are mapped. |
| Swift macros, property wrappers, context providers | Deferred / no direct equivalent | Python examples use ordinary composition and explicit context passing. |
| Swift/Rust conformance | Partial | Rust v1 fixtures cover synchronous composition, first-match and context. They do not define async or Swift tracing semantics. |

Trace never stores candidates, decision payloads, or exception messages. It
stores exception type names only. Evaluation exceptions are re-raised after
recording. Python `typing.final` communicates a static restriction to type
checkers; it does not prevent runtime subclassing.
