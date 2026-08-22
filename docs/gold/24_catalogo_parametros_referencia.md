# 24 - Catálogo Gold de Parâmetros de Referência

## 1. Objetivo

O catálogo de referência Gold reúne os parâmetros planetários e estelares
necessários para preparar a curva de luz de HAT-P-7 b para modelagem futura.

Ele é derivado da tabela Silver:

```text
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
```

Essa tabela Silver, por sua vez, foi derivada da RAW NASA Exoplanet Archive:

```text
data/raw/nasa_exoplanet_archive/pscomppars/hat_p_7_b/response.csv
```

## 2. Arquivos Criados

Versão CSV:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
```

Versão JSON:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.json
```

A versão CSV é conveniente para leitura tabular.

A versão JSON é conveniente para uso programático em scripts ou notebooks.

## 3. Conteúdo

O catálogo possui uma linha para:

```text
HAT-P-7 b
```

Campos principais:

| Campo | Descrição |
|---|---|
| `planet_name` | Nome do planeta selecionado |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Identificador seguro para caminhos |
| `orbital_period_days` | Período orbital em dias |
| `transit_midpoint` | Tempo central de trânsito conforme catálogo NASA |
| `transit_duration_hours` | Duração de trânsito em horas |
| `transit_depth` | Profundidade catalográfica do trânsito |
| `planet_radius_earth` | Raio planetário em raios terrestres |
| `planet_radius_jupiter` | Raio planetário em raios de Júpiter |
| `stellar_radius_solar` | Raio estelar em raios solares |
| `stellar_mass_solar` | Massa estelar em massas solares |
| `stellar_teff` | Temperatura efetiva da estrela |
| `system_distance_pc` | Distância do sistema em parsecs |
| `source_raw_path` | Arquivo RAW de origem |
| `silver_source_path` | Arquivo Silver de origem |
| `gold_created_at_utc` | Data/hora UTC de criação da Gold |

## 4. Valores Registrados

Valores principais da execução:

| Parâmetro | Valor |
|---|---:|
| Período orbital | `2,20474` dias |
| Tempo central de trânsito NASA | `2454954,358572` |
| Duração de trânsito | `3,88216` horas |
| Profundidade catalográfica | `0,6` |
| Raio planetário | `16,92559` raios terrestres |
| Raio planetário | `1,51` raios de Júpiter |
| Raio estelar | `2,0` raios solares |
| Massa estelar | `1,56` massas solares |
| Temperatura efetiva | `6389 K` |
| Distância do sistema | `341,079 pc` |

## 5. Uso na Gold

O catálogo foi usado para:

- recuperar período orbital;
- recuperar tempo central de trânsito;
- recuperar duração de trânsito;
- criar a fase orbital;
- definir a largura inicial da janela de trânsito;
- documentar parâmetros físicos que serão necessários na modelagem futura.

## 6. Conversão de Tempo

O `transit_midpoint` veio do catálogo NASA em escala absoluta de data juliana
baricêntrica.

A curva Kepler usa tempo relativo com referência:

```text
BJDREFI = 2454833
BJDREFF = 0
```

Na Gold, o tempo central foi convertido para a escala da curva:

```text
transit_midpoint_used = transit_midpoint - (BJDREFI + BJDREFF)
```

Resultado usado:

```text
121.35857200017199
```

Esse valor aparece em:

```text
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

## 7. O Que Não Foi Feito

O catálogo Gold não:

- escolhe nova solução astrofísica;
- recalcula parâmetros físicos;
- compara com literatura;
- ajusta período orbital;
- ajusta época de trânsito;
- estima incertezas novas;
- preenche valores ausentes.

Ele apenas preserva, para o planeta selecionado, os parâmetros catalográficos
que já estavam consolidados na Silver.
