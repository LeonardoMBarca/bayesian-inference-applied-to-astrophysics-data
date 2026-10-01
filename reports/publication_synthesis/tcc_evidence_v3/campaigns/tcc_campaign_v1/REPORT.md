# Corrected gate accounting: tcc_campaign_v1

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: COMPLETED.
Declared jobs: 117; preserved attempts: 118; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 117 | 117 | 111 | 6 | 0 | 0 |
| ALL | sampler | 117 | 111 | 81 | 30 | 6 | 0 |
| ALL | ppc | 117 | 111 | 88 | 23 | 6 | 0 |
| ALL | joint | 117 | 111 | 66 | 45 | 6 | 0 |
| PUB-02 | provenance | 80 | 80 | 80 | 0 | 0 | 0 |
| PUB-02 | sampler | 80 | 80 | 66 | 14 | 0 | 0 |
| PUB-02 | ppc | 80 | 80 | 79 | 1 | 0 | 0 |
| PUB-02 | joint | 80 | 80 | 65 | 15 | 0 | 0 |
| PUB-03 | provenance | 2 | 2 | 2 | 0 | 0 | 0 |
| PUB-03 | sampler | 2 | 2 | 1 | 1 | 0 | 0 |
| PUB-03 | ppc | 2 | 2 | 0 | 2 | 0 | 0 |
| PUB-03 | joint | 2 | 2 | 0 | 2 | 0 | 0 |
| PUB-04 | provenance | 30 | 30 | 24 | 6 | 0 | 0 |
| PUB-04 | sampler | 30 | 24 | 10 | 14 | 6 | 0 |
| PUB-04 | ppc | 30 | 24 | 9 | 15 | 6 | 0 |
| PUB-04 | joint | 30 | 24 | 1 | 23 | 6 | 0 |
| PUB-05 | provenance | 5 | 5 | 5 | 0 | 0 | 0 |
| PUB-05 | sampler | 5 | 5 | 4 | 1 | 0 | 0 |
| PUB-05 | ppc | 5 | 5 | 0 | 5 | 0 | 0 |
| PUB-05 | joint | 5 | 5 | 0 | 5 | 0 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.
