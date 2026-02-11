from __future__ import annotations

import threading

_lock = threading.Lock()
_metrics: dict[str, int] = {
    "events_published_total": 0,
    "events_consumed_total": 0,
    "dlq_total": 0,
}


def inc_metric(name: str, value: int = 1) -> None:
    with _lock:
        _metrics[name] = _metrics.get(name, 0) + value


def render_metrics() -> str:
    with _lock:
        lines = [f"{key} {value}" for key, value in _metrics.items()]
    return "\n".join(lines) + "\n"
