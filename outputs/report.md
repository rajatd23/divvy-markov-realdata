# Divvy Markov Model (Real Data → Learned Transitions → Simulation)

## What this does

- Collects real Divvy GBFS station snapshots

- Converts availability into states: EMPTY/LOW/MEDIUM/HIGH

- Learns transition probabilities from historical state-to-state movement

- Simulates future evolution using a Markov chain


## Learned transition probabilities

| from_state   |      EMPTY |        LOW |   MEDIUM |   HIGH |
|:-------------|-----------:|-----------:|---------:|-------:|
| EMPTY        | 0.998884   | 0.00111607 | 0        |      0 |
| LOW          | 0          | 1          | 0        |      0 |
| MEDIUM       | 0.00189394 | 0          | 0.998106 |      0 |
| HIGH         | 0          | 0          | 0        |      1 |


## Initial distribution (from real data)

| state   |   init_prob |
|:--------|------------:|
| EMPTY   |   0.467153  |
| LOW     |   0.205944  |
| MEDIUM  |   0.275287  |
| HIGH    |   0.0516163 |


## Simulated occupancy (first 10 steps)

|   time_step |   EMPTY |    LOW |   MEDIUM |   HIGH |
|------------:|--------:|-------:|---------:|-------:|
|           0 |  0.4738 | 0.2058 |   0.2696 | 0.0508 |
|           1 |  0.4738 | 0.2064 |   0.269  | 0.0508 |
|           2 |  0.4734 | 0.2072 |   0.2686 | 0.0508 |
|           3 |  0.474  | 0.2076 |   0.2676 | 0.0508 |
|           4 |  0.474  | 0.208  |   0.2672 | 0.0508 |
|           5 |  0.4744 | 0.2082 |   0.2666 | 0.0508 |
|           6 |  0.4744 | 0.209  |   0.2658 | 0.0508 |
|           7 |  0.4746 | 0.2092 |   0.2654 | 0.0508 |
|           8 |  0.4752 | 0.2096 |   0.2644 | 0.0508 |
|           9 |  0.4758 | 0.21   |   0.2634 | 0.0508 |

