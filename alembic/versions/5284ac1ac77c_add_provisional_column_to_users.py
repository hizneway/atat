"""add provisional column to users

Revision ID: 5284ac1ac77c
Revises: e0fc3cd315c1
Create Date: 2018-10-25 11:04:49.879393

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5284ac1ac77c'
down_revision = 'e0fc3cd315c1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('provisional', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'provisional')
    # ### end Alembic commands ###
