"""Add versioned transcript pipeline and 32-dimensional embeddings.

Revision ID: 20260812_0003
Revises: 20260812_0002
Create Date: 2026-08-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260812_0003"
down_revision: str | None = "20260812_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_materials_transcript_status", "materials", type_="check")
    op.create_check_constraint(
        "ck_materials_transcript_status",
        "materials",
        "transcript_status IN ('NOT_IMPORTED', 'PROCESSING', 'READY', 'FAILED')",
    )
    op.create_table(
        "transcript_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("source_fixture", sa.String(length=120), nullable=False),
        sa.Column("normalization_version", sa.String(length=64), nullable=False),
        sa.Column("chunking_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
        sa.Column("failure_message", sa.String(length=240), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "status IN ('PROCESSING', 'READY', 'FAILED')", name="ck_transcript_versions_status"
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "material_id", "version", name="uq_transcript_versions_material_version"
        ),
    )
    op.create_index(
        op.f("ix_transcript_versions_material_id"),
        "transcript_versions",
        ["material_id"],
        unique=False,
    )
    op.create_index(
        "uq_transcript_versions_current_material",
        "transcript_versions",
        ["material_id"],
        unique=True,
        postgresql_where=sa.text("is_current"),
    )
    op.create_table(
        "transcript_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transcript_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.CheckConstraint("sequence >= 1", name="ck_segments_sequence"),
        sa.CheckConstraint("start_ms >= 0 AND end_ms > start_ms", name="ck_segments_time"),
        sa.ForeignKeyConstraint(
            ["transcript_version_id"], ["transcript_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "transcript_version_id", "sequence", name="uq_segments_version_sequence"
        ),
    )
    op.create_index(
        op.f("ix_transcript_segments_transcript_version_id"),
        "transcript_segments",
        ["transcript_version_id"],
        unique=False,
    )
    op.create_table(
        "transcript_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transcript_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("first_segment_sequence", sa.Integer(), nullable=False),
        sa.Column("last_segment_sequence", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.CheckConstraint("sequence >= 1", name="ck_chunks_sequence"),
        sa.CheckConstraint("start_ms >= 0 AND end_ms > start_ms", name="ck_chunks_time"),
        sa.ForeignKeyConstraint(
            ["transcript_version_id"], ["transcript_versions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("transcript_version_id", "sequence", name="uq_chunks_version_sequence"),
    )
    op.create_index(
        op.f("ix_transcript_chunks_transcript_version_id"),
        "transcript_chunks",
        ["transcript_version_id"],
        unique=False,
    )
    op.create_table(
        "chunk_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_version", sa.String(length=64), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["transcript_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id", name="uq_chunk_embeddings_chunk_id"),
    )


def downgrade() -> None:
    op.drop_table("chunk_embeddings")
    op.drop_index(
        op.f("ix_transcript_chunks_transcript_version_id"), table_name="transcript_chunks"
    )
    op.drop_table("transcript_chunks")
    op.drop_index(
        op.f("ix_transcript_segments_transcript_version_id"), table_name="transcript_segments"
    )
    op.drop_table("transcript_segments")
    op.drop_index("uq_transcript_versions_current_material", table_name="transcript_versions")
    op.drop_index(op.f("ix_transcript_versions_material_id"), table_name="transcript_versions")
    op.drop_table("transcript_versions")
    op.drop_constraint("ck_materials_transcript_status", "materials", type_="check")
    op.create_check_constraint(
        "ck_materials_transcript_status", "materials", "transcript_status IN ('NOT_IMPORTED')"
    )
