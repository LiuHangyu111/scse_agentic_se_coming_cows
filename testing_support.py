"""Small runtime helper for local Ollama smoke tests."""

import os


def allow_local_ollama() -> None:
    for variable in ("NO_PROXY", "no_proxy"):
        existing = os.environ.get(variable, "")
        hosts = [item for item in existing.split(",") if item]
        for host in ("127.0.0.1", "localhost"):
            if host not in hosts:
                hosts.append(host)
        os.environ[variable] = ",".join(hosts)
