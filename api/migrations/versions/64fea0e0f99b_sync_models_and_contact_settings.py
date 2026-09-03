"""sync_models_and_contact_settings

Revision ID: 64fea0e0f99b
Revises: 8d3fb6296a31
Create Date: 2026-09-03 20:49:09.601023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '64fea0e0f99b'
down_revision: Union[str, Sequence[str], None] = '8d3fb6296a31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    has_faqs = inspector.has_table("faqs")

    if not has_faqs:
        op.create_table(
            'faqs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('answer', sa.Text(), nullable=False),
            sa.Column('category', sa.String(length=50), server_default='general', nullable=False),
            sa.Column('display_order', sa.Integer(), server_default='0', nullable=False),
            sa.Column('is_published', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_faqs_category'), 'faqs', ['category'], unique=False)
    else:
        op.alter_column('faqs', 'created_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   nullable=False,
                   existing_server_default=sa.text('now()'))
        op.alter_column('faqs', 'updated_at',
                   existing_type=postgresql.TIMESTAMP(timezone=True),
                   nullable=False,
                   existing_server_default=sa.text('now()'))
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('faqs')]
        if 'ix_faqs_is_published' in existing_indexes:
            op.drop_index('ix_faqs_is_published', table_name='faqs')

    # 2. Ensure subscription_plans columns exist
    sub_plan_cols = [c['name'] for c in inspector.get_columns('subscription_plans')]
    if 'interval' not in sub_plan_cols:
        op.add_column('subscription_plans', sa.Column('interval', sa.String(length=20), server_default='monthly', nullable=False))
    if 'has_trial' not in sub_plan_cols:
        op.add_column('subscription_plans', sa.Column('has_trial', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    else:
        op.alter_column('subscription_plans', 'has_trial',
                   existing_type=sa.BOOLEAN(),
                   nullable=False,
                   existing_server_default=sa.text('false'))
    if 'trial_duration_days' not in sub_plan_cols:
        op.add_column('subscription_plans', sa.Column('trial_duration_days', sa.Integer(), server_default='0', nullable=True))

    # 3. Ensure user_subscriptions columns exist
    user_sub_cols = [c['name'] for c in inspector.get_columns('user_subscriptions')]
    if 'is_trial' not in user_sub_cols:
        op.add_column('user_subscriptions', sa.Column('is_trial', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    else:
        op.alter_column('user_subscriptions', 'is_trial',
                   existing_type=sa.BOOLEAN(),
                   nullable=False,
                   existing_server_default=sa.text('false'))

    # 4. Ensure users columns exist
    user_cols = [c['name'] for c in inspector.get_columns('users')]
    if 'has_used_trial' not in user_cols:
        op.add_column('users', sa.Column('has_used_trial', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    else:
        op.alter_column('users', 'has_used_trial',
                   existing_type=sa.BOOLEAN(),
                   nullable=False,
                   existing_server_default=sa.text('false'))
    if 'referral_code' not in user_cols:
        op.add_column('users', sa.Column('referral_code', sa.String(length=30), nullable=True))
    if 'referred_by_id' not in user_cols:
        op.add_column('users', sa.Column('referred_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
        op.create_index(op.f('ix_users_referred_by_id'), 'users', ['referred_by_id'], unique=False)

    # 5. Ensure referral_code index is unique
    user_indexes = [idx['name'] for idx in inspector.get_indexes('users')]
    user_uniques = [u['name'] for u in inspector.get_unique_constraints('users')]
    if 'users_referral_code_key' in user_uniques:
        op.drop_constraint('users_referral_code_key', 'users', type_='unique')
    if 'ix_users_referral_code' in user_indexes:
        op.drop_index('ix_users_referral_code', table_name='users')
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_referral_code'), table_name='users')
    op.create_index(op.f('ix_users_referral_code'), 'users', ['referral_code'], unique=False)
    op.create_unique_constraint(op.f('users_referral_code_key'), 'users', ['referral_code'], postgresql_nulls_not_distinct=False)
    op.alter_column('users', 'has_used_trial',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('false'))
    op.alter_column('user_subscriptions', 'is_trial',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('false'))
    op.alter_column('subscription_plans', 'has_trial',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('false'))
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table("faqs"):
        op.drop_table('faqs')
