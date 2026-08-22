# 22 - Seleção do Candidato Gold

## 1. Objetivo da Seleção

A etapa de seleção Gold teve como objetivo escolher um planeta e uma missão
principal para a primeira análise bayesiana futura.

A seleção não foi feita manualmente apenas por preferência. Ela foi baseada em
um scorecard simples, explícito e reprodutível, construído a partir da Silver.

O objetivo do scorecard não é definir uma métrica astrofísica definitiva. Ele
serve para justificar de forma transparente por que um alvo é mais apropriado
para a primeira modelagem.

## 2. Fontes Silver Usadas

O scorecard leu os seguintes arquivos:

```text
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/lightcurves/mast/mast_fits_metadata.csv
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
data/silver/catalogs/exomast/exomast_tces.csv
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_metadata.csv
```

Esses arquivos já continham a consolidação da disponibilidade de dados por
planeta, missão e fonte.

## 3. Arquivos Gold Gerados Pela Seleção

Foram criados:

```text
data/gold/selection/gold_candidate_scorecard.csv
data/gold/selection/gold_candidate_report.md
data/gold/selection/selected_gold_target.json
```

O CSV é a versão tabular do scorecard.

O Markdown é a versão humana da justificativa.

O JSON é a decisão final em formato legível por máquina.

## 4. Critérios de Pontuação

A pontuação foi dividida em três blocos:

- disponibilidade;
- qualidade técnica;
- completude catalográfica.

### 4.1 Disponibilidade

Critérios:

- `+3` se possui Kepler;
- `+2` se possui TESS;
- `+1` se possui K2;
- `+1` se possui pelo menos 50.000 linhas MAST;
- `+1` se possui observações ETD.

Justificativa:

Kepler recebeu maior peso porque, para trânsitos de exoplanetas, fornece
séries temporais extensas, homogêneas e historicamente muito usadas. TESS é
igualmente relevante, mas neste projeto a primeira modelagem foi planejada
para começar com um alvo Kepler quando disponível.

### 4.2 Qualidade Técnica

Critérios:

- `+2` se `PDCSAP_FLUX` está disponível;
- `+1` se `SAP_FLUX` está disponível;
- `+3` se a razão `quality == 0` é pelo menos `0,80`;
- `+2` se a razão `quality == 0` é pelo menos `0,60`;
- `+1` se há qualquer linha com `quality == 0`;
- `-1` se mais de 30% das linhas têm `quality != 0`.

Justificativa:

`PDCSAP_FLUX` foi preferido por ser o fluxo corrigido pelo pipeline da missão,
mantendo-se ainda como dado observacional tabular derivado da missão, não como
resultado de modelagem bayesiana deste projeto.

O filtro por `quality == 0` é técnico: ele seleciona pontos sem flags de
qualidade instrumentais explícitas. Esse filtro não remove outliers por análise
estatística própria e não ajusta o trânsito.

### 4.3 Completude Catalográfica

Critérios:

- `+2` se há período orbital;
- `+2` se há tempo de meio trânsito;
- `+1` se há duração de trânsito;
- `+1` se há profundidade de trânsito.

Justificativa:

Esses parâmetros são necessários para preparar fase orbital e uma janela
inicial de trânsito. Sem período e tempo central, o faseamento não seria
defensável sem criar aproximações adicionais.

## 5. Resultado do Scorecard

Resumo dos candidatos principais:

| Planeta | Kepler | TESS | Score total | Papel recomendado |
|---|---:|---:|---:|---|
| TrES-2 b | sim | sim | 19 | backup_candidate |
| HAT-P-7 b | sim | sim | 19 | primary_candidate |
| HD 209458 b | não | sim | 16 | reference_only |
| WASP-10 b | não | sim | 16 | reference_only |
| HAT-P-32 b | não | sim | 16 | reference_only |
| HD 189733 b | não | sim | 16 | reference_only |
| WASP-12 b | não | sim | 16 | reference_only |
| WASP-4 b | não | sim | 16 | reference_only |

HAT-P-7 b e TrES-2 b empataram em score total, ambos com `19`.

## 6. Por Que HAT-P-7 b Foi Selecionado

A decisão final selecionou:

```text
HAT-P-7 b
```

Motivo registrado no JSON de seleção:

```text
HAT-P-7 b selected because it satisfies the default rule: Kepler available, PDCSAP flux available, orbital period available, and more than 1000 quality==0 rows.
```

Além do score, HAT-P-7 b já era o candidato principal inicial do projeto.
Como ele satisfez todos os critérios mínimos esperados, não houve necessidade
de acionar o backup TrES-2 b.

## 7. Papel de TrES-2 b

TrES-2 b permaneceu como backup forte.

Motivos:

- possui Kepler;
- possui TESS;
- possui `PDCSAP_FLUX`;
- possui bom volume de pontos com `quality == 0`;
- empatou com HAT-P-7 b em score total.

Se a EDA ou a modelagem futura mostrar problemas graves com HAT-P-7 b, TrES-2 b
é a alternativa natural.

## 8. Limitações do Scorecard

O scorecard é simples por desenho.

Ele não avalia:

- ruído correlacionado;
- systematics de longo prazo;
- profundidade real por ajuste físico;
- consistência com literatura;
- contaminação por estrelas próximas;
- sensibilidade de priors;
- qualidade de resíduos;
- evidência bayesiana;
- convergência de cadeias MCMC.

Esses pontos pertencem a etapas posteriores.

## 9. Como Citar na Metodologia

Na metodologia, a seleção pode ser descrita como uma triagem técnica
reprodutível baseada em:

- disponibilidade de missões;
- presença de fluxo corrigido;
- quantidade de pontos válidos por flags;
- presença de parâmetros orbitais mínimos;
- rastreabilidade por manifesto.

É importante deixar claro que o scorecard não é uma métrica astrofísica de
qualidade absoluta, mas um procedimento operacional para escolher o primeiro
alvo de modelagem.
