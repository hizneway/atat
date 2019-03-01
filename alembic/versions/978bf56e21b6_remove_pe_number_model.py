"""Remove PE number model

Revision ID: 978bf56e21b6
Revises: c92cec2f32d4
Create Date: 2019-02-20 18:24:37.970323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '978bf56e21b6'
down_revision = 'c92cec2f32d4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pe_numbers')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pe_numbers',
    sa.Column('number', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('number', name='pe_numbers_pkey')
    )
    # ### end Alembic commands ###