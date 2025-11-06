alembic current      # See current database revision
alembic heads        # Show latest migration (head)
alembic history      # Show all migrations

# Auto-generate from model changes (RECOMMENDED)
alembic revision --autogenerate -m "your description here"

# Create empty migration for manual SQL
alembic revision -m "your description here"

alembic upgrade head    # Apply all pending migrations
alembic upgrade +1      # Apply next migration only
alembic upgrade <rev>   # Upgrade to specific revision (e.g., alembic upgrade f7195268e430)

alembic downgrade -1    # Rollback one migration
alembic downgrade <rev> # Rollback to specific revision
alembic downgrade base  # Rollback all migrations

alembic upgrade head --sql  # See what SQL would be executed
