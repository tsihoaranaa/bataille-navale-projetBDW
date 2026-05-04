# Auteurs : GERGES Robin, RAONIMANANA Aaron

# Connexion à la base de données pour les tests du modèle.
# Le test est exécuté depuis mon_site/model/, ce fichier doit y être présent
# pour que l'import `from config import connexion` fonctionne.


from __future__ import annotations

from pathlib import Path
import tomllib

import psycopg


def _load_db_config() -> dict:
    repo_root = Path(__file__).resolve().parents[2]  # .../projetbdw2026
    config_path = repo_root / "config-bd.toml"
    data = config_path.read_text(encoding="utf-8")
    return tomllib.loads(data)


_cfg = _load_db_config()
_schema = _cfg.get("POSTGRESQL_SCHEMA", "public")

connexion = psycopg.connect(
    host=_cfg["POSTGRESQL_SERVER"],
    user=_cfg["POSTGRESQL_USER"],
    password=_cfg["POSTGRESQL_PASSWORD"],
    dbname=_cfg["POSTGRESQL_DATABASE"],
    port=_cfg.get("POSTGRESQL_PORT", 5432),
    autocommit=True,
)

_cursor = psycopg.ClientCursor(connexion)
_cursor.execute("SET search_path TO %s", [_schema])

