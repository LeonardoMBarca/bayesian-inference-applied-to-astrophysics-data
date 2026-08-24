# Inventário de runs

stored_gate_scientifically_interpretable records the gate value preserved in the run artifact. currently_scientifically_interpretable is a present-day inventory decision and is true only for a non-failed run whose stored gate passed on the current target Gold dataset. A passed stored gate on an older dataset remains historical rather than currently interpretable.

| model_name | run_id | target | max_r_hat | min_ess | divergences | bfmi_min | stored_gate_scientifically_interpretable | currently_scientifically_interpretable | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1_box_transit_baseline | hat_p_7_b | HAT-P-7 b | None | None | None | None | None | False | historical_ungated_not_currently_interpretable |
| M1_box_transit_baseline | 001_operational_metropolis | HAT-P-7 b | None | None | None | None | None | False | historical_ungated_not_currently_interpretable |
| M1_box_transit_baseline | 002_nuts_robust | HAT-P-7 b | 1.00088086 | 4553.6002094 | 0 | 1.1052624756536682 | None | False | historical_ungated_not_currently_interpretable |
| M3_bayesian_noise_injection | 001_nuts | HAT-P-7 b | 1.00135589 | 3952.28488274 | 0 | 0.9222825676187097 | None | False | historical_ungated_not_currently_interpretable |
| M5_bayesian_physical_transit | 001_nuts | HAT-P-7 b | 1.00312909 | 1595.87223522 | 0 | 0.8296934736762236 | None | False | historical_ungated_not_currently_interpretable |
| M5_bayesian_physical_transit | 001_nuts | Kepler-10 b | 1.00223414 | 1476.77896935 | 0 | 0.7717185800187982 | None | False | historical_ungated_not_currently_interpretable |
| M5_bayesian_physical_transit | scientific_001 | Kepler-10 b | 1.00508421 | 582.0676616 | 0 | None | False | False | stored_gate_rejected |
| M5_bayesian_physical_transit | scientific_002 | Kepler-10 b | 1.00508421 | 582.0676616 | 0 | 0.7317310172214905 | True | False | historical_gated_dataset_not_current |
| M5_bayesian_physical_transit | scientific_003 | Kepler-10 b | 1.00508421 | 582.0676616 | 0 | 0.7317310172214905 | True | True | current_scientifically_interpretable |
| M5_bayesian_physical_transit | sensitivity_001_catalog_tighter | Kepler-10 b | 1.00377887 | 616.52762201 | 0 | 0.8126776041632984 | True | False | historical_gated_dataset_not_current |
| M5_bayesian_physical_transit | sensitivity_001_weak | Kepler-10 b | 1.0045834 | 800.64801586 | 0 | 0.7471179922306367 | True | False | historical_gated_dataset_not_current |
| M5_bayesian_physical_transit | sensitivity_001_weak_interrupted | Kepler-10 b | None | None | None | None | None | False | failed_preserved_for_traceability |
| M5_bayesian_physical_transit | sensitivity_002_catalog_tighter | Kepler-10 b | 1.00377887 | 616.52762201 | 0 | 0.8126776041632984 | True | True | current_scientifically_interpretable |
| M5_bayesian_physical_transit | sensitivity_002_weak | Kepler-10 b | 1.0045834 | 800.64801586 | 0 | 0.7471179922306367 | True | True | current_scientifically_interpretable |
| M5_bayesian_physical_transit | smoke_003 | Kepler-10 b | None | None | None | None | None | False | failed_preserved_for_traceability |
| M5_bayesian_physical_transit | smoke_004 | Kepler-10 b | 3.10433584 | 3.64260666 | 0 | None | False | False | failed_preserved_for_traceability |
| M5_bayesian_physical_transit | smoke_005 | Kepler-10 b | 3.10433584 | 3.64260666 | 0 | None | False | False | stored_gate_rejected |
| M2_bayesian_predictive_phase_regression | 001_nuts | HAT-P-7 b | 1.00292448 | 2269.80467052 | 0 | 0.714672777534181 | None | False | historical_ungated_not_currently_interpretable |
| M3_bayesian_sensitivity | 001_nuts | HAT-P-7 b | 1.73410951 | 6.10245888 | 11 | 0.8281942729352045 | None | False | historical_ungated_not_currently_interpretable |
| M3_bayesian_trapezoid_transit | 001_nuts | HAT-P-7 b | 1.00107423 | 4212.34208408 | 0 | 0.8543011995144133 | None | False | historical_ungated_not_currently_interpretable |
