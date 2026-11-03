"""split user settings into user_settings table

Revision ID: 2ba9564d0162
Revises: 6f107b0bfde0
Create Date: 2026-11-02 17:14:52.179045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2ba9564d0162'
down_revision: Union[str, Sequence[str], None] = '6f107b0bfde0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'reminders_enabled',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
        sa.Column(
            'reminder_interval_hours',
            sa.Integer(),
            server_default='48',
            nullable=False,
        ),
        sa.Column(
            'reminder_schedule',
            sa.String(length=20),
            server_default='after_work',
            nullable=False,
        ),
        sa.Column(
            'timezone',
            sa.String(length=50),
            server_default='Europe/Moscow',
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Переносим настройки существующих пользователей в новую таблицу,
    # иначе после удаления колонок из users они будут потеряны.
    op.execute(
        """
        INSERT INTO user_settings (
            id,
            reminders_enabled,
            reminder_interval_hours,
            reminder_schedule,
            timezone
        )
        SELECT
            id,
            reminders_enabled,
            reminder_interval_hours,
            reminder_schedule,
            timezone
        FROM users
        """
    )

    # notifications.telegram_id хранил users.id (так была задана связь),
    # поэтому переносим значение как есть.
    op.add_column(
        'notifications',
        sa.Column('user_id', sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE notifications
        SET user_id = telegram_id
        """
    )
    op.alter_column('notifications', 'user_id', nullable=False)
    op.create_unique_constraint(
        'uq_notifications_user_id',
        'notifications',
        ['user_id'],
    )
    op.drop_constraint(
        'notifications_telegram_id_fkey',
        'notifications',
        type_='foreignkey',
    )
    op.create_foreign_key(
        'fk_notifications_user_id_users',
        'notifications',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_column('notifications', 'last_reminder_sent_at')
    op.drop_column('notifications', 'telegram_id')

    op.create_unique_constraint(
        'uq_users_telegram_id',
        'users',
        ['telegram_id'],
    )
    op.drop_column('users', 'reminder_schedule')
    op.drop_column('users', 'reminders_enabled')
    op.drop_column('users', 'reminder_interval_hours')
    op.drop_column('users', 'timezone')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'reminders_enabled',
            sa.Boolean(),
            server_default=sa.text('true'),
            nullable=False,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'reminder_interval_hours',
            sa.Integer(),
            server_default='48',
            nullable=False,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'reminder_schedule',
            sa.String(length=20),
            server_default='after_work',
            nullable=False,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'timezone',
            sa.String(length=50),
            server_default='Europe/Moscow',
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE users AS u
        SET
            reminders_enabled = s.reminders_enabled,
            reminder_interval_hours = s.reminder_interval_hours,
            reminder_schedule = s.reminder_schedule,
            timezone = s.timezone
        FROM user_settings AS s
        WHERE s.id = u.id
        """
    )

    op.add_column(
        'notifications',
        sa.Column('telegram_id', sa.Integer(), nullable=True),
    )
    op.execute(
        """
        UPDATE notifications
        SET telegram_id = user_id
        """
    )
    op.alter_column('notifications', 'telegram_id', nullable=False)
    op.add_column(
        'notifications',
        sa.Column(
            'last_reminder_sent_at',
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.drop_constraint(
        'fk_notifications_user_id_users',
        'notifications',
        type_='foreignkey',
    )
    op.drop_constraint(
        'uq_notifications_user_id',
        'notifications',
        type_='unique',
    )
    op.drop_column('notifications', 'user_id')
    op.create_foreign_key(
        'notifications_telegram_id_fkey',
        'notifications',
        'users',
        ['telegram_id'],
        ['id'],
        ondelete='CASCADE',
    )

    op.drop_constraint('uq_users_telegram_id', 'users', type_='unique')
    op.drop_table('user_settings')
