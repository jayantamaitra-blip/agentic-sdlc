# Agentic SDLC Prototype

A small workflow system that takes a software requirement and moves it through
analysis, planning and design, with a human approving key steps.

Built as an interview assignment. The demo requirement is:
"Build a scalable URL shortener service with APIs, persistence, and analytics."

## Status: what works and what does not

Working:
- Workflow engine with task dependencies, retries and human approval gates
- Shared state ("notebook") passed between agents
- Analyst agent: lists unclear points and assumptions
- Planner agent: breaks the requirement into tasks with dependencies, then
  groups them into waves that could run in parallel
- Architect agent: produces components, API contract, database schema, and
  design decisions with trade-offs
- Guardrails: task graph validation, design completeness check
- [OPTIONAL, only if your Coder works] Coder agent: writes a URL shortener
  service into `output/url_shortener/` after safety checks
- Unit tests for the orchestrator and the task graph

Not built (see Limitations): Tester, Risk Reviewer and Summarizer agents,
real brownfield and ambiguous-requirement examples, and a live model connection.

## How it works

Think of it like a CI/CD pipeline for writing software:

| Pipeline idea | In this project |
|---|---|
| Pipeline engine | Orchestrator (`src/orchestrator/runner.py`) |
| Stage | Agent (one file per agent in `src/agents/`) |
| `dependsOn` | `depends_on` on each task |
| Retry on failure | `max_retries` in the runner |
| Manual approval gate | `needs_approval=True`, asks y/n in the terminal |

Flow: Analyze -> Plan -> Design [-> Code]. Plan and Design wait for human approval.

## Setup

Requires Python 3.10 or newer. The core system uses only the standard library.

```
git clone <your-repo-url>
cd agentic-sdlc
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
python main.py
```
Type `y` at each approval prompt. Type `n` to see the rejection path.

Run the tests:
```
python -m unittest discover -s tests -v
```

## Mock mode (important)

The agents call one function, `ask_model`, in `src/agents/llm.py`. It currently
returns prepared answers for the URL shortener. No real AI model is connected
yet. This keeps the demo runnable without an API key and makes the workflow
logic easy to test. A real model call would replace the body of `ask_model`
without changing the agents.

## Failure scenarios checked

- A task that fails once is retried and succeeds on attempt 2.
- A task that keeps failing stops the workflow after the retry limit.
- A circular dependency between tasks is detected and rejected.
- A task depending on an unknown task is rejected.
- A design missing a trade-off or API field fails validation.
- A human typing `n` at an approval gate stops the workflow.

## Key decisions

- **Shared state dictionary:** simple, easy to inspect, every agent reads and
  writes the same place. Trade-off: no type checking between agents.
- **Waves for parallelism:** the planner output is grouped into waves of
  independent tasks. The runner currently executes them one after another;
  the waves show where parallel execution would be safe.
- **Validate before trusting:** agent output is checked (task graph, design
  completeness) before it enters shared state.
- **Mock model behind one function:** easy to swap for a real model later.

## Limitations

- No live model connection; agents return prepared answers.
- Tester, Risk Reviewer and Summarizer agents are not implemented, so there is
  no automated generated-test run and no final engineering summary yet.
- Only the greenfield URL shortener scenario is demonstrated. Brownfield
  (impact analysis on an existing codebase) and ambiguous-requirement examples
  are not implemented.
- Tasks run sequentially even where waves allow parallel work.
- Retries cannot fix a deterministic coding error; they help with temporary
  failures.

## Next steps

1. Add the Tester agent: write tests, run them, retry on failure.
2. Add the Risk Reviewer and Summarizer to produce the final summary.
3. Add a brownfield example with impact analysis and an ambiguous example.
4. Connect a real model and run tasks in a wave in parallel.

## AI assistance

I used an AI assistant to help plan the approach and review code. I typed,
ran and tested the code myself and can explain each part.