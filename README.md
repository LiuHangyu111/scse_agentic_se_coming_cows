# SCSE 26: Integration and Simulation

This repository extends the previous analyst, planner, and developer agents with
the teacher's integration and simulation exercise. The teacher's
`test_irsim_with_agent.py` and `run_visual.sh` are kept unchanged. The
`world_difficult.yaml` file is a copy of the supplied `world_hard.yaml` because
the assignment names the third world “difficult.”

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
.venv/bin/python -m pytest -q test_generated_navigation_logic.py generated/test_navigation_agent.py
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
another, and each one saves and displays its artifact:

```bash
.venv/bin/python test_analyst.py     # -> artifacts/requirements.json
.venv/bin/python test_planner.py     # -> artifacts/plan.json
.venv/bin/python test_developer.py   # -> generated/navigation_logic.py
```

These three are standalone runners, so `pytest.ini` and `conftest.py` keep them
out of `pytest` auto-collection. Level 2 behavioural testing is `pytest -q`, and
`verify_tests_detect_bug.py` checks that those tests are actually able to fail:
it injects three separate bugs into `generated/navigation_logic.py`, confirms the
suite turns red, then restores the file and verifies its SHA-256 is unchanged.

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

