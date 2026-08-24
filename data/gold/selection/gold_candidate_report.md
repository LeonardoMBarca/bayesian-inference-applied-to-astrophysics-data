# Relatório de Seleção Gold

## 1. Objetivo

Selecionar um planeta e uma missão principal para a primeira camada Gold do projeto, usando apenas artefatos já consolidados na Silver.

## 2. Fontes Silver Usadas

- `data/silver/validation/silver_summary_by_planet.csv`
- `data/silver/validation/silver_mast_quality_summary.csv`
- `data/silver/lightcurves/mast/mast_fits_metadata.csv`
- `data/silver/catalogs/nasa/pscomppars_selected_planets.csv`
- `data/silver/catalogs/exomast/exomast_tces.csv`
- `data/silver/etd/etd_observations.csv`
- `data/silver/etd/etd_lightcurve_metadata.csv`

## 3. Critérios de Pontuação

Pontuação de disponibilidade:

- +3 se possui Kepler;
- +2 se possui TESS;
- +1 se possui K2;
- +1 se possui ao menos 50.000 linhas MAST;
- +1 se possui observações ETD.

Pontuação de qualidade:

- +2 se `PDCSAP_FLUX` está disponível;
- +1 se `SAP_FLUX` está disponível;
- +3 se a razão `quality == 0` é pelo menos 0,80;
- +2 se a razão `quality == 0` é pelo menos 0,60;
- +1 se há qualquer linha `quality == 0`;
- -1 se mais de 30% das linhas têm `quality != 0`.

Pontuação catalográfica:

- +2 se há período orbital;
- +2 se há tempo de meio trânsito;
- +1 se há duração de trânsito;
- +1 se há profundidade de trânsito.

## 4. Tabela Resumida dos Candidatos

| planet_name | has_kepler | has_tess | kepler_fits_count | tess_fits_count | total_mast_rows | total_quality_zero_rows | score_total | recommended_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HAT-P-7 b | True | False | 3 | 3 | 64872 | 54075 | 17 | reference_only |
| Kepler-10 b | True | False | 3 | 0 | 6469 | 5267 | 15 | primary_candidate |

## 5. Planeta Escolhido

Planeta selecionado:

```text
Kepler-10 b
```

Missão principal selecionada:

```text
Kepler
```

Fonte de fluxo:

```text
pdcsap_flux
```

Justificativa:

```text
Kepler-10 b selected because it satisfies the default rule: Kepler available, PDCSAP flux available, orbital period available, and more than 1000 quality==0 rows.
```

## 6. Justificativa da Missão

A missão Kepler é preferida quando disponível porque fornece uma série temporal extensa e historicamente adequada para estudos de trânsitos. Para o alvo escolhido, Kepler está disponível na Silver e contém fluxo `PDCSAP_FLUX`.

## 7. Limitações

- A pontuação é simples e transparente, não uma métrica astrofísica definitiva.
- A seleção não avalia ruído instrumental em profundidade.
- A seleção não ajusta modelo de trânsito.
- A seleção não compara parâmetros com literatura.
- A seleção não executa inferência bayesiana.

## 8. Próximos Passos

A próxima etapa poderá usar `data/gold/kepler_10_b/modeling/transit_window_lightcurve.csv` como entrada para uma modelagem bayesiana preliminar, após revisão das escolhas de normalização, janela temporal e modelo físico.
