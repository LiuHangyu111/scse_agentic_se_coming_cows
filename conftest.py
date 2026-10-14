"""Pytest configuration.

test_analyst.py, test_planner.py and test_developer.py are Level 1 pipeline
smoke tests required by the Testing assignment: they run the real agents
against the real local model. They are therefore excluded from auto-collection
and must be executed explicitly, one after another:

    .venv\\Scripts\\python.exe test_analyst.py
    .venv\\Scripts\\python.exe test_planner.py
    .venv\\Scripts\\python.exe test_developer.py
"""

collect_ignore_glob = [
    "test_analyst.py",
    "test_planner.py",
    "test_developer.py",
]
