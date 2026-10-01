# Benefits and evidence

## What the pattern contributes

Treat SpycificationCore as a shared style for managing domain policy throughout development. The same concepts support authoring, review, tests, diagnostics, and later changes. This is especially useful in an AI-assisted SDLC, where multiple agents need to find and modify the same rule without inventing separate conventions.

| Benefit | Mechanism | Evidence to look for |
| --- | --- | --- |
| Uniformity and discoverability | Semantic rule names and a common evaluation contract | Consumers refer to the same named policy; reviewers can locate its definition and tests |
| Centralized policy management | One definition used across the bounded context | Equivalent predicates disappear from callers; an actual rule change is made in one policy definition |
| Local understanding | Typed facts and outcomes separate policy from orchestration | A caller states the decision it needs; parsing, effects, and rule internals remain in their layers |
| Observation and debugging | Stable names and an opt-in TraceRecorder | Traces explain matched, unmatched, and skipped rules without changing application output |
| Boundary diagnosis | Explicit inputs reveal where decisions are made or repeated | Extraction identifies redundant decisions, impossible fallbacks, or downstream reinterpretation of a producer result |

Centralization concerns the semantic rule within its bounded context. It does not require a global registry, singleton, god object, or one module containing every policy. Similar syntax in different contexts may express different rules and should not be merged merely to reduce duplication.

## Use extraction as a diagnostic

Before wrapping existing conditions, ask:

- Which production path supplies these facts, and what does its producer already guarantee?
- Does this consumer need to evaluate the policy, or should it consume an authoritative typed outcome?
- Are repeated predicates semantically identical, including errors, priority, and timing?
- Can the proposed fallback occur in production, or only in a synthetic test?

For example, suppose a producer marks a preview ready when there are no findings and either repairs were applied or the input is already ready with no actions. A downstream fallback for “not ready, no findings, already-ready input, no actions” contradicts that producer rule. Naming its predicate can expose the contradiction. Removing it and consuming the producer outcome restores the boundary; preserving it as a new specification would retain the redundancy.

Record such a finding as a concrete result of the refactoring process. Do not claim the framework automatically detects it or guarantees correctness. Any removal still needs evidence that observable behavior is preserved.

## Evaluate cost and benefit together

Choose the relevant evidence for the task; this is not a mandatory benchmark suite for every extraction.

- **Behavior:** decision tables, representative production paths, output parity, priority, error and effect timing.
- **Duplication:** absolute duplicated conditions or fragments and the number of consumers sharing one policy. A lower clone percentage caused by adding code is not duplicate removal.
- **Local complexity:** caller CC, Cognitive Complexity, nesting, and conditions mixed with orchestration. Also inspect the extracted rules.
- **Whole-family cost:** source size, modules, dependencies, and complexity across callers and specifications. Moving code between files changes its location, not necessarily its total cost.
- **Change locality:** for an actual or controlled change to one rule, count production definitions and consumers that require edits. Keep test edits visible but separate; compare equivalent changes from the same baseline.
- **Diagnostics:** record confirmed redundant decisions and boundary violations found, together with their fixes and supporting evidence.

A summed CC can increase because tools assign a baseline cost to each new function. Record that overhead alongside the decision logic and local improvements. Check whether the chosen tool includes closures and lambdas before comparing variants. Keep measurement scope and tool versions constant.

An import of a stable policy within its intended layer has a different architectural role from a reverse dependency or a consumer reaching into implementation details. Classify dependency edges against the project's declared layers and bounded contexts; count violations separately. A well-placed dependency still has maintenance cost, so do not automatically exempt all specification imports from coupling measurements.

Prefer a Boolean composition when multiple conditions lead to the same result without meaningful priority. Introduce wrappers or a DSL where repeated application of policies benefits from a common contract; measure both caller savings and shared infrastructure cost over the actual consumers.

## Bound the conclusion

Say what was demonstrated: for example, “the shared rule has three consumers, removes two duplicate definitions, preserves the decision table, and permits a policy change without editing callers.” Uniform structure and named traces can be useful even when raw complexity is similar to conventional extraction.

Fewer bugs, less rework, and smaller future blast radius are longitudinal hypotheses until supported by subsequent changes or incidents. A pilot can establish behavior parity, diagnosis, reuse, and controlled change locality; it cannot establish those long-term outcomes by itself. Report overhead honestly without treating a single aggregate number as a verdict on the pattern.
