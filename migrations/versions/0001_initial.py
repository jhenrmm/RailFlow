"""initial schema"""

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("email", sa.String(255), nullable=False, unique=True), sa.Column("password", sa.String(255), nullable=False))
    op.create_table("route_analysis_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("origin_lat", sa.Float(), nullable=False), sa.Column("origin_lon", sa.Float(), nullable=False), sa.Column("destination_lat", sa.Float(), nullable=False), sa.Column("destination_lon", sa.Float(), nullable=False), sa.Column("profile", sa.String(32), nullable=False), sa.Column("distance_m", sa.Float(), nullable=False), sa.Column("duration_s", sa.Float(), nullable=False), sa.Column("weather_json", sa.Text(), nullable=False), sa.Column("analysis", sa.Text(), nullable=False), sa.Column("model", sa.String(64), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_table("revoked_tokens", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("token_hash", sa.String(64), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index("ix_revoked_tokens_token_hash", "revoked_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_revoked_tokens_token_hash", table_name="revoked_tokens")
    op.drop_table("revoked_tokens")
    op.drop_table("route_analysis_history")
    op.drop_table("users")
