from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SimulationResult:
    paths: np.ndarray  # (n_entities, n_steps+1)


def simulate_markov(P: np.ndarray, init_dist: np.ndarray, n_entities: int, n_steps: int, seed: int) -> SimulationResult:
    rng = np.random.default_rng(seed)
    n_states = P.shape[0]

    # initial states
    cur = rng.choice(n_states, size=n_entities, p=init_dist)
    paths = np.zeros((n_entities, n_steps + 1), dtype=np.int32)
    paths[:, 0] = cur

    cdf = np.cumsum(P, axis=1)

    for t in range(1, n_steps + 1):
        u = rng.random(n_entities)
        nxt = np.empty_like(cur)

        for s in range(n_states):
            idx = np.where(cur == s)[0]
            if idx.size == 0:
                continue

            sampled = np.searchsorted(cdf[s], u[idx], side="right")

            # SAFETY: if searchsorted returns n_states (possible if cdf ends slightly < 1),
            # clamp it to the last valid index
            sampled = np.clip(sampled, 0, n_states - 1)

            nxt[idx] = sampled

        # SAFETY: ensure no negatives
        nxt = np.clip(nxt, 0, n_states - 1)

        cur = nxt
        paths[:, t] = cur

    return SimulationResult(paths=paths)


def occupancy_table(paths: np.ndarray, state_names: List[str]) -> pd.DataFrame:
    n_entities, T = paths.shape
    n_states = len(state_names)

    rows = []
    for t in range(T):
        c = np.bincount(paths[:, t], minlength=n_states) / n_entities
        row = {"time_step": t}
        for i, s in enumerate(state_names):
            row[s] = float(c[i])
        rows.append(row)

    return pd.DataFrame(rows)
