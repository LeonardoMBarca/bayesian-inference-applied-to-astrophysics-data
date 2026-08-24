# Documentação RAW

> Os capítulos numerados são um snapshot anterior ao hardening de 2026-08-24 e
> ainda podem inventariar oito alvos históricos. O pipeline executável atual
> suporta HAT-P-7 b e Kepler-10 b; use `src/project_config.py` e os manifestos
> `raw_data_current_state.*` para o estado vigente.

Esta pasta contém a documentação da camada **RAW** do datalake local.

A RAW é a camada de coleta e preservação dos dados públicos brutos. Ela guarda respostas e arquivos como foram obtidos das fontes, acompanhados de manifestos, logs e checksums.

## Escopo

A RAW cobre:

- NASA Exoplanet Archive;
- MAST / Lightkurve / Astroquery;
- Exo.MAST;
- ETD / VarAstro.

Ela não executa:

- limpeza;
- normalização;
- faseamento;
- remoção de outliers;
- modelagem;
- inferência bayesiana;
- criação de Silver ou Gold.

## Como ler

Os arquivos estão numerados em ordem sugerida:

1. [00_contexto_escopo_e_regras_raw.md](00_contexto_escopo_e_regras_raw.md)  
   Escopo, regras e limites da RAW.

2. [01_mapa_do_pipeline_e_codigo.md](01_mapa_do_pipeline_e_codigo.md)  
   Scripts, módulos e arquitetura do pipeline RAW.

3. [02_configuracao_execucao_ambiente.md](02_configuracao_execucao_ambiente.md)  
   Ambiente, dependências e comandos.

4. [03_manifestos_logs_checksums_reexecucao.md](03_manifestos_logs_checksums_reexecucao.md)  
   Manifestos, logs, checksums e reexecução.

5. [04_nasa_exoplanet_archive.md](04_nasa_exoplanet_archive.md)  
   Coleta NASA via TAP.

6. [05_mast_lightkurve_astroquery.md](05_mast_lightkurve_astroquery.md)  
   Busca e download de curvas MAST.

7. [06_exomast.md](06_exomast.md)  
   Metadados Exo.MAST.

8. [07_etd_varastro.md](07_etd_varastro.md)  
   Coleta ETD / VarAstro.

9. [08_inventario_por_planeta.md](08_inventario_por_planeta.md)  
   Inventário RAW por planeta.

10. [09_validacao_e_qualidade.md](09_validacao_e_qualidade.md)  
    Validação da coleta RAW.

11. [10_como_usar_na_metodologia.md](10_como_usar_na_metodologia.md)  
    Como aproveitar a RAW na metodologia.

12. [11_dicionario_de_arquivos_e_campos.md](11_dicionario_de_arquivos_e_campos.md)  
    Dicionário de arquivos e campos RAW.

## Saída principal documentada

```text
data/raw/
```

Manifesto global:

```text
data/raw/_manifests/raw_data_manifest.csv
data/raw/_manifests/raw_data_manifest.json
```
