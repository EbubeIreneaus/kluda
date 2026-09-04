from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '23be59d77db3'
down_revision: Union[str, Sequence[str], None] = 'd624891c255d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'store_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_id', sa.UUID(), nullable=False),
        sa.Column('store_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('actor_name', sa.String(length=150), nullable=True),
        sa.Column('actor_email', sa.String(length=150), nullable=True),
        sa.Column('actor_role', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.String(length=150), nullable=True),
        sa.Column('target_name', sa.String(length=255), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.user_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['store_id'], ['stores.store_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_store_audit_logs_action'), 'store_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_store_audit_logs_actor_id'), 'store_audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_store_audit_logs_created_at'), 'store_audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_store_audit_logs_log_id'), 'store_audit_logs', ['log_id'], unique=True)
    op.create_index(op.f('ix_store_audit_logs_store_id'), 'store_audit_logs', ['store_id'], unique=False)
    op.create_index(op.f('ix_store_audit_logs_target_id'), 'store_audit_logs', ['target_id'], unique=False)
    op.create_index(op.f('ix_store_audit_logs_target_type'), 'store_audit_logs', ['target_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_store_audit_logs_target_type'), table_name='store_audit_logs')
    op.drop_index(op.f('ix_store_audit_logs_target_id'), table_name='store_audit_logs')
    op.drop_index(op.f('ix_store_audit_logs_store_id'), table_name='store_audit_logs')
    op.drop_index(op.f('ix_store_audit_logs_log_id'), table_name='store_audit_logs')
    op.drop_index(op.f('ix_store_audit_logs_created_at'), table_name='store_audit_logs')
    op.drop_index(op.f('ix_store_audit_logs_actor_id'), table_name='store_audit_logs')
    op.drop_index(op.f('ix_store_audit_logs_action'), table_name='store_audit_logs')
    op.drop_table('store_audit_logs')
