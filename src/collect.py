"""
Collects: catalogs -> schemas -> tables -> columns via the Unity Catalog API.
Auth:
    WorkspaceClient must read at least DATABRICKS_HOST and DATABRICKS_TOKEN.
"""
import os
import re

from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import DatabricksError


DEFAULT_EXCLUDE = ["system", "information_schema", "__databricks_internal"]


def matches(name: str, words: list[str]) -> bool:
    """
    True if a word equals the whole name or any part of it (split on _ - . or space), case-insensitive.
        e.g. "dev" matches "dev", "sales_dev" and "DEV_raw", but not "device".
    """
    name = name.lower()
    parts = re.split(r"[_\-.\s]+", name)
    return any(word.lower() == name or word.lower() in parts for word in words)


def collect(include: list[str] | None = None, exclude: list[str] | None = None) -> list[dict]:
    """
    include: if given, keep only catalogs, schemas and tables matching a word
        (a matching catalog or schema keeps everything under it).
    exclude: skip catalogs, schemas and tables matching a word; wins over include.
    """
    include = include or []
    exclude = exclude or []

    HOST=os.getenv("DATABRICKS_HOST")
    TOKEN=os.getenv("DATABRICKS_TOKEN")

    w = WorkspaceClient(
            host=HOST,
            token=TOKEN
        )

    result = []

    for catalog in w.catalogs.list():
        if matches(catalog.name, exclude):
            continue

        ctlg_included = not include or matches(catalog.name, include)
        ctlg_obj = {"name": catalog.name, "comment": catalog.comment, "schemas": []}

        try:
            schemas = list(w.schemas.list(catalog_name=catalog.name))
        except DatabricksError as e:
            ctlg_obj["error"] = str(e)
            if ctlg_included:
                result.append(ctlg_obj)
            continue

        for schema in schemas:
            if matches(schema.name, exclude):
                continue

            schm_included = ctlg_included or matches(schema.name, include)
            schm_obj = {"name": schema.name, "comment": schema.comment, "tables": []}

            try:
                tables = list(w.tables.list(catalog_name=catalog.name, schema_name=schema.name))
            except DatabricksError as e:
                schm_obj["error"] = str(e)
                if schm_included:
                    ctlg_obj["schemas"].append(schm_obj)
                continue

            for table in tables:
                if matches(table.name, exclude):
                    continue
                if not (schm_included or matches(table.name, include)):
                    continue

                schm_obj["tables"].append({
                    "name": table.name,
                    "type": table.table_type.value if table.table_type else None,
                    "comment": table.comment,
                    "columns": [
                        {"name": c.name, "type": c.type_text, "nullable": c.nullable, "comment": c.comment}
                        for c in (table.columns or [])
                    ],
                })

            if schm_included or schm_obj["tables"]:
                ctlg_obj["schemas"].append(schm_obj)

        if ctlg_included or ctlg_obj["schemas"]:
            result.append(ctlg_obj)

    return result
