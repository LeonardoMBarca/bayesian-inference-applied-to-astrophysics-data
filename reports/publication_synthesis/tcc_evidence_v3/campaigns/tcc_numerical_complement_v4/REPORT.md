# Corrected gate accounting: tcc_numerical_complement_v4

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: COMPLETED.
Declared jobs: 24; preserved attempts: 24; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 24 | 24 | 24 | 0 | 0 | 0 |
| ALL | sampler | 24 | 24 | 13 | 11 | 0 | 0 |
| ALL | ppc | 24 | 24 | 21 | 3 | 0 | 0 |
| ALL | joint | 24 | 24 | 10 | 14 | 0 | 0 |
| PUB-02 | provenance | 12 | 12 | 12 | 0 | 0 | 0 |
| PUB-02 | sampler | 12 | 12 | 7 | 5 | 0 | 0 |
| PUB-02 | ppc | 12 | 12 | 12 | 0 | 0 | 0 |
| PUB-02 | joint | 12 | 12 | 7 | 5 | 0 | 0 |
| PUB-03 | provenance | 3 | 3 | 3 | 0 | 0 | 0 |
| PUB-03 | sampler | 3 | 3 | 3 | 0 | 0 | 0 |
| PUB-03 | ppc | 3 | 3 | 0 | 3 | 0 | 0 |
| PUB-03 | joint | 3 | 3 | 0 | 3 | 0 | 0 |
| PUB-04 | provenance | 9 | 9 | 9 | 0 | 0 | 0 |
| PUB-04 | sampler | 9 | 9 | 3 | 6 | 0 | 0 |
| PUB-04 | ppc | 9 | 9 | 9 | 0 | 0 | 0 |
| PUB-04 | joint | 9 | 9 | 3 | 6 | 0 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.
