# 21 - Contexto, Escopo e Regras da Gold

## 1. Contexto Acadêmico

O projeto de TCC se chama:

```text
Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional
```

O objetivo geral é investigar como inferência bayesiana pode ser aplicada à
estimação de parâmetros físicos em sistemas astrofísicos sob incerteza
observacional, com ênfase em curvas de luz de trânsitos de exoplanetas.

A arquitetura de dados foi construída em camadas:

- **RAW**: dados públicos preservados como coletados;
- **Silver**: dados validados, padronizados, tabulares e auditáveis;
- **Gold**: dataset analítico inicial para modelagem bayesiana futura.

Este documento descreve a terceira camada, a **Gold inicial**.

## 2. Papel da Gold no Projeto

A Gold existe para fazer a ponte entre uma camada Silver ampla, ainda
multi-planeta e multi-fonte, e uma etapa futura de modelagem bayesiana focada
em um alvo específico.

A Silver preserva uma base mais larga:

- vários planetas;
- múltiplas missões;
- NASA Exoplanet Archive;
- MAST/Lightkurve;
- Exo.MAST;
- ETD/VarAstro;
- catálogos;
- curvas espaciais;
- curvas terrestres;
- validações por planeta.

A Gold inicial reduz esse universo para um caso analítico controlado:

- escolhe um planeta;
- escolhe uma missão principal;
- escolhe uma coluna de fluxo;
- mantém uma coluna de incerteza associada;
- aplica um filtro técnico simples de qualidade;
- cria fase orbital;
- seleciona uma janela em torno do trânsito;
- registra a decisão em manifestos, logs e relatórios.

## 3. Entradas da Gold

A Gold lê exclusivamente arquivos da Silver:

```text
data/silver/
```

As principais entradas são:

```text
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/lightcurves/mast/mast_fits_metadata.csv
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
data/silver/catalogs/exomast/exomast_tces.csv
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_metadata.csv
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
```

A Gold não lê a internet, não baixa novos dados e não consulta APIs externas.

## 4. Saídas da Gold

A Gold escreve exclusivamente em:

```text
data/gold/
```

Os principais grupos de saída são:

- seleção do candidato Gold;
- catálogo de parâmetros de referência;
- curva primária;
- curva filtrada por qualidade;
- curva faseada;
- janela de trânsito;
- validações;
- manifesto;
- log;
- documentação técnica gerada pela execução.

## 5. Imutabilidade das Camadas Anteriores

A construção da Gold respeita a imutabilidade das camadas anteriores:

- não altera `data/raw/`;
- não altera `data/silver/`;
- não reprocessa arquivos RAW diretamente;
- não sobrescreve produtos Silver;
- não baixa dados externos;
- não cria dados sintéticos.

A Gold é uma camada derivada. Se for necessário reconstruí-la, ela deve ser
reexecutada a partir da Silver, não editada manualmente como fonte primária.

## 6. O Que Foi Feito

Foram implementadas as seguintes operações:

1. Leitura de resumos Silver por planeta.
2. Construção de scorecard de candidatos.
3. Seleção do planeta Gold inicial.
4. Seleção da missão principal.
5. Seleção da coluna de fluxo preferencial.
6. Seleção da coluna de erro do fluxo.
7. Criação de catálogo Gold com parâmetros de referência.
8. Criação da curva primária.
9. Remoção de linhas sem `time`.
10. Remoção de linhas sem fluxo.
11. Filtro técnico por `quality == 0`.
12. Conversão do tempo central de trânsito da NASA para a escala Kepler.
13. Criação de fase orbital.
14. Seleção de janela em torno da fase zero.
15. Criação de manifesto Gold com SHA256.
16. Criação de logs e validações.

## 7. O Que Não Foi Feito

Não foram feitos:

- inferência bayesiana;
- amostragem posterior;
- ajuste físico completo de trânsito;
- normalização científica final;
- escolha de priors;
- definição de likelihood final;
- modelagem com PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- comparação com literatura;
- gráficos finais para o TCC;
- seleção definitiva e irrevogável do dataset final da dissertação.

A Gold é uma preparação analítica inicial. A decisão de modelagem ainda depende
da EDA e dos diagnósticos posteriores.

## 8. Resultado da Execução Gold

O alvo selecionado foi:

```text
HAT-P-7 b
```

A missão escolhida foi:

```text
Kepler
```

A coluna de fluxo usada foi:

```text
pdcsap_flux
```

A coluna de erro usada foi:

```text
pdcsap_flux_err
```

Resumo numérico:

| Produto | Linhas |
|---|---:|
| Curva primária | 6.163 |
| Curva filtrada por qualidade | 3.909 |
| Curva faseada | 3.909 |
| Janela de trânsito | 1.664 |

## 9. Interpretação Correta da Gold

A Gold não deve ser interpretada como resultado científico final.

Ela deve ser interpretada como:

- uma seleção inicial rastreável;
- uma preparação analítica mínima;
- uma entrada organizada para EDA;
- uma base potencial para o primeiro modelo bayesiano.

A Gold permite que a modelagem futura comece a partir de um arquivo único,
mas ainda exige decisões adicionais sobre janela, normalização local, modelo
físico, priors, likelihood e diagnóstico posterior.
