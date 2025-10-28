# Alembic Quick Reference

## Essential Commands

### Check Status
```bash
alembic current     # Current revision
alembic heads       # Show all heads
alembic history     # Show full history
```

### Create Migration
```bash
# Auto-generate from model changes (RECOMMENDED)
alembic revision --autogenerate -m "description"

# Create empty migration for manual SQL
alembic revision -m "description"
```

### Apply Migrations
```bash
alembic upgrade head    # Apply all pending
alembic upgrade +1      # Apply next only
alembic upgrade <rev>   # Upgrade to specific revision
```

### Rollback Migrations
```bash
alembic downgrade -1    # Rollback one
alembic downgrade <rev> # Rollback to specific
alembic downgrade base   # Rollback all
```

## Common Workflows

### New Feature with DB Changes
```bash
# 1. Edit models in app/models.py
# 2. Generate migration
alembic revision --autogenerate -m "add feature X"

# 3. Review generated migration
# 4. Apply it
alembic upgrade head
```

### Fix Current Schema
```bash
# 1. Update models to match current DB
# 2. Stamp current state
alembic stamp head

# 3. Now autogenerate will work correctly
```

### View Migration SQL
```bash
alembic upgrade head --sql  # Show SQL without executing
```

## Helper Script Usage

```bash
# Using the helper script
python alembic_helpers.py status
python alembic_helpers.py autogenerate "description"
python alembic_helpers.py upgrade
python alembic_helpers.py downgrade -1
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Database out of sync | `alembic upgrade head` |
| Can't locate revision | Check `alembic history` |
| DATABASE_URL not set | `export DATABASE_URL=postgresql://...` |
| Import errors | Check models imported in `alembic/env.py` |

## File Locations

- Config: `alembic.ini`
- Environment: `alembic/env.py`
- Migrations: `alembic/versions/*.py`
- Models: `app/models.py`
- Database: `app/database.py`

