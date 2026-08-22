# 12. Contexto, Escopo e Regras da Camada Silver

## Objetivo deste documento

Este documento descreve a implementação da camada **Silver** do datalake local do projeto:

**Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional**

- Aluno: Leonardo Moraes Barca
- Orientadora: Patrícia Belfiore Fávero
- Curso: MBA em Data Science e Analytics
- Etapa documentada: transformação tabular, validação e padronização técnica dos dados brutos já coletados.

A documentação aqui registrada foi escrita para servir como base técnica para a futura seção de metodologia do TCC.

## Papel da Silver no datalake

O datalake local foi organizado em camadas:

| Camada | Papel | Status |
|---|---|---|
| RAW | Preservar dados públicos como coletados | Implementada |
| Silver | Validar, tabularizar e padronizar dados brutos | Implementada |
| Gold | Construir dataset analítico final para um planeta específico | Não implementada |

A Silver fica em:

```text
data/silver/
```

Ela lê dados de:

```text
data/raw/
```

e não altera a RAW.

## Princípio central

A RAW foi tratada como imutável.

Durante a implementação e execução da Silver, não foram feitos:

- alteração de arquivos em `data/raw/`;
- remoção de arquivos em `data/raw/`;
- movimentação de arquivos em `data/raw/`;
- renomeação de arquivos em `data/raw/`;
- sobrescrita de arquivos em `data/raw/`;
- novo download de dados externos;
- chamada de rede.

A verificação final comparou checksums da RAW antes e depois da construção da Silver. O resultado não indicou diferenças.

## Objetivo técnico da Silver

A Silver transforma os artefatos RAW em tabelas CSV padronizadas, auditáveis e reexecutáveis.

Ela foi criada para responder às seguintes perguntas:

1. Quais dados brutos foram usados?
2. Onde cada linha Silver se conecta ao arquivo RAW original?
3. Quais planetas possuem catálogos consolidados?
4. Quais planetas possuem curvas MAST em formato tabular?
5. Quais observações e curvas públicas ETD foram consolidadas?
6. Quais colunas estão presentes ou ausentes nos produtos FITS?
7. Quais validações foram executadas antes de qualquer análise científica?

## Fontes usadas pela Silver

A Silver usou somente os dados já existentes na RAW.

| Fonte | Entrada RAW | Saída Silver |
|---|---|---|
| NASA Exoplanet Archive | CSVs `pscomppars`, `ps` e snapshot geral | Catálogos NASA padronizados |
| Exo.MAST | JSONs de identificadores, propriedades e TCEs | Tabelas achatadas |
| MAST / Lightkurve | FITS originais de Kepler e TESS | Curvas de luz tabulares e metadados FITS |
| ETD / VarAstro | JSONs/CSVs públicos de observações e curvas | Observações, pontos fotométricos e metadados |

## O que foi padronizado

Foram padronizados:

- nomes de planetas;
- slugs dos planetas;
- estrelas hospedeiras;
- nomes de colunas catalográficas;
- campos principais de curvas de luz;
- metadados de missão;
- metadados de origem;
- checksums dos artefatos Silver;
- manifestos e logs da execução.

## O que não foi padronizado cientificamente

A Silver não transforma os dados em uma base analítica final.

Por isso, não foram feitos:

- normalização de fluxo;
- conversão de magnitude para fluxo;
- faseamento orbital;
- seleção definitiva de janela de trânsito;
- remoção de outliers;
- filtragem por flags de qualidade;
- interpolação;
- imputação de valores ausentes;
- escolha de solução orbital preferida;
- ajuste de curva de luz;
- inferência bayesiana.

## Por que manter a Silver sem modelagem

A separação é metodologicamente importante.

A Silver demonstra:

- rastreabilidade;
- reprodutibilidade;
- controle de qualidade inicial;
- separação entre dado bruto e dado preparado;
- preservação de incertezas e ausências;
- ausência de decisões analíticas prematuras.

Esses pontos são relevantes para um TCC que pretende discutir inferência sob incerteza observacional, porque deixam claro que a etapa de organização dos dados não introduziu inferências, filtros ou preenchimentos antes da modelagem.

## Planetas cobertos

A configuração Silver manteve os oito planetas candidatos da RAW:

| Planeta | Estrela | Slug |
|---|---|---|
| HAT-P-7 b | HAT-P-7 | `hat_p_7_b` |
| TrES-2 b | TrES-2 | `tres_2_b` |
| HD 189733 b | HD 189733 | `hd_189733_b` |
| HD 209458 b | HD 209458 | `hd_209458_b` |
| WASP-12 b | WASP-12 | `wasp_12_b` |
| WASP-10 b | WASP-10 | `wasp_10_b` |
| WASP-4 b | WASP-4 | `wasp_4_b` |
| HAT-P-32 b | HAT-P-32 | `hat_p_32_b` |

## Diretórios criados

Estrutura Silver principal:

```text
data/silver/
├── catalogs/
│   ├── nasa/
│   └── exomast/
├── lightcurves/
│   ├── mast/
│   └── etd/
├── etd/
├── validation/
├── manifests/
├── logs/
└── docs/
```

Observação: a pasta `data/silver/lightcurves/etd/` foi criada para manter separação conceitual, mas as tabelas ETD consolidadas foram gravadas em `data/silver/etd/`, conforme definido na especificação da tarefa.

## Comando principal

Pipeline completo:

```bash
python scripts/build_silver_data.py
```

No ambiente desta execução, foi usado:

```bash
.venv/bin/python scripts/build_silver_data.py
```

Isso ocorreu porque o comando `python` não estava disponível no PATH fora do ambiente virtual. Após ativar o ambiente com `source .venv/bin/activate`, o comando documentado com `python` é o esperado.

## Resultado geral da execução

Resumo validado:

| Métrica | Valor |
|---|---:|
| Registros lidos no manifesto RAW | 749 |
| Arquivos RAW locais únicos validados | 399 |
| Arquivos RAW ausentes | 0 |
| Divergências de checksum RAW | 0 |
| FITS MAST processados | 30 |
| Curvas MAST tabularizadas | 10 |
| Observações ETD consolidadas | 1.650 |
| Pontos fotométricos ETD extraídos | 8.752 |
| Arquivos Silver criados | 29 |
| Registros no manifesto Silver | 26 |
| Divergências de checksum Silver | 0 |

## Status da Gold

A Gold não foi criada.

A Silver apenas indica disponibilidade de dados. Com base na disponibilidade, HAT-P-7 b e TrES-2 b são candidatos fortes para a futura Gold porque possuem curvas Kepler e TESS. HAT-P-7 b permanece como candidato principal inicial.
