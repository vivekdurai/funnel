"""add_commentspace_subscription

Revision ID: 179dea70e558
Revises: 570f4ea99cda
Create Date: 2017-03-17 16:57:57.285501

"""

# revision identifiers, used by Alembic.
revision = '179dea70e558'
down_revision = '570f4ea99cda'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('commentspace_subscription',
      sa.Column('created_at', sa.DateTime(), nullable=False),
      sa.Column('updated_at', sa.DateTime(), nullable=False),
      sa.Column('status', sa.Integer(), nullable=False),
      sa.Column('user_id', sa.Integer(), nullable=False),
      sa.Column('commentspace_id', sa.Integer(), nullable=False),
      sa.Column('id', sa.Integer(), nullable=False),
      sa.ForeignKeyConstraint(['commentspace_id'], ['commentspace.id'], ),
      sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
      sa.PrimaryKeyConstraint('id'),
      sa.UniqueConstraint('user_id', 'commentspace_id')
    )


def downgrade():
    op.drop_table('commentspace_subscription')
