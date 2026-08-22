# 18. Inventário Silver por Planeta

## Objetivo deste documento

Este documento resume a disponibilidade de dados Silver por planeta.

Ele responde:

- quais planetas possuem NASA consolidada;
- quais planetas possuem Exo.MAST tabularizado;
- quais planetas possuem curvas MAST tabulares;
- quais missões aparecem por planeta;
- quantas observações ETD foram consolidadas;
- quantos pontos fotométricos ETD foram extraídos.

## Resumo geral

| Planeta | NASA `pscomppars` | NASA `ps` | FITS MAST | Linhas MAST | Missões MAST | Exo.MAST JSONs | Obs. ETD | Curvas ETD | Pontos ETD |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| HAT-P-7 b | 1 | 24 | 6 | 64.872 | Kepler, TESS | 4 | 60 | 5 | 1.243 |
| TrES-2 b | 1 | 34 | 6 | 63.836 | Kepler, TESS | 4 | 371 | 5 | 1.180 |
| HD 189733 b | 1 | 21 | 3 | 57.213 | TESS | 3 | 218 | 5 | 1.262 |
| HD 209458 b | 1 | 23 | 3 | 159.179 | TESS | 3 | 92 | 5 | 1.625 |
| WASP-12 b | 1 | 19 | 3 | 54.224 | TESS | 3 | 376 | 5 | 793 |
| WASP-10 b | 1 | 11 | 3 | 145.851 | TESS | 3 | 241 | 5 | 322 |
| WASP-4 b | 1 | 22 | 3 | 56.783 | TESS | 3 | 80 | 5 | 1.039 |
| HAT-P-32 b | 1 | 13 | 3 | 140.907 | TESS | 3 | 212 | 5 | 1.288 |

## HAT-P-7 b

Slug:

```text
hat_p_7_b
```

Estrela:

```text
HAT-P-7
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 24 linhas.

Exo.MAST:

- 4 JSONs tabularizados;
- inclui TCEs Kepler e TESS.

### MAST

Arquivos:

```text
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
data/silver/lightcurves/mast/hat_p_7_b/tess_lightcurve.csv
```

Resultados:

- FITS: 6;
- linhas MAST: 64.872;
- missões: Kepler e TESS.

### ETD

- observações: 60;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.243;
- filtros/bandas: `Clear`, `R`, `SLOAN 'r`, `V to IR`;
- registros privados: 0.

### Comentário

É o candidato principal inicial do projeto. Tem boa vantagem metodológica por combinar Kepler, TESS e ETD.

## TrES-2 b

Slug:

```text
tres_2_b
```

Estrela:

```text
TrES-2
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 34 linhas.

Exo.MAST:

- 4 JSONs tabularizados;
- inclui TCEs Kepler e TESS.

### MAST

Arquivos:

```text
data/silver/lightcurves/mast/tres_2_b/kepler_lightcurve.csv
data/silver/lightcurves/mast/tres_2_b/tess_lightcurve.csv
```

Resultados:

- FITS: 6;
- linhas MAST: 63.836;
- missões: Kepler e TESS.

### ETD

- observações: 371;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.180;
- filtros/bandas: `Clear`, `L`, `R`, `clear`, `r`;
- registros privados: 0.

### Comentário

É um candidato forte para Gold pela presença de Kepler e TESS, além de grande volume de observações ETD.

## HD 189733 b

Slug:

```text
hd_189733_b
```

Estrela:

```text
HD 189733
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 21 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/hd_189733_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 57.213;
- missão: TESS.

### ETD

- observações: 218;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.262;
- filtros/bandas: `Clear`, `R`, `i`;
- registros privados: 0.

## HD 209458 b

Slug:

```text
hd_209458_b
```

Estrela:

```text
HD 209458
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 23 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/hd_209458_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 159.179;
- missão: TESS.

### ETD

- observações: 92;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.625;
- filtros/bandas: `Clear`, `I`, `R`;
- registros privados: 0.

## WASP-12 b

Slug:

```text
wasp_12_b
```

Estrela:

```text
WASP-12
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 19 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/wasp_12_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 54.224;
- missão: TESS.

### ETD

- observações: 376;
- curvas JSON públicas: 5;
- pontos fotométricos: 793;
- filtros/bandas: `CBB`, `Clear`, `Luminance`, `R`, `V to IR`;
- registros privados: 0.

## WASP-10 b

Slug:

```text
wasp_10_b
```

Estrela:

```text
WASP-10
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 11 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/wasp_10_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 145.851;
- missão: TESS.

### ETD

- observações: 241;
- curvas JSON públicas: 5;
- pontos fotométricos: 322;
- filtros/bandas: `Clear`, `IR-UV`, `L`, `R`;
- registros privados: 0.

## WASP-4 b

Slug:

```text
wasp_4_b
```

Estrela:

```text
WASP-4
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 22 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/wasp_4_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 56.783;
- missão: TESS.

### ETD

- observações: 80;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.039;
- filtros/bandas: `Clear`, `Luminance`, `V`;
- registros privados: 0.

## HAT-P-32 b

Slug:

```text
hat_p_32_b
```

Estrela:

```text
HAT-P-32
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 13 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/hat_p_32_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 140.907;
- missão: TESS.

### ETD

- observações: 212;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.288;
- filtros/bandas: `CV`, `IR`, `Sloan r'`, `V`, `r`;
- registros privados: 0.

## Conclusão do inventário

Todos os planetas possuem:

- NASA `pscomppars`;
- NASA `ps`;
- Exo.MAST tabularizado;
- TESS tabularizado;
- ETD observações;
- ETD pontos fotométricos.

Somente HAT-P-7 b e TrES-2 b possuem Kepler na Silver.

Nenhum planeta possui K2 na Silver.

Para Gold, a disponibilidade favorece HAT-P-7 b e TrES-2 b, com preferência inicial para HAT-P-7 b por alinhamento com o escopo definido do projeto.
