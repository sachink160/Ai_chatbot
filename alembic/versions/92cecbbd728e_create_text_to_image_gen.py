"""create Text to Image Gen

Revision ID: 92cecbbd728e
Revises: 2b968ed498d6
Create Date: 2025-11-06 14:56:56.318950
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92cecbbd728e'
down_revision = '2b968ed498d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'image_generations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('prompt', sa.String(), nullable=True),
        sa.Column('negative_prompt', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('guidance_scale', sa.Float(), nullable=True),
        sa.Column('num_inference_steps', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('seed', sa.String(), nullable=True),
        sa.Column('output_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('image_generations')
