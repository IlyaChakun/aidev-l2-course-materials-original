"""Central settings. Everything comes from environment variables with demo defaults."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6371")
PG_ADMIN_DSN = os.getenv("PG_ADMIN_DSN", "postgresql://postgres:postgres@localhost:5451/kb")
PG_APP_DSN = os.getenv("PG_APP_DSN", "postgresql://app_user:app_pass@localhost:5451/kb")
API_URL = os.getenv("API_URL", "http://localhost:8471")

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIM = 1536
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

COLLECTION = "kb_shared"          # shared collection, payload-based partitioning
TIERED_COLLECTION = "kb_tiered"   # custom sharding, tiered multitenancy

SHARED_CORPUS = Path(os.getenv("SHARED_CORPUS", ROOT.parent / "_shared" / "corpus"))
TENANTS_DIR = ROOT / "tenants"
CORPUS_DIR = ROOT / "corpus"      # generated per-tenant corpora
CACHE_DIR = ROOT / "data" / "cache"
CONFIG_DIR = ROOT / "config"

# The unsafe endpoint exists only so the leak can be shown live. Never enable in prod.
DEMO_UNSAFE_ENABLED = os.getenv("DEMO_UNSAFE_ENABLED", "0") == "1"
