# Corrected gate accounting: tcc_numerical_complement_v3

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: STOPPED.
Declared jobs: 24; preserved attempts: 13; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 24 | 13 | 13 | 0 | 11 | 0 |
| ALL | sampler | 24 | 13 | 11 | 2 | 11 | 0 |
| ALL | ppc | 24 | 6 | 6 | 0 | 11 | 7 |
| ALL | joint | 24 | 6 | 5 | 1 | 11 | 7 |
| PUB-02 | provenance | 12 | 12 | 12 | 0 | 0 | 0 |
| PUB-02 | sampler | 12 | 12 | 10 | 2 | 0 | 0 |
| PUB-02 | ppc | 12 | 6 | 6 | 0 | 0 | 6 |
| PUB-02 | joint | 12 | 6 | 5 | 1 | 0 | 6 |
| PUB-03 | provenance | 3 | 1 | 1 | 0 | 2 | 0 |
| PUB-03 | sampler | 3 | 1 | 1 | 0 | 2 | 0 |
| PUB-03 | ppc | 3 | 0 | 0 | 0 | 2 | 1 |
| PUB-03 | joint | 3 | 0 | 0 | 0 | 2 | 1 |
| PUB-04 | provenance | 9 | 0 | 0 | 0 | 9 | 0 |
| PUB-04 | sampler | 9 | 0 | 0 | 0 | 9 | 0 |
| PUB-04 | ppc | 9 | 0 | 0 | 0 | 9 | 0 |
| PUB-04 | joint | 9 | 0 | 0 | 0 | 9 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.
