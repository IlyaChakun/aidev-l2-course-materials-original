import sqlite3
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA = REPO_ROOT / "db" / "schema.sqlite.sql"
SEED = REPO_ROOT / "db" / "seed.sql"


def make_db(seed: bool = True) -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "test.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if seed:
        conn.executescript(SEED.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    return tmp, path


def fixed_clock(value: str = "2030-01-01T00:00:00Z"):
    return lambda: value
