# Architecture Overview

## Components

- **Orchestrator** (`src/orchestrator/runner.py`): runs tasks in dependency
  order, retries failures, and pauses for human approval.
- **Task graph checker** (`src/orchestrator/graph.py`): validates the planner's
  tasks (no duplicate ids, no unknown or circular dependencies) and groups them
  into waves.
- **Shared state** (`src/orchestrator/state.py`): one dictionary holding the
  requirement, assumptions, tasks, design and results.
- **Agents** (`src/agents/`): Analyst, Planner and Architect.
- **Model gateway** (`src/agents/llm.py`): the single place agents ask a model.
  Currently returns prepared answers.

## Control flow

    requirement
        |
        v
    Analyst  --(human approves)-->  Planner  --(human approves)-->  Architect
                                                                        |
                                                        (human approves)|
                                                                        v
                                                              design saved in state

Each step reads from the shared state, adds its result, and the orchestrator
moves on only when every dependency has finished.

## Error handling and recovery

- A failing step is retried up to `max_retries` times, then the workflow stops
  with a clear error.
- Agent output is validated before it is saved to state.
- A human rejection stops the workflow immediately.

## Controlled autonomy

Agents run their steps without prompting. A human must approve the analysis,
the plan and the design before the workflow continues.

## URL shortener design (produced by the Architect agent)

- Endpoints: `POST /shorten`, `GET /{code}` (redirect), `GET /stats/{code}`.
- Tables: `links` (id, code, original_url, created_at, expires_at) and
  `clicks` (id, link_id, clicked_at, referrer).
- Short codes: base62 encoding of the row id. No collisions. Trade-off: codes
  can be guessed in order.
- Storage: SQLite for easy setup. Trade-off: a single writer; move to
  PostgreSQL for real scale.
- Redirect: HTTP 302 so every click is counted. Trade-off: more load than a
  cached 301.
- Analytics: clicks stored in a separate table. Trade-off: it grows fast and
  needs archiving.

## Risks and trade-offs

- Mock model means the generated design is not tested against real model
  variability.
- Sequential execution is slower than parallel waves.
- No authentication or rate limiting in version one.
- Code generation, test generation and the final summary are not built yet.