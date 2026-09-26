# Isolated independent-benchmark environment

This environment is separate from the validated M5 environment. No juliet-only
dependency is installed into `mc3`. It targets Linux x86_64 / WSL2 Ubuntu 24.04,
Python 3.12, juliet 2.2.10 and batman-package 2.5.3. Exact resolved distributions
are captured in `benchmark-requirements.txt` by the inspection command below;
that lock is authoritative, not a future unconstrained `pip install juliet`.

## Installation history

The initial system Python 3.12.3 `venv` attempt failed because `ensurepip` was
unavailable. Bootstrapping pip into that isolated partial venv then failed when
building UltraNest: system Python development headers (`Python.h`) were absent.
Neither failure changed the canonical environment. The unused partial venv is
not a scientific run or a validated environment and was not silently deleted.

A distinct conda prefix, `publication-benchmark-conda`, was created with Python
3.12.14 and its development headers. This avoids requiring system-wide package
changes or contaminating M5. UltraNest is an upstream juliet dependency even
when the selected final sampler is dynesty; it requires a native build here.

## Recreate and inspect

Run in a **new, empty** environment. Do not reuse the M5 prefix. A native C/C++
compiler and Python headers are required for source distributions. The tested
host provides them through Ubuntu and the separate conda Python package.

```bash
conda create --prefix /path/to/new-benchmark python=3.12.14 pip
/path/to/new-benchmark/bin/python -m pip install -r publication/environments/benchmark-requirements.txt
/path/to/new-benchmark/bin/python -m pip check
/path/to/new-benchmark/bin/python scripts/inspect_benchmark_environment.py \
  --output-directory /path/to/new-environment-capture
/path/to/new-benchmark/bin/python scripts/validate_benchmark_adapter.py \
  --validate-fixture publication/engineering/benchmark_forward_fixture_v1.json \
  --output /path/to/new-adapter-check.json
```

The inspector refuses to overwrite existing environment captures. The numeric
check refuses to overwrite outputs. Compare package versions, source checksums
and contract-check outcomes, not machine-specific prefix names. Conda's base
runtime package URLs are captured separately in `benchmark-conda-explicit.txt`;
pip's resolved distributions and archive hashes are in the environment JSON.

The dependency inventory is a full installed-distribution freeze (including
pip, setuptools and wheel), normalized to `name==version` so conda's local
build paths are not mistaken for portable package requirements. The metadata
records exact source files for juliet and batman. Source-archive hashes do not
prove bit-for-bit native build reproducibility; compiler/build-backend identity
and a future clean-room rebuild remain relevant limitations.

## Meaning of the engineering checks

The canonical environment generates three deterministic *forward-model*
fixtures (deep/long cadence, shallow/short cadence, grazing/long cadence).
The isolated environment evaluates them with batman. These are **not** final
injection/recovery replicates, posterior benchmark evidence or calibration.

The installed-juliet contract check separately evaluates a 60-row,
heteroscedastic, two-exposure dataset without running a sampler. It checks:

- shared q1/q2, white jitter and additive constant across technical instruments;
- baseline mapping `B=1+theta0`, fixed dilution 1 and mflux 0;
- input errors in relative flux and photometric jitter in ppm;
- the normalized Gaussian likelihood against an analytic evaluation;
- half-normal jitter quantiles via the installed truncated-normal transform;
- dynesty's documented RNG-argument presence (not full sampler reproducibility).

The subsequent tiny worker smoke found that juliet 2.2.10's constructor
introspection silently drops `rstate` with dynesty 3.1.0. The worker therefore
uses an explicit-RNG subclass that delegates unchanged to installed dynesty
and restores the original class afterward. It also replaces only the
*canonical artifact* resampling with a separately seeded resample of the raw
weighted results; native juliet outputs remain preserved and noncanonical.
See `docs/publication/BENCHMARK_ENGINEERING_REPORT.md` for the preserved failed
v1 smoke and reproducible v2 smoke. No installed package source is patched.

Exposure duration remains physical metadata. The adapter contracts batman's
endpoint quadrature span by `(n-1)/n` to reproduce M5's midpoint-Riemann nodes
at the same odd number `n` of evaluations. This is a declared numerical-stencil
mapping, not an unreported cadence change. Exact exposure groups are retained;
the adapter refuses more than 32 groups instead of silently averaging them.

All sampler claims remain pending a committed PUB-03 final protocol. A passing
forward/likelihood adapter check cannot establish posterior convergence,
external posterior agreement, good uncertainty coverage or physical adequacy.
