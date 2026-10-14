# SCSE 26: Final Project Submission

This repository contains the group project's analyst, planner, developer, test,
simulation, and review agents, plus the testing and integration exercises. The teacher's
`test_irsim_with_agent.py` and `run_visual.sh` are kept unchanged. The
`world_difficult.yaml` file is a copy of the supplied `world_hard.yaml` because
the assignment names the third world “difficult.”

## Final submission contents

- Agent and orchestration source: `analyst_agent.py`, `planner_agent.py`,
  `developer_agent.py`, `test_agent.py`, `reviewer_agent.py`,
  `reviewer_benchmark_agent.py`, `main.py`, and supporting scripts.
- All generated files: `generated/navigation_logic.py`,
  `generated/navigation_logic_revised.py`, and the generated test files.
- All saved artifacts: `artifacts/`, including requirements, plan, navigation
  logic, testing evidence, simulation reports, benchmark results, and reviews.
- Complete pipeline trace: `trace.log`.

The final submission page asks for this repository link. The separate
“Project – Testing” handout is an earlier practice exercise whose source and
evidence are included here as part of the complete project.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-integration.txt
ollama pull qwen3:8b
```

If another local model is available, set `QWEN_MODEL` to its Ollama name.

## Full pipeline

```bash
QWEN_MODEL=qwen3:8b .venv/bin/python main.py
```

For unattended runs without a GUI, add `MPLBACKEND=Agg`. This project was
verified locally with `QWEN_MODEL=qwen3:0.6b`; the orchestrator rejects unsafe
model output and uses a validated reference implementation if needed. The
rejected test draft is similarly replaced with exhaustive tests and noted in
`trace.log`.

The orchestrator runs the analyst, planner, developer, test agent, exhaustive
simulation, simulation reviewer, four-world IR-SIM benchmark, and benchmark
reviewer. It then asks the developer agent for one revised version using the
reviews and benchmark, and retests and rebenchmarks that version. All stages
are recorded in `trace.log`. Reports are written under `artifacts/`.

The previous `navigate(front_blocked, left_blocked, right_blocked,
goal_direction)` API remains in the original `navigation_logic.py`. Pipeline
agent outputs are saved as new files in `artifacts/`. The generated
`decide_next_move(state)` adapter used by IR-SIM is in
`generated/navigation_logic.py`.

## Individual checks

```bash
.venv/bin/python -m pytest -q test_generated_navigation_logic.py generated/test_navigation_agent.py generated/test_navigation_agent_revised.py
.venv/bin/python runner.py
.venv/bin/python benchmark_irsim.py
./run_visual.sh irsim_worlds/world_easy.yaml
./run_visual.sh irsim_worlds/world_medium.yaml
./run_visual.sh irsim_worlds/world_difficult.yaml
./run_visual.sh irsim_worlds/world_custom.yaml
```

For the four visual runs, activate `.venv` first so the unchanged shell script
uses the correct Python interpreter. IR-SIM reports use 300 maximum steps and
count a successful run as efficient when it takes at most 200 steps, as defined
by the supplied simulator.

## Testing exercise

Run the three real agent smoke tests in order. They use the original `brief.txt`,
then each preceding artifact, and print their validated results:

```bash
QWEN_MODEL=qwen3:8b .venv/bin/python test_analyst.py
QWEN_MODEL=qwen3:8b .venv/bin/python test_planner.py
QWEN_MODEL=qwen3:8b .venv/bin/python test_developer.py
.venv/bin/python -m pytest -q test_generated_navigation_logic.py
.venv/bin/python verify_tests_detect_bug.py
```

The tests call `decide_next_move(state)` for all 64 combinations of six sensor
flags, plus invalid inputs. The bug check runs the same tests against an
isolated copy that wrongly returns `RIGHT` while right is blocked. The test
must fail, and the unmodified source must pass. Evidence is saved in
`artifacts/testing_evidence.json`.

The local validation run used `qwen3:0.6b` because `qwen3:8b` was unavailable.
The smaller model produced a vague plan and unsafe code, so the planner and
developer validators rejected those drafts and used explicit safe references.
These fallbacks are logged; the resulting code is tested and benchmarked rather
than presented as a successful raw model output.
