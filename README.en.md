# databricks_api

Reads Unity Catalog metadata from a Databricks workspace (catalogs, schemas, tables and columns) and writes it out as JSON and/or dbt source files.

dbt sources are written as one file per schema, including each column's type and comment. `NOT NULL` columns get a `not_null` test.

## Dependencies

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- `databricks-sdk`
- `pyyaml`

To install:

```bash
uv sync
```

The devcontainer in `.devcontainer/` already ships with Python and uv.

## Authentication

The script reads two environment variables:

| Variable           | Example                                         |
|--------------------|-------------------------------------------------|
| `DATABRICKS_HOST`  | `https://abc-1234567890-0123.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | personal access token for a user or service principal |

In the devcontainer they are loaded from `.devcontainer/.env`, which is not committed. Outside of it, export them in your shell before running.

The token needs read access (`USE CATALOG`, `USE SCHEMA`, `SELECT` or `BROWSE`) on the objects you want to collect. When access to a catalog or schema is denied, the error is stored in the `error` field of the JSON and collection moves on to the next one.

## Flags

| Flag | Description |
|------|-------------|
| `--json` | Writes everything collected to `output/json/catalogs.json`. |
| `--sources` | Writes dbt sources to `output/yml/<catalog>_<schema>.yml`. |
| `--include word [word ...]` | Collects only catalogs, schemas and tables whose name contains one of these words. If a catalog or schema matches, everything inside it is included. |
| `--exclude [word ...]` | Skips catalogs, schemas and tables whose name contains one of these words. Default: `system information_schema __databricks_internal`. |

Without `--json` or `--sources`, the script collects the metadata but writes nothing.

### How matching works

Matching is case-insensitive. The name is split on `_`, `-`, `.` and spaces, and the word must equal either the whole name or one of those parts:

| Word | Matches | Doesn't match |
|------|---------|---------------|
| `dev` | `dev`, `sales_dev`, `DEV_raw` | `device` |
| `sap` | `sap`, `sap_vbak`, `bronze.sap` | `sapiens` |

`--exclude` takes precedence over `--include`.

Passing your own words to `--exclude` replaces the default. To keep skipping system objects, list them again.

## Examples

Write the JSON with everything except system objects:

```bash
uv run src/main.py --json
```

Write the dbt sources:

```bash
uv run src/main.py --sources
```

Write both:

```bash
uv run src/main.py --json --sources
```

Collect only what has `sap` or `xpto` in its name:

```bash
uv run src/main.py --sources --include sap xpto
```

Also skip anything dev, keeping the default:

```bash
uv run src/main.py --sources --exclude system information_schema __databricks_internal dev
```

Combine both filters (everything `sap`, except `dev` or `tmp`):

```bash
uv run src/main.py --sources --include sap --exclude system information_schema __databricks_internal dev tmp
```

Collect everything, system objects included:

```bash
uv run src/main.py --json --exclude
```

## Output

```
output/
├── json/
│   └── catalogs.json
└── yml/
    ├── main_sales.yml
    └── sap_raw.yml
```

Example `output/yml/main_sales.yml`:

```yaml
version: 2
sources:
- name: main_sales
  database: main
  schema: sales
  description: Sales
  tables:
  - name: orders
    description: Orders
    columns:
    - name: id
      data_type: bigint
      description: PK
      data_tests:
      - not_null
    - name: notes
      data_type: string
```

In dbt, the table is then available as `{{ source('main_sales', 'orders') }}`.

The source name combines catalog and schema because the same schema (e.g. `default`) can exist in more than one catalog.

## Notes

- With `--include`, the script still lists schemas and tables for every catalog that isn't excluded, since it has to look for matching tables. On large workspaces, `--exclude` is what actually cuts down API calls.
- Each run overwrites files in `output/` but doesn't delete files that weren't regenerated. If a schema drops out of the filter, its old `.yml` stays in the folder.
