# databricks_api
[🇬🇧 EN README](./README.md)

Lê os metadados do Unity Catalog de um workspace Databricks (catalogs, schemas, tabelas e colunas) e grava o resultado em JSON e/ou em arquivos de sources do dbt.

Os sources do dbt são gerados com um arquivo por schema, incluindo as colunas com tipo e comentário. Colunas `NOT NULL` recebem o teste `not_null`.

## Dependências
- `databricks-sdk`
- `pyyaml`

Para instalar as dependências:

```bash
uv sync
```

O devcontainer em `.devcontainer/` já vem com `Python` e `uv` instalados.

## Autenticação

O script lê duas variáveis de ambiente:

| Variável           | Exemplo                                   |
|--------------------|-------------------------------------------|
| `DATABRICKS_HOST`  | `https://abc-1234567890-0123.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | personal access token do usuário ou service principal |

No devcontainer, elas são carregadas de `.devcontainer/.env`, que não vai para o git. Fora dele, exporte as variáveis no shell antes de rodar.

O token precisa de permissão de leitura (`USE CATALOG`, `USE SCHEMA`, `SELECT` ou `BROWSE`) nos objetos que você quer coletar. Quando falta permissão em um catalog ou schema, o erro é registrado no campo `error` do JSON e a coleta segue para o próximo.

## Flags

| Flag | Descrição |
|------|-----------|
| `--json` | Grava tudo o que foi coletado em `output/json/catalogs.json`. |
| `--sources` | Grava os sources do dbt em `output/yml/<catalog>_<schema>.yml`. |
| `--include palavra [palavra ...]` | Coleta só catalogs, schemas e tabelas cujo nome tenha alguma dessas palavras. Se um catalog ou schema der match, tudo o que estiver dentro dele entra. |
| `--exclude [palavra ...]` | Ignora catalogs, schemas e tabelas cujo nome tenha alguma dessas palavras. Padrão: `system information_schema __databricks_internal`. |

Sem `--json` e sem `--sources`, o script coleta os metadados mas não grava nada.

### Como funciona o match

A comparação ignora maiúsculas e minúsculas. O nome é quebrado em `_`, `-`, `.` e espaço, e a palavra precisa ser igual ao nome inteiro ou a um desses pedaços:

| Palavra | Dá match em | Não dá match em |
|---------|-------------|-----------------|
| `dev` | `dev`, `sales_dev`, `DEV_raw` | `device` |
| `sap` | `sap`, `sap_vbak`, `bronze.sap` | `sapiens` |

O `--exclude` tem prioridade sobre o `--include`.

Passar `--exclude` com palavras próprias substitui o padrão. Para continuar ignorando os objetos de sistema, repita-os na lista.

## Exemplos

Gerar o JSON com tudo, exceto os objetos de sistema:

```bash
uv run src/main.py --json
```

Gerar os sources do dbt:

```bash
uv run src/main.py --sources
```

Gerar os dois:

```bash
uv run src/main.py --json --sources
```

Coletar só o que tiver `sap` ou `xpto` no nome:

```bash
uv run src/main.py --sources --include sap xpto
```

Ignorar também o que for de dev, mantendo o padrão:

```bash
uv run src/main.py --sources --exclude system information_schema __databricks_internal dev
```

Combinar os dois filtros (tudo de `sap`, menos o que for `dev` ou `tmp`):

```bash
uv run src/main.py --sources --include sap --exclude system information_schema __databricks_internal dev tmp
```

Coletar tudo, inclusive os objetos de sistema:

```bash
uv run src/main.py --json --exclude
```

## Saída

```
output/
├── json/
│   └── catalogs.json
└── yml/
    ├── main_sales.yml
    └── sap_raw.yml
```

Exemplo de `output/yml/main_sales.yml`:

```yaml
version: 2
sources:
- name: main_sales
  database: main
  schema: sales
  description: Vendas
  tables:
  - name: orders
    description: Pedidos
    columns:
    - name: id
      data_type: bigint
      description: PK
      data_tests:
      - not_null
    - name: obs
      data_type: string
```

No dbt, a tabela fica disponível como `{{ source('main_sales', 'orders') }}`.

O nome do source junta catalog e schema porque o mesmo schema (por exemplo, `default`) pode existir em mais de um catalog.

## Observações

- Com `--include`, o script ainda lista os schemas e tabelas de todos os catalogs que não foram excluídos, porque precisa disso para encontrar tabelas que deem match. Em workspaces grandes, o `--exclude` é o que diminui as chamadas à API.
- Cada execução sobrescreve os arquivos em `output/`, mas não apaga os que não foram gerados de novo. Se um schema sair do filtro, o `.yml` antigo dele continua na pasta.
