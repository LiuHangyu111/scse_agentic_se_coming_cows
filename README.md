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
verified locally with `QWEN_MODEL=qwen3:8b`; the orchestrator rejects unsafe
model output and uses a validated reference implementation if needed. The
rejected test draft is similarly replaced with exhaustive tests and noted in
`trace.log`. See the Testing assignment section below for how the `qwen3:0.6b`
run differs.

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

## Testing assignment

Level 1 smoke tests run the real agents against the real local model, one after
another. They use the original `brief.txt`, then each preceding artifact, and
print their validated results:

```bash
QWEN_MODEL=qwen3:8b .venv/bin/python test_analyst.py     # -> artifacts/requirements.json
QWEN_MODEL=qwen3:8b .venv/bin/python test_planner.py     # -> artifacts/plan.json
QWEN_MODEL=qwen3:8b .venv/bin/python test_developer.py   # -> artifacts/navigation_logic.py
```

These three are standalone runners, so `pytest.ini` and `conftest.py` keep them
out of `pytest` auto-collection. Level 2 behavioural testing is:

```bash
.venv/bin/python -m pytest -q test_generated_navigation_logic.py
.venv/bin/python verify_tests_detect_bug.py
```

The behavioural tests call `decide_next_move(state)` from
`artifacts/navigation_logic.py` for all 64 combinations of the six sensor flags,
plus invalid inputs, and check that it matches `generated/navigation_logic.py`.
`verify_tests_detect_bug.py` then runs the same tests against an isolated copy
that wrongly returns `RIGHT` while right is blocked: the test must fail, and the
unmodified source must pass. Evidence is saved in
`artifacts/testing_evidence.json`, and the tracked navigation logic is never
modified because the mutant is a temporary copy.

The local validation run documented in `trace.log` used `qwen3:8b`. With that
model the Analyst, Planner and Developer drafts all pass their validators and are
used directly; the Test Agent draft is still rejected as invalid Python and is
replaced by the exhaustive tests, which is recorded as a warning in `trace.log`.
With the smaller `qwen3:0.6b` the planner produced a vague plan and the developer
produced unsafe code, so both validators rejected those drafts and used the
explicit safe references. Those fallbacks are logged rather than presented as a
successful raw model output.

## Windows notes

```powershell
uv venv --python 3.12 .venv
$env:UV_LINK_MODE = "copy"   # required when the project sits in a OneDrive folder
uv pip install --python .\.venv\Scripts\python.exe -r requirements-integration.txt
$env:QWEN_MODEL = "qwen3:8b"
$env:MPLBACKEND = "Agg"      # no GUI needed for the benchmark
```

`run_visual.sh` is a shell script and is not run on Windows; the four worlds are
checked headlessly by calling the unchanged `test_irsim_with_agent.py` directly
for each world file.
