# Documentação Silver

Esta pasta contém a documentação da camada **Silver** do datalake local.

A Silver lê exclusivamente a RAW, valida os artefatos brutos e gera tabelas padronizadas, auditáveis e rastreáveis em `data/silver/`.

## Escopo

A Silver cobre:

- validação do manifesto RAW;
- consolidação de catálogos NASA;
- tabularização de JSONs Exo.MAST;
- leitura dos FITS MAST;
- extração de curvas de luz tabulares;
- consolidação de observações ETD;
- extração de pontos fotométricos ETD;
- criação de manifestos, logs e validações.

Ela não executa:

- criação de Gold;
- normalização final de curvas;
- faseamento orbital;
- remoção de outliers;
- filtragem por qualidade;
- conversão de magnitude para fluxo;
- modelagem física;
- inferência bayesiana.

## Como ler

Os arquivos estão numerados em ordem sugerida:

1. [12_contexto_escopo_e_regras_silver.md](12_contexto_escopo_e_regras_silver.md)  
   Papel da Silver, regras de imutabilidade da RAW e limites da etapa.

2. [13_mapa_do_pipeline_silver_e_codigo.md](13_mapa_do_pipeline_silver_e_codigo.md)  
   Scripts, módulos e fluxo de execução Silver.

3. [14_catalogos_silver_nasa_e_exomast.md](14_catalogos_silver_nasa_e_exomast.md)  
   Catálogos NASA e Exo.MAST.

4. [15_curvas_mast_silver.md](15_curvas_mast_silver.md)  
   Leitura dos FITS MAST e geração das curvas tabulares.

5. [16_etd_varastro_silver.md](16_etd_varastro_silver.md)  
   Observações ETD, curvas JSON públicas e pontos fotométricos.

6. [17_manifestos_logs_validacoes_silver.md](17_manifestos_logs_validacoes_silver.md)  
   Manifestos, logs, checksums e validações Silver.

7. [18_inventario_silver_por_planeta.md](18_inventario_silver_por_planeta.md)  
   Inventário Silver por planeta.

8. [19_dicionario_de_arquivos_e_campos_silver.md](19_dicionario_de_arquivos_e_campos_silver.md)  
   Dicionário de arquivos e campos Silver.

9. [20_como_usar_silver_na_metodologia.md](20_como_usar_silver_na_metodologia.md)  
   Como aproveitar a Silver na metodologia.

## Saída principal documentada

```text
data/silver/
```

Manifesto Silver:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

Documentação técnica mantida no repositório:

```text
docs/silver/
```
