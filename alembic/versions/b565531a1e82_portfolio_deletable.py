"""Portfolio deletable

Revision ID: b565531a1e82
Revises: c19d6129cca1
Create Date: 2019-06-06 09:16:08.803603

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b565531a1e82'
down_revision = 'c19d6129cca1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('portfolios', sa.Column('deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('portfolios', 'deleted')
    # ### end Alembic commands ###
