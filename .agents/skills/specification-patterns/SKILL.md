---
name: specification-patterns
description: Decide where SpycificationCore clarifies domain policy; use when designing or refactoring decision-heavy Python code, explaining pattern benefits and trade-offs, or evaluating refactoring pilots.
---

# Shape code around semantic decisions

Use this skill to put stable domain decisions in named, testable specifications without turning every branch into a specification. A syntactic opportunity is a prompt to inspect intent, not an instruction to refactor.

## Understand the benefit

SpycificationCore provides a common way to name, compose, test, observe, and change domain rules. Its value includes a consistent development style for humans and agents: callers consume a policy contract instead of reconstructing its conditions. A useful extraction can also expose duplicated rules, unreachable fallbacks, or a decision being recomputed in the wrong layer.

Evaluate the whole decision family, including specifications and their callers. A shorter caller is useful evidence, but does not show that total complexity or duplication fell. For choosing a refactor, explaining its benefit, or assessing a pilot, read [Benefits and evidence](references/benefits-and-evidence.md).

## Decide whether a branch expresses policy

Before changing code, state the question the code answers and list its meaningful outcomes. A decision is a strong specification candidate when it:

- chooses a domain outcome such as eligibility, lifecycle state, authority/provenance, completeness, or routing;
- has stable named alternatives, priority, or a meaningful no-match case;
- is repeated across call sites, needs a single place to evolve, or benefits from named traces and branch-level tests.

Keep ordinary control flow when it performs mechanics: parsing or recognizing syntax, adapting I/O into facts, handling exceptions, projecting optional values, iterating/aggregating, serializing, or carrying out side effects. A large `match` or `if` chain is not automatically a domain rule; inspect what the cases mean and whether the same decision is duplicated elsewhere.

When repeated cases dispatch behavior already owned by variants of an enum or protocol, consider placing that behavior with the variants. Keep a match at a boundary when it translates external or syntactic forms into typed domain facts.

## Keep responsibilities in their layer

Use a narrow pipeline:

```text
input / I-O adapter -> typed facts -> named policy specifications -> typed outcome -> application effects
```

Adapters may branch to parse formats and report malformed input. Specifications evaluate prepared facts; they should not fetch, mutate, publish, or hide fallback effects. The application layer interprets the outcome and performs effects. Do not move a decision to another layer just to make a file-level metric smaller.

Model one semantic decision per specification. Do not create one specification for every `if`, every field, or every line. Prefer a small immutable context that names the facts the decision needs. In Python, use a frozen dataclass for a stable multi-field context. Put each new concrete specification in its own module; share a context type only when it is substantial or used by multiple rules.

Use `Specification` for a Boolean predicate. Use `FirstMatch` for ordered alternatives and make the fallback explicit. Preserve the distinction between `MatchResult.no_match()` and a matched result whose value is `None`; do not silently turn no-match into a fallback. Keep priority order observable and deliberate.

When alternatives produce the same outcome and priority has no semantic meaning, prefer one Boolean specification with explicit composition rather than an ordered decision table. Keep independent observations independent: for example, an operation can be a no-op while findings still prevent readiness.

For example, a promotion decision can be modeled as named outcomes over facts prepared by the caller:

```python
from dataclasses import dataclass
from enum import Enum

from specification_core import FirstMatch, PredicateSpec


@dataclass(frozen=True)
class PromotionContext:
    is_blocked: bool
    repair_preview_applied: bool


class PromotionState(Enum):
    BLOCKED = "blocked"
    REPAIRED_PREVIEW = "repaired_preview"
    READY = "ready"


promotion: FirstMatch[PromotionContext, PromotionState] = FirstMatch.with_fallback(
    [
        (PredicateSpec(lambda c: c.is_blocked, "report.blocked"), PromotionState.BLOCKED),
        (
            PredicateSpec(lambda c: c.repair_preview_applied, "report.repaired_preview"),
            PromotionState.REPAIRED_PREVIEW,
        ),
    ],
    fallback=PromotionState.READY,
    name="promotion.pre_sib_state",
)
```

Keep the order intentional: if facts allow conditions to overlap, the earlier rule wins. For tests and consumers, inspect `MatchResult.matched` before reading `value` when no fallback is configured. Pass a `TraceRecorder` only when the caller needs an evaluation trace.

## Implement and verify

1. Record the current behavior as a decision table: input facts, outcome, precedence, no-match/error behavior, and effects owned by the caller.
   Trace the production callers and producer guarantees. A fallback tested with constructed inputs can still be unreachable in the real pipeline; distinguish reachable behavior from obsolete or contradictory logic before extraction.
2. Separate facts already available at the decision boundary from parsing and external work. Build a typed context from those facts.
3. Name the semantic rules and outcomes. Extract only the policy decision; leave mechanical branches and orchestration in their current owners.
4. Compare observable behavior before and after, including warning/error details and side-effect timing where relevant.
5. Test every outcome, overlapping rules and priority, fallback/no-match, and representative malformed or boundary inputs. If tracing is enabled, assert stable semantic rule names and skipped later branches.
6. Review the diff for unnecessary modules, duplicated rule logic, new dependencies, and decision logic that has leaked into adapters or orchestration.
7. State the observed benefit: shared policy consumers, duplicate rules removed, boundaries restored, useful traces, or reduced caller complexity. Distinguish these results from expectations about future bugs or change cost.

Prefer a behavior-preserving refactor. Do not change the business rule, externally visible output, error contract, or side-effect order unless the user explicitly requested that change.
