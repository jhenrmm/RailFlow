from typing import Any, cast

from models import RouteAnalysisHistory
from services.security import hash_password, verify_password


def test_scrypt_password_hash_verifies_and_rejects_wrong_password():
    password_hash = hash_password("safe-password-123")

    assert password_hash.startswith("scrypt$")
    assert verify_password("safe-password-123", password_hash)
    assert not verify_password("wrong-password", password_hash)


def test_history_has_index_for_user_and_created_at():
    table = cast(Any, RouteAnalysisHistory.__table__)
    indexes = {index.name: tuple(index.columns.keys()) for index in table.indexes}

    assert indexes["ix_route_analysis_history_user_created"] == ("user_id", "created_at")
