"""Add reset_token/reset_token_expires to users for password reset

Revision ID: 6f2b9c1a4e57
Revises: 113ddf41ede3
Create Date: 2026-09-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6f2b9c1a4e57'
down_revision = '113ddf41ede3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reset_token', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('reset_token_expires', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_users_reset_token'), ['reset_token'], unique=False)


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_reset_token'))
        batch_op.drop_column('reset_token_expires')
        batch_op.drop_column('reset_token')
