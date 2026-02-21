# Database Migrations

This directory contains Alembic database migrations for the factory-service.

## Usage

### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

### Apply migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Upgrade one step
alembic upgrade +1
```

### Downgrade migrations

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade all
alembic downgrade base
```

### View migration history

```bash
# Show current revision
alembic current

# Show history
alembic history

# Show pending migrations
alembic history --verbose
```

## Migration Locking

To prevent concurrent migrations:

1. Use database advisory locks (PostgreSQL)
2. Use distributed locks (Redis)
3. Use deployment coordination (single instance)

Current strategy: **Single deployment instance** (Cloud Run revision rollout)

## Safe Migration Practices

1. **Always test migrations locally first**
2. **Backup database before production migrations**
3. **Write reversible migrations (downgrade)**
4. **Avoid data loss operations** (drop column, drop table)
5. **Use transactions** (transaction_per_migration=True)
6. **Monitor migration duration** (set timeout)

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `ALEMBIC_CONFIG`: Path to alembic.ini (optional)

## Example Migration

```python
"""Add api_keys table

Revision ID: 001
Revises: 
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('api_keys')
```

## Troubleshooting

### Migration fails mid-way

```bash
# Check current state
alembic current

# Manually fix database
# Then stamp to correct revision
alembic stamp <revision_id>
```

### Conflict between migrations

```bash
# Merge heads
alembic merge heads -m "Merge migrations"
```

### Reset migrations (dev only)

```bash
# Drop all tables
alembic downgrade base

# Reapply
alembic upgrade head
```
