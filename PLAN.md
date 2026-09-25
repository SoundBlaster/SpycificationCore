# SpycificationCore: план Python-порта

Статус: initial implementation is in place; conformance and release checks remain.

## Цель и исходная точка

Создать самостоятельную typed Python-библиотеку с поведением SpecificationCore:
композиция правил, short-circuit, упорядоченные решения, явный no match,
async evaluation и объяснимый trace. Применение — candidate eligibility и routing.

Источник поведения: соседний `../SpecificationCore`, проверенный commit
`483214469828c42f7b615654aa70d0acbecc4dbf`. Swift checkout чистый.
Дополнительный oracle для общего подмножества — Rust fixtures
`specification-core-rs/crates/specification-core/fixtures/conformance/v1/`.
Swift и Rust не считаются автоматически полностью эквивалентными.

Рабочие допущения: Python 3.10+, import package `specification_core`, distribution
`specification-core`, без обязательных runtime dependencies. Имя distribution предварительное;
доступность имени в PyPI не проверена. Соседние проекты не изменяются.
MIT copyright/permission notice исходника сохраняется при переносе.

## Архитектурные правила

- Небольшие объекты с поведением; композиция и decorators вместо наследования
  реализации, service classes и глобальных registries.
- `Specification[T]`, `DecisionSpec[T, R]` и async counterparts задают узкие
  интерфейсы. Конкретные реализации помечаются `typing.final`.
- Правила хранят неизменяемую конфигурацию; конструкторы связывают зависимости,
  но не вычисляют правила и не выполняют I/O. Нет setters и скрытого cache.
- Списки дочерних правил фиксируются как tuples. Неизменяемость конфигурации
  не означает глубокую неизменяемость переданного candidate или callable.
- Основной API — объекты `And`, `Or`, `Not`, `FirstMatch`, `Returning`.
  Операторы `&`, `|`, `~` — необязательный последующий sugar без повторения логики.
- Результат решения: `MatchResult[R]`, с явным поведением
  извлечения результата/fallback. `Matched(None)` отличим от `NoMatch`.
  Это намеренная адаптация Swift `Result?`, а не буквальная сигнатура порта.
- Ошибки распространяются как exceptions, cancellation сохраняется; ни то,
  ни другое не превращается в false или no match.
- Trace включается явно на одну evaluation. Recorder — отдельный объект с
  изменяемым состоянием; правила остаются неизменяемыми. Нет process-wide recorder.
- `typing.final` проверяется type checker, а не запрещает наследование в runtime.
  Специальный metaclass для runtime-запрета не планируется.

Это практическая адаптация Elegant Objects к Python. `typing`, отдельные
immutable trace records и явно stateful recorder — осознанные решения,
а не заявление о буквальном соблюдении всех рекомендаций книги.

## Фазы и критерии завершения

Текущий статус: базовый пакет и синхронное/асинхронное ядро реализованы;
compatibility table и candidate example добавлены. Полный перенос встроенных
specifications, conformance fixtures, type checker и packaging verification
остаются следующими этапами.

### 1. Зафиксировать поведенческий контракт

- Создать `docs/compatibility.md`: каждому public Swift capability назначить
  статус equivalent / adapted / deferred с причиной и проверяемыми примерами.
- Зафиксировать AND/OR/NOT, порядок вызовов, пустые коллекции, FirstMatch,
  fallback, metadata, falsey payloads, ошибки и async cancellation.
- Отдельно разобрать context defaults, границы времени и timezone semantics.
- Для macros, property wrappers и type erasure описать Python replacement
  либо явное отсутствие аналога. Не объявлять их перенесёнными автоматически.

Готовность: однозначный контракт и список расхождений до реализации.

### 2. Собрать пакет и синхронное ядро

- `pyproject.toml`, `src/specification_core/`, `py.typed`, `tests/`, README и LICENSE.
- Protocols, final concrete classes, predicates, константные правила,
  композиция, Returning и FirstMatch, явные outcomes и fallback.
- Никаких обязательных DSL, ORM, framework adapters или global context provider.
- Тесты на observed call order, отсутствие вызовов skipped branches,
  empty/no-match, первый победивший маршрут, payload `False`, `0`, `None`.

Готовность: sync tests и strict type checking проходят, публичный пример исполним.

### 3. Добавить trace, async и встроенные правила

- Trace tree: стабильные имена, parent IDs, satisfied/unsatisfied,
  selected/no_match, skipped, failed/cancelled. Не записывать candidate,
  result payload или exception message по умолчанию.
- Trace строится за один проход: диагностика не переисполняет predicates.
  Исключение из tracing подавляет subtree и сохраняет поведение правила.
- Async composition и AsyncFirstMatch вычисляют ветви последовательно;
  не запускать skipped branches как tasks. Изолировать параллельные evaluations.
- Перенести count/date/range/cooldown/event specifications и context behavior
  по таблице совместимости. Clock/context передавать явно.
- Timeline и прочие расширения Swift занести в compatibility matrix;
  если отложены, не заявлять полный feature parity первой версии.

Готовность: trace on/off дают одинаковые результаты и вызовы; tests проверяют
ошибки, cancellation, concurrency isolation и временные границы без sleep.

### 4. Доказать совместимость и удобство применения

- Подключить версионированные Rust fixtures с provenance и лицензией;
  сверить ожидаемую семантику с Swift, не переписывая expectations ради pass.
- Дополнить fixtures случаями из Swift tests для async, trace и адаптаций API.
- Сделать runnable candidate eligibility/routing example с именованными
  объектами правил, ручным approval и объяснением отказа. Данные синтетические,
  интеграция с реальным SpecHarvester — отдельная задача.
- Настроить pytest, strict mypy, Ruff и CI для поддерживаемых Python versions.
- Собрать wheel/sdist; установить wheel в чистое окружение, проверить import,
  runnable example и `pip check`.

Готовность: все принятые contracts покрыты проверками, пакет устанавливается,
README показывает реальный API, ограничения parity перечислены явно.

## Делегирование и ожидание

Использовать GPT-6 Luna / low для bounded subtasks. Главный агент владеет
архитектурой, интеграцией, Git и итоговой проверкой. На этапе плана один
read-only агент проверяет тестовые контракты; при реализации независимые
test/review задачи делегируются после фиксации API. Параллельная запись —
только с разделённым владением файлами или отдельными worktrees.

Долгие процессы сохраняются в одной session; ждать completion через event-aware
wait без короткого polling. Публикация в PyPI не входит в этот план.

## References

- Swift: `Core/Specification.swift`, `Core/DecisionSpec.swift`,
  `Specs/FirstMatchSpec.swift`, `Core/AsyncDecisionSpec.swift`,
  `Documentation.docc/Tracing.md` в соседнем SpecificationCore.
- Rust: `docs/src/guides/conformance.md` и fixtures v1.
- Elegant Objects: https://www.yegor256.com/elegant-objects.html
- Immutability: https://www.yegor256.com/2014/12/22/immutable-objects-not-dumb.html
- Python final: https://typing.python.org/en/latest/spec/qualifiers.html
