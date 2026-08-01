"""Hand-rolled Prometheus metrics (no external dependency).

Provides counters and histograms with thread-safe access and text-format
exposition compatible with Prometheus scraping.
"""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Generator


class _Counter:
    """Thread-safe counter with labels."""

    def __init__(self, name: str, help_text: str, label_names: tuple[str, ...] = ()):
        self.name = name
        self.help_text = help_text
        self.label_names = label_names
        self._lock = threading.Lock()
        self._values: dict[tuple[str, ...], float] = {}

    def inc(self, labels: dict[str, str] | None = None, amount: float = 1.0) -> None:
        key = self._key(labels)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + amount

    def _key(self, labels: dict[str, str] | None) -> tuple[str, ...]:
        if not self.label_names:
            return ()
        labels = labels or {}
        return tuple(labels.get(n, "") for n in self.label_names)

    def expose(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} counter",
        ]
        with self._lock:
            for key, val in sorted(self._values.items()):
                if self.label_names:
                    label_str = ",".join(
                        f'{n}="{v}"' for n, v in zip(self.label_names, key)
                    )
                    lines.append(f"{self.name}{{{label_str}}} {val}")
                else:
                    lines.append(f"{self.name} {val}")
        return lines


class _Histogram:
    """Thread-safe histogram with labels and fixed buckets."""

    def __init__(
        self,
        name: str,
        help_text: str,
        buckets: tuple[float, ...] = (0.1, 0.5, 1, 5, 10),
        label_names: tuple[str, ...] = (),
    ):
        self.name = name
        self.help_text = help_text
        self.buckets = sorted(buckets)
        self.label_names = label_names
        self._lock = threading.Lock()
        # key -> {bucket_le: count, "+Inf": count, "_sum": float, "_count": int}
        self._data: dict[tuple[str, ...], dict[str, float]] = {}

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(labels)
        with self._lock:
            if key not in self._data:
                self._data[key] = {str(b): 0 for b in self.buckets}
                self._data[key]["+Inf"] = 0
                self._data[key]["_sum"] = 0.0
                self._data[key]["_count"] = 0
            entry = self._data[key]
            for b in self.buckets:
                if value <= b:
                    entry[str(b)] += 1
            entry["+Inf"] += 1
            entry["_sum"] += value
            entry["_count"] += 1

    def _key(self, labels: dict[str, str] | None) -> tuple[str, ...]:
        if not self.label_names:
            return ()
        labels = labels or {}
        return tuple(labels.get(n, "") for n in self.label_names)

    def expose(self) -> list[str]:
        lines = [
            f"# HELP {self.name} {self.help_text}",
            f"# TYPE {self.name} histogram",
        ]
        with self._lock:
            for key in sorted(self._data.keys()):
                entry = self._data[key]
                label_prefix = ""
                if self.label_names:
                    label_prefix = ",".join(
                        f'{n}="{v}"' for n, v in zip(self.label_names, key)
                    )
                cumulative = 0
                for b in self.buckets:
                    cumulative += int(entry.get(str(b), 0))
                    if label_prefix:
                        lines.append(
                            f'{self.name}_bucket{{{label_prefix},le="{b}"}} {cumulative}'
                        )
                    else:
                        lines.append(f'{self.name}_bucket{{le="{b}"}} {cumulative}')
                inf_count = int(entry.get("+Inf", 0))
                if label_prefix:
                    lines.append(f'{self.name}_bucket{{{label_prefix},le="+Inf"}} {inf_count}')
                    lines.append(f"{self.name}_sum{{{label_prefix}}} {entry['_sum']:.6f}")
                    lines.append(f"{self.name}_count{{{label_prefix}}} {int(entry['_count'])}")
                else:
                    lines.append(f'{self.name}_bucket{{le="+Inf"}} {inf_count}')
                    lines.append(f"{self.name}_sum {entry['_sum']:.6f}")
                    lines.append(f"{self.name}_count {int(entry['_count'])}")
        return lines


class MetricsRegistry:
    """Central registry for all application metrics."""

    def __init__(self):
        self._metrics: list[_Counter | _Histogram] = []

    def counter(self, name: str, help_text: str, label_names: tuple[str, ...] = ()) -> _Counter:
        c = _Counter(name, help_text, label_names)
        self._metrics.append(c)
        return c

    def histogram(
        self, name: str, help_text: str, buckets: tuple[float, ...] = (0.1, 0.5, 1, 5, 10), label_names: tuple[str, ...] = ()
    ) -> _Histogram:
        h = _Histogram(name, help_text, buckets, label_names)
        self._metrics.append(h)
        return h

    def expose(self) -> str:
        lines: list[str] = []
        for m in self._metrics:
            lines.extend(m.expose())
        return "\n".join(lines) + "\n"


# --- Global registry with application metrics ---
registry = MetricsRegistry()

m1_parse_total = registry.counter(
    "m1_parse_total", "Total M1 parse requests", ("format", "status")
)
m1_parse_duration_seconds = registry.histogram(
    "m1_parse_duration_seconds",
    "M1 parse duration",
    buckets=(0.1, 0.5, 1, 5, 10, 30, 60, 120),
    label_names=("format",),
)
m2_qa_total = registry.counter(
    "m2_qa_total", "Total M2 QA requests", ("status",)
)
m2_qa_duration_seconds = registry.histogram(
    "m2_qa_duration_seconds",
    "M2 QA duration",
    buckets=(0.1, 0.5, 1, 2, 5, 10),
)
llm_tokens_total = registry.counter(
    "llm_tokens_total", "Total LLM tokens consumed", ("model",)
)
rerank_duration_seconds = registry.histogram(
    "rerank_duration_seconds",
    "Rerank duration",
    buckets=(0.05, 0.1, 0.2, 0.5, 1),
)


@contextmanager
def time_histogram(histogram: _Histogram, labels: dict[str, str] | None = None) -> Generator[None, None, None]:
    """Context manager to time a block and observe into a histogram."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        histogram.observe(elapsed, labels)
