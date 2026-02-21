"""
Alembic migration: Create anchors table.

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_create_anchors'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create anchors table
    op.create_table(
        'anchors',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('merkle_root', sa.String(64), nullable=False),
        sa.Column('product_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('transaction_id', sa.String(255), nullable=True, unique=True),
        sa.Column('block_number', sa.BigInteger(), nullable=True),
        sa.Column('gas_used', sa.BigInteger(), nullable=True),
        sa.Column('gas_price_gwei', sa.Integer(), nullable=True),
        sa.Column('network', sa.String(50), nullable=True),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('anchored_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_anchor_batch_id', 'anchors', ['batch_id'])
    op.create_index('idx_anchor_merkle_root', 'anchors', ['merkle_root'])
    op.create_index('idx_anchor_status', 'anchors', ['status'])
    op.create_index('idx_anchor_transaction_id', 'anchors', ['transaction_id'])
    op.create_index('idx_anchor_block_number', 'anchors', ['block_number'])
    op.create_index('idx_anchor_created_at', 'anchors', ['created_at'])
    op.create_index('idx_anchor_status_created', 'anchors', ['status', 'created_at'])
    op.create_index('idx_anchor_batch_status', 'anchors', ['batch_id', 'status'])


def downgrade():
    op.drop_table('anchors')
