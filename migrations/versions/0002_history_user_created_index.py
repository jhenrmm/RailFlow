"""add history user-created index"""

from alembic import op

revision = "0002_history_user_created_index"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_route_analysis_history_user_created",
        "route_analysis_history",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_route_analysis_history_user_created", table_name="route_analysis_history")
