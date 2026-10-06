import os

# Tests must not depend on a developer's local .env file.  These are read by
# config at import time, so the defaults have to be in place before any test
# module is imported.
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-not-for-production-use")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("OPENROUTE_API_KEY", "test-openroute-key")