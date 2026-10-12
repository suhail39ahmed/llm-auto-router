# Golden prompt set: `golden_prompts.jsonl`

This is the answer key the router is scored against. It has 100 prompts written the way real users talk. They state intent implicitly and avoid hint words like "SQL", "code", or "search", so the router has to work out what each prompt needs.

## Schema (one JSON object per line)
| field | type | meaning |
|---|---|---|
| id | `p001`–`p100` | unique id |
| prompt | string | the user's message, verbatim |
| category | string | simple, general, code, query, structured, reasoning, tool_rag, tool_sql, tool_web |
| expected_tier | cheap \| general \| balanced \| strong | the cheapest model that answers well |
| tool | null \| rag \| sql \| web | outside information needed before answering |
| rationale | string | why it got this label (`[tricky]` marks the hard-to-route cases) |

Tier → deployment: cheap = Phi-4-mini-instruct, general = mistral-small-2503, balanced = gpt-5-mini, strong = gpt-5.4.

## Labelling rubric: pick the cheapest tier that gets it right
- **cheap:** The answer is a fixed label, a short translation, a span copied from the input, a yes/no, or a single well-known fact. There's no explanation and nothing to get subtly wrong. Input length doesn't matter (a long message with a trivial ask is still cheap).
- **general:** Fluent language work: summarising, rewriting or changing tone, short drafting, light brainstorming, and explaining common concepts. Getting it wrong would be mildly embarrassing, not costly. Phi gave a wrong definition of "model routing" in the smoke test, so explanations start at general.
- **balanced:** The output has to be *exactly* correct and machine-checkable: a program, a shell command, a regex, a query, a cron expression, a JSON/YAML/CSV schema or conversion. This applies even when the user never says "code" or "SQL" (e.g. "who were our top 10 customers given this table").
- **strong:** Open-ended design, trade-offs under constraints, multi-step quantitative or diagnostic reasoning, and architecture critique. Prompts that are short but ambiguous and strategic ("should we go multi-cloud?") belong here, because the model has to reason about missing context.

## Tool rules (decided separately from the tier)
- **rag:** Asks about *our* internal policies, limits, runbooks, error codes, or procedures. Tier is usually general (the answer is in the docs); it goes up to strong if the retrieved rules then have to be applied to a scenario.
- **sql:** Asks for numbers about *our* company data (spend, customers, tickets, revenue). Tier is balanced because a query has to be generated; strong if the user also wants analysis.
- **web:** Anything about now: live prices, this week's news, last night's results. Tier is general.

## Counts
Non-tool tiers: cheap 25, general 25, balanced 20, strong 15. Tool: rag 5, sql 5, web 5.
Overall expected_tier including tool rows: cheap 25, general 34, balanced 24, strong 17.

## Tricky cases (short but hard, long but easy, ambiguous)
| id | prompt (truncated) | label | why |
|---|---|---|---|
| p023 | I've been going back and forth with my manager for weeks about whether | cheap | Long but the real ask is trivial yes/no |
| p024 | Here's the full customer message: 'Hi, I ordered the blue jacket in si | cheap | Long input, simple extraction |
| p025 | ok | cheap | One-word, acknowledgement only |
| p048 | why is the sky blue | general | Short but needs a real explanation, Phi tends to be shallow/wrong |
| p049 | what is model routing | general | Short definition; smoke test showed Phi gets it wrong |
| p050 | Here is our 600-word team newsletter draft [pasted]... honestly just f | general | Long input, easy edit |
| p053 | why does this return None? def add(a,b): a+b | balanced | Bug fix, short |
| p070 | cron for every weekday at 6:30am | balanced | Very short but needs exact syntax; Phi often wrong |
| p081 | should we go multi-cloud? | strong | Short but deeply context-dependent strategic question |
| p082 | why is our pipeline slow | strong | Short, ambiguous, needs diagnostic reasoning and clarifying questions |
| p083 | microservices or monolith for us | strong | Short but open-ended architecture trade-off |
| p090 | Does the trade we did yesterday — 8% of the fund in one tech small-cap | strong/rag | Policy lookup plus multi-rule reasoning |
| p095 | compare our cloud spend per active user over the last 4 quarters and t | strong/sql | Data pull plus analysis |
| p099 | who won the match last night | general/web | Ambiguous, current event; needs web |
