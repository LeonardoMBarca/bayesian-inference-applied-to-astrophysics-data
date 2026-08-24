# Política de armazenamento e reprodutibilidade

Esta política separa evidência de origem, produtos derivados reproduzíveis e
artefatos de execução caros.

## O que fica no Git

- código, configuração autoritativa, testes, CI e documentação;
- manifestos RAW de eventos e de estado atual, com caminhos POSIX e SHA-256;
- arquivos RAW usados para construir os datasets Gold suportados;
- metadados de busca e seleção de cadência;
- catálogos e metadados Silver, além da janela Gold publicada, seu
  `dataset_metadata` e diagnósticos de normalização;
- configurações, status, resumos, tabelas e relatórios de runs científicos.

RAW é evidência imutável: um arquivo baixado nunca deve ser normalizado,
reescrito ou substituído silenciosamente. Uma nova obtenção gera um novo evento
no histórico e o manifesto de estado identifica o artefato atual verificável.

## O que é regenerado localmente

- traces NetCDF (`*.nc`), por serem grandes;
- tabelas completas de curvas Silver, que são derivadas dos FITS RAW;
- intermediários Gold completos (`primary`, `quality_filtered`,
  `phase_folded` e `segment_normalized`); a janela Gold consumida pelo M5 fica
  versionada e o clean rebuild comprova a regeneração dos intermediários;
- séries completas de injeção de ruído; sua configuração e semente permanecem
  registradas, mas o CSV é reproduzível pelo script correspondente;
- caches, logs e ambientes virtuais.

Um run sem trace não deve ser apresentado como reproduzível apenas pelos
resumos. Para refazê-lo, use a configuração, o `dataset_id`, o checksum da
entrada de modelagem, o perfil de prior e o ambiente fixado. O trace local deve
ser conservado quando auditoria amostra-a-amostra for necessária.

## Reconstrução validada

```bash
python scripts/refresh_raw_manifest_state.py
python scripts/build_silver_data.py
python scripts/build_gold_data.py
python scripts/validate_hardened_artifacts.py
python -m unittest discover -s tests -v
# validação clean-room mais cara, também disponível manualmente na CI
python scripts/validate_clean_rebuild.py
```

A coleta RAW usa rede e pode produzir um novo estado. Para reproduzir exatamente
o dataset publicado, não baixe novamente: valide os checksums RAW versionados e
reconstrua Silver e Gold a partir deles.
