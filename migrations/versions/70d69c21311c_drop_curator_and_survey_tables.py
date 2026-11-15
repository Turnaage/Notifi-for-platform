"""drop curator and survey tables

Revision ID: 70d69c21311c
Revises: 4d264ba11427
Create Date: 2026-11-15 15:03:23.420089

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70d69c21311c'
down_revision: Union[str, Sequence[str], None] = '4d264ba11427'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Удаляем всё, что связано с кураторами и локальным хранением опросов."""
    inspector = sa.inspect(op.get_bind())

    foreign_keys = {
        fk["name"] for fk in inspector.get_foreign_keys("users")
    }
    columns = {
        column["name"] for column in inspector.get_columns("users")
    }
    tables = set(inspector.get_table_names())

    # Миграция должна переживать базу, где часть объектов уже удалена вручную.
    if "fk_users_curator_id_curators" in foreign_keys:
        op.drop_constraint(
            'fk_users_curator_id_curators',
            'users',
            type_='foreignkey',
        )

    if "curator_id" in columns:
        op.drop_column('users', 'curator_id')

    if "surveys" in tables:
        op.drop_table('surveys')

    if "curators" in tables:
        op.drop_table('curators')


def downgrade() -> None:
    """Возвращаем прежнюю схему кураторов и опросов."""
    op.create_table(
        'curators',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('reviews', sa.Integer(), nullable=False),
        sa.Column('avg_rate', sa.Numeric(precision=2, scale=1), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'surveys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('curator_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('question_1', sa.Integer(), nullable=True),
        sa.Column('question_2', sa.Integer(), nullable=True),
        sa.Column('question_3', sa.Integer(), nullable=True),
        sa.Column('avg_rate', sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['curator_id'],
            ['curators.id'],
            ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.add_column(
        'users',
        sa.Column('curator_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_users_curator_id_curators',
        'users',
        'curators',
        ['curator_id'],
        ['id'],
        ondelete='RESTRICT',
    )
