# 06. Exo.MAST

## Fonte

Fonte pública:

```text
https://exo.mast.stsci.edu/
```

API pública usada:

```text
https://exo.mast.stsci.edu/api/v0.1
```

## Papel do Exo.MAST nesta etapa

O Exo.MAST foi usado como fonte auxiliar de metadados, não como fonte principal dos FITS.

O papel dele foi:

- resolver identificadores;
- obter propriedades públicas do planeta;
- recuperar listas de TCEs quando disponíveis;
- complementar rastreabilidade entre planeta, estrela e missões.

Os arquivos de curva de luz continuaram sendo baixados via MAST/Lightkurve.

## Estrutura de diretórios

```text
data/raw/exomast/
  hat_p_7_b/
  tres_2_b/
  hd_189733_b/
  hd_209458_b/
  wasp_12_b/
  wasp_10_b/
  wasp_4_b/
  hat_p_32_b/
  manifests/
```

## Arquivos por planeta

Arquivos comuns:

```text
identifiers.json
properties.json
notes.md
```

Arquivos opcionais:

```text
kepler_tces.json
tess_tces.json
```

Eles aparecem quando a API retorna identificadores associados à missão.

## `identifiers.json`

Retorno bruto do endpoint de identificadores.

Uso:

- resolver nome canônico;
- localizar IDs de missão;
- verificar nomes alternativos;
- apoiar rastreabilidade entre catálogos.

Exemplo de caminho:

```text
data/raw/exomast/hat_p_7_b/identifiers.json
```

## `properties.json`

Retorno bruto do endpoint de propriedades do planeta.

Uso:

- registrar metadados auxiliares;
- comparar futuramente com NASA Exoplanet Archive;
- apoiar validação de nome e alvo.

Exemplo:

```text
data/raw/exomast/wasp_12_b/properties.json
```

## `kepler_tces.json`

Lista de TCEs Kepler quando há identificador Kepler.

Na coleta validada, apareceu para:

- HAT-P-7 b;
- TrES-2 b.

Exemplo:

```text
data/raw/exomast/hat_p_7_b/kepler_tces.json
```

## `tess_tces.json`

Lista de TCEs TESS quando há identificador TESS.

Na coleta validada, apareceu para todos os planetas.

Exemplo:

```text
data/raw/exomast/hd_209458_b/tess_tces.json
```

## `notes.md`

Arquivo textual por planeta.

Registra:

- que Exo.MAST foi usado como fonte auxiliar;
- que FITS originais foram coletados via MAST/Lightkurve;
- resultados de tentativa por endpoint;
- endpoint de documentação.

## Quantidade de JSONs por planeta

| Planeta | JSONs Exo.MAST | Observação |
|---|---:|---|
| HAT-P-7 b | 4 | identificadores, propriedades, Kepler TCEs, TESS TCEs |
| TrES-2 b | 4 | identificadores, propriedades, Kepler TCEs, TESS TCEs |
| HD 189733 b | 3 | identificadores, propriedades, TESS TCEs |
| HD 209458 b | 3 | identificadores, propriedades, TESS TCEs |
| WASP-12 b | 3 | identificadores, propriedades, TESS TCEs |
| WASP-10 b | 3 | identificadores, propriedades, TESS TCEs |
| WASP-4 b | 3 | identificadores, propriedades, TESS TCEs |
| HAT-P-32 b | 3 | identificadores, propriedades, TESS TCEs |

Total de JSONs Exo.MAST:

```text
26
```

## O que não foi feito no Exo.MAST

Não foram baixadas curvas de luz via Exo.MAST.

Não foi feita:

- conversão de JSON para tabela analítica;
- escolha de TCE preferencial;
- validação astrofísica;
- cruzamento com curva de luz;
- modelagem.

## Uso metodológico no TCC

Na metodologia, esta fonte pode ser descrita como:

> O Exo.MAST foi usado como portal auxiliar de metadados e identificação, por meio de sua API pública. Para cada planeta foram coletados identificadores, propriedades e, quando disponíveis, listas de TCEs associadas às missões Kepler ou TESS. Esses JSONs foram preservados na camada RAW sem transformação e servem como apoio à rastreabilidade entre catálogos e produtos observacionais.

