"""slash user and staff into user only

Revision ID: cf9bd89b6b02
Revises: f4a0054ff26d
Create Date: 2026-09-02 14:51:51.677216

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'cf9bd89b6b02'
down_revision: Union[str, Sequence[str], None] = 'f4a0054ff26d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'store_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('store_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('permission', sa.JSON(), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'SUSPENDED', 'TERMINATED', name='staffstatus', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['store_id'], ['stores.store_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_store_members_store_id'), 'store_members', ['store_id'], unique=False)
    op.create_index(op.f('ix_store_members_user_id'), 'store_members', ['user_id'], unique=False)

    try:
        op.drop_constraint('stock_histories_staff_id_fkey', 'stock_histories', type_='foreignkey')
    except Exception:
        pass

    try:
        op.drop_column('stock_histories', 'staff_id')
    except Exception:
        pass

    op.drop_table('staff_sessions')
    op.drop_table('staff_notification_subscriptions')
    op.drop_table('owner_notification_subscriptions')

    op.drop_index(op.f('ix_staffs_access_token'), table_name='staffs')
    op.drop_index(op.f('ix_staffs_otp_token'), table_name='staffs')
    op.drop_index(op.f('ix_staffs_store_id'), table_name='staffs')
    op.drop_table('staffs')

    try:
        op.drop_index(op.f('ix_notification_subscriptions_user_type'), table_name='notification_subscriptions')
    except Exception:
        pass

    try:
        op.create_foreign_key(None, 'notification_subscriptions', 'users', ['user_id'], ['user_id'], ondelete='CASCADE')
    except Exception:
        pass

    try:
        op.drop_column('notification_subscriptions', 'user_type')
    except Exception:
        pass

    op.add_column('sales', sa.Column('user_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_sales_user_id'), 'sales', ['user_id'], unique=False)
    op.create_foreign_key(None, 'sales', 'users', ['user_id'], ['user_id'], ondelete='SET NULL')

    op.add_column('stock_histories', sa.Column('user_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_stock_histories_user_id'), 'stock_histories', ['user_id'], unique=False)
    op.create_foreign_key(None, 'stock_histories', 'users', ['user_id'], ['user_id'], ondelete='SET NULL')


def downgrade() -> None:
    op.add_column('stock_histories', sa.Column('staff_id', sa.VARCHAR(length=10), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'stock_histories', type_='foreignkey')
    op.create_foreign_key(op.f('stock_histories_staff_id_fkey'), 'stock_histories', 'staffs', ['staff_id'], ['staff_id'])
    op.drop_index(op.f('ix_stock_histories_user_id'), table_name='stock_histories')
    op.drop_column('stock_histories', 'user_id')
    op.drop_constraint(None, 'sales', type_='foreignkey')
    op.drop_index(op.f('ix_sales_user_id'), table_name='sales')
    op.drop_column('sales', 'user_id')
    op.add_column('notification_subscriptions', sa.Column('user_type', postgresql.ENUM('STAFF', 'USER', 'ADMIN', name='notificationrecipienttype'), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'notification_subscriptions', type_='foreignkey')
    op.create_index(op.f('ix_notification_subscriptions_user_type'), 'notification_subscriptions', ['user_type'], unique=False)
    op.create_table('staff_notification_subscriptions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('staff_id', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('sub_info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('staff_notification_subscriptions_pkey'))
    )
    op.create_index(op.f('ix_staff_notification_subscriptions_staff_id'), 'staff_notification_subscriptions', ['staff_id'], unique=False)
    op.create_table('staff_sessions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('session_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('staff_id', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('refresh_token_hash', sa.VARCHAR(length=64), autoincrement=False, nullable=False),
    sa.Column('ip_address', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
    sa.Column('user_agent', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('expired_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('previous_refresh_token_hash', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['staff_id'], ['staffs.staff_id'], name=op.f('staff_sessions_staff_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('staff_sessions_pkey'))
    )
    op.create_index(op.f('ix_staff_sessions_session_id'), 'staff_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_staff_sessions_refresh_token_hash'), 'staff_sessions', ['refresh_token_hash'], unique=True)
    op.create_index(op.f('ix_staff_sessions_previous_refresh_token_hash'), 'staff_sessions', ['previous_refresh_token_hash'], unique=False)
    op.create_table('owner_notification_subscriptions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('sub_info', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], name=op.f('owner_notification_subscriptions_user_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('owner_notification_subscriptions_pkey'))
    )
    op.create_index(op.f('ix_owner_notification_subscriptions_user_id'), 'owner_notification_subscriptions', ['user_id'], unique=False)
    op.create_table('staffs',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('staff_id', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('first_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('last_name', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('other_name', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('role', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('access_token', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
    sa.Column('last_login', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('otp_token', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('otp_expires_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('password', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('phone', sa.VARCHAR(length=100), autoincrement=False, nullable=True),
    sa.Column('store_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('permission', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('status', postgresql.ENUM('ACTIVE', 'SUSPENDED', 'TERMINATED', name='staffstatus', create_type=False), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('pin_hash', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('pin_salt', sa.VARCHAR(length=64), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['store_id'], ['stores.store_id'], name=op.f('staffs_store_id_fkey'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('staffs_pkey')),
    sa.UniqueConstraint('staff_id', name=op.f('staffs_staff_id_key'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_staffs_store_id'), 'staffs', ['store_id'], unique=False)
    op.create_index(op.f('ix_staffs_otp_token'), 'staffs', ['otp_token'], unique=True)
    op.create_index(op.f('ix_staffs_access_token'), 'staffs', ['access_token'], unique=True)
    op.drop_index(op.f('ix_store_members_user_id'), table_name='store_members')
    op.drop_index(op.f('ix_store_members_store_id'), table_name='store_members')
    op.drop_table('store_members')
