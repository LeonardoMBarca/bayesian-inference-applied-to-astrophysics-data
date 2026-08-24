# Artefatos de modelos

O estado atual usa a hierarquia
`models/bayesian_physical_transit/<target>/runs/<run_id>/`. O run validado é
`kepler_10_b/runs/scientific_003`; `model_config.json` e `run_status.json`
registram a decisão científica e o checksum do trace local.

Diretórios antigos sem o contrato `dataset_id` + checksum + gate, inclusive
`runs/001_nuts`, são snapshots históricos. Smoke runs `003` e `004` preservam
falhas explícitas; `smoke_005` comprova a rejeição por diagnósticos ruins.
Traces NetCDF são locais e ignorados pelo Git conforme `docs/STORAGE_POLICY.md`.
