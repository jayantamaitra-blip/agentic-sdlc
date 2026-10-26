# Agentic SDLC Prototype

A small interview-focused workflow that takes a software requirement through analysis, design, planning, implementation, testing and review. The demo requirement is a URL shortener with APIs, persistence and analytics.

## Workflow

`Analyst -> Architect -> Planner -> Coder -> Tester -> Reviewer`

- **Analyst** identifies ambiguities and records assumptions.
- **Architect** defines components, API contracts, persistence schema and trade-offs.
- **Planner** creates tasks and dependencies using the requirement, assumptions and approved design.
- **Coder** uses the design and plan to produce a runnable URL-shortener project under `output/generated_url_shortener/`.
- **Tester** executes the generated project's unit tests and records the real command, output and exit status.
- **Quality loop** runs the tests and a source-code inspection on each round. If either fails, captured test diagnostics and code-review findings are sent back to the Coder. There are at most three total validation/review rounds (initial run plus two repairs).
- **Reviewer** inspects Python syntax, expected implementation symbols, dangerous dynamic execution, f-string SQL queries, `shell=True`, HTTP/HTTPS URL validation, and the presence of core tests. It then checks the final test outcome, records known risks and writes a summary.

Each stage reads/writes the shared workflow state. The orchestrator enforces stage dependencies, supports bounded retries and asks for human approval at the analysis, design, plan and implementation gates.

## Setup

Requires Python 3.10 or newer. The orchestration prototype and generated URL shortener use only the Python standard library.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m unittest discover -s tests -v
python main.py
```

Type `y` when asked to approve each major stage. The generated service and its tests are written to `output/generated_url_shortener/`.

To run the generated service after the workflow completes:

```bash
cd output/generated_url_shortener
python shortener.py
```

It listens on `http://127.0.0.1:8000`.

## Generated URL-shortener API

- `POST /shorten` with JSON `{"url":"https://example.com"}` and optional `expires_in_days`.
- `GET /{code}` redirects to the original URL and records a click.
- `GET /stats/{code}` returns total clicks and counts by day.

Run its tests from the generated project directory:

```bash
python -m unittest discover -s tests -v
```

## Tests

The repository tests cover workflow dependency ordering, retry behavior, human rejection, task-graph validation, source-code inspection, review-triggered repairs and the three-round limit. The workflow also runs tests against the generated URL-shortener project and records their actual output and exit status for the Reviewer.

## Scope and limitations

This is an interview prototype, not a production deployment. The generated service does not include authentication, rate limiting, production-grade concurrency or deployment infrastructure. Planned tasks inform the implementation stage, but the prototype does not yet dispatch every individual planned task as a separate worker. The current Coder uses a deterministic reference implementation; its repair action regenerates that scaffold after recording the test/review diagnostics, rather than using an LLM to make arbitrary targeted edits. The code reviewer uses lightweight deterministic checks, not a complete security audit. The loop control is real and bounded, but fully adaptive code repair requires a model-driven Coder.
