"""baseline (current schema)

Revision ID: 000000000000
Revises: 
Create Date: 2025-10-13 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '000000000000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Empty baseline; represents the current schema state
    pass


def downgrade():
    # No-op for baseline
    pass
