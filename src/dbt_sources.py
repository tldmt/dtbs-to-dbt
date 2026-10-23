import yaml

from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output" / "yml"

def write_dbt_sources(catalogs: list[dict], output_dir: Path = OUTPUT_DIR) -> list[Path]:
    """
    Write one dbt sources YAML per catalog.schema from collect() output.
        Layout: <output_dir>/<catalog>_<schema>.yml, each listing every table of that schema.
    """
    written = []

    for ctlg in catalogs:
        for schm in ctlg.get("schemas", []):
            if not schm["tables"]:
                continue

            source = {
                "name": f"{ctlg['name']}_{schm['name']}",
                "database": ctlg["name"],
                "schema": schm["name"],
            }
            if schm["comment"]:
                source["description"] = schm["comment"]
            source["tables"] = []

            for table in schm["tables"]:
                tbl = {"name": table["name"]}
                if table["comment"]:
                    tbl["description"] = table["comment"]
                tbl["columns"] = []
                source["tables"].append(tbl)

                for c in table["columns"]:
                    col = {"name": c["name"], "data_type": c["type"]}
                    if c["comment"]:
                        col["description"] = c["comment"]
                    if c["nullable"] is False:
                        col["data_tests"] = ["not_null"]
                    tbl["columns"].append(col)

            path = Path(output_dir) / f"{source['name']}.yml"
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w") as f:
                yaml.safe_dump({"version": 2, "sources": [source]}, f, sort_keys=False, allow_unicode=True)
            written.append(path)

    return written