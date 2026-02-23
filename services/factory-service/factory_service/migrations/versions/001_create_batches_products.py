"""
Alembic migration: Create batches and products tables.

Revision ID: 001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_create_batches_products'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create batches table
    op.create_table(
        'batches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('factory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('merkle_root', sa.String(64), nullable=True),
        sa.Column('blockchain_tx', sa.String(255), nullable=True),
        sa.Column('blockchain_task_id', sa.String(255), nullable=True),
        sa.Column('batch_metadata', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('anchored_at', sa.DateTime(), nullable=True),
    )
    
    # Create indexes on batches
    op.create_index('idx_batch_factory_id', 'batches', ['factory_id'])
    op.create_index('idx_batch_status', 'batches', ['status'])
    op.create_index('idx_batch_created_at', 'batches', ['created_at'])
    op.create_index('idx_batch_factory_created', 'batches', ['factory_id', 'created_at'])
    op.create_index('idx_batch_status_created', 'batches', ['status', 'created_at'])
    op.create_index('idx_batch_blockchain_tx', 'batches', ['blockchain_tx'])
    
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('verification_url', sa.String(500), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='CASCADE'),
    )
    
    # Create indexes on products
    op.create_index('idx_product_token', 'products', ['token'], unique=True)
    op.create_index('idx_product_batch_id', 'products', ['batch_id'])
    op.create_index('idx_product_created_at', 'products', ['created_at'])
    op.create_index('idx_product_serial_number', 'products', ['serial_number'])
    op.create_index('idx_product_batch_created', 'products', ['batch_id', 'created_at'])


def downgrade():
    op.drop_table('products')
    op.drop_table('batches')
