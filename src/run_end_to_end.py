from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yaml

from build_transitions import learn_transition_matrix, STATES
from simulate_markov import simulate_markov, occupancy_table


def _ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_config(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _initial_distribution_from_real(transitions_df: pd.DataFrame) -> np.ndarray:
    """
    Use the empirical distribution of "state" as init distribution (like "current conditions").
    """
    counts = transitions_df["state"].value_counts()
    dist = np.array([counts.get(s, 0) for s in STATES], dtype=float)
    if dist.sum() == 0:
        # fallback uniform
        return np.ones(len(STATES)) / len(STATES)
    return dist / dist.sum()


def main(config_path: str = "config/config.yaml") -> None:
    cfg = _load_config(config_path)
    out_dir = _ensure_dir("outputs")

    # 1) Learn from real-world Divvy data
    transitions_df, counts_df, probs_df = learn_transition_matrix(config_path)

    # 2) Build Markov simulation inputs
    P = probs_df.values.astype(float)

    # SAFETY: renormalize rows to sum exactly to 1 (handles tiny rounding issues)
    row_sums = P.sum(axis=1, keepdims=True)
    # If any row sum is 0 (no data for that state), fall back to self-loop
    zero_rows = (row_sums.squeeze() == 0)
    if zero_rows.any():
        for i, z in enumerate(zero_rows):
            if z:
                P[i, :] = 0.0
                P[i, i] = 1.0
        row_sums = P.sum(axis=1, keepdims=True)

    P = P / row_sums
    
    init_dist = _initial_distribution_from_real(transitions_df)

    n_entities = int(cfg["model"]["n_entities"])
    n_steps = int(cfg["model"]["n_steps"])
    seed = int(cfg["model"]["seed"])

    # 3) Simulate
    sim = simulate_markov(P, init_dist, n_entities, n_steps, seed)
    print("Min/Max state in simulated paths:", sim.paths.min(), sim.paths.max())
    occ = occupancy_table(sim.paths, STATES)

    # 4) Save outputs
    counts_df.to_csv(out_dir / "transition_counts_real.csv")
    probs_df.to_csv(out_dir / "transition_probs_real.csv")
    occ.to_csv(out_dir / "simulated_occupancy.csv", index=False)

    # 5) Plot
    plt.figure()
    for s in STATES:
        plt.plot(occ["time_step"], occ[s], label=s)
    plt.xlabel("Time Step")
    plt.ylabel("Fraction of Entities")
    plt.title("Simulated State Occupancy (Learned from Real Divvy Data)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_dir / "simulated_occupancy.png", dpi=150)
    plt.close()

    # 6) Simple report
    report = []
    report.append("# Divvy Markov Model (Real Data → Learned Transitions → Simulation)\n")
    report.append("## What this does\n")
    report.append("- Collects real Divvy GBFS station snapshots\n")
    report.append("- Converts availability into states: EMPTY/LOW/MEDIUM/HIGH\n")
    report.append("- Learns transition probabilities from historical state-to-state movement\n")
    report.append("- Simulates future evolution using a Markov chain\n\n")

    report.append("## Learned transition probabilities\n")
    report.append(probs_df.to_markdown())
    report.append("\n\n## Initial distribution (from real data)\n")
    init_series = pd.Series(init_dist, index=STATES, name="init_prob").reset_index().rename(columns={"index": "state"})
    report.append(init_series.to_markdown(index=False))
    report.append("\n\n## Simulated occupancy (first 10 steps)\n")
    report.append(occ.head(10).to_markdown(index=False))
    report.append("\n")

    (out_dir / "report.md").write_text("\n".join(report), encoding="utf-8")

    print("✅ End-to-end pipeline complete.")
    print(f"Outputs saved to: {out_dir.resolve()}")
    print("- transition_counts_real.csv")
    print("- transition_probs_real.csv")
    print("- simulated_occupancy.csv")
    print("- simulated_occupancy.png")
    print("- report.md")


if __name__ == "__main__":
    main()
