# Corrected gate accounting: tcc_calibration_confirmatory_v1

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: COMPLETED.
Declared jobs: 400; preserved attempts: 400; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 400 | 400 | 400 | 0 | 0 | 0 |
| ALL | sampler | 400 | 400 | 339 | 61 | 0 | 0 |
| ALL | ppc | 400 | 400 | 398 | 2 | 0 | 0 |
| ALL | joint | 400 | 400 | 337 | 63 | 0 | 0 |
| PUB-02 | provenance | 400 | 400 | 400 | 0 | 0 | 0 |
| PUB-02 | sampler | 400 | 400 | 339 | 61 | 0 | 0 |
| PUB-02 | ppc | 400 | 400 | 398 | 2 | 0 | 0 |
| PUB-02 | joint | 400 | 400 | 337 | 63 | 0 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.
