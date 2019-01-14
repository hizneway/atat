"""add funding columns to task order

Revision ID: 4536f50b25bc
Revises: 3d346b5c8f19
Create Date: 2019-01-10 14:24:03.101309

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4536f50b25bc'
down_revision = '3d346b5c8f19'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('task_orders', sa.Column('attachment_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('task_orders', sa.Column('performance_length', sa.Integer(), nullable=True))
    op.create_foreign_key('task_orders_attachments_attachment_id', 'task_orders', 'attachments', ['attachment_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('task_orders_attachments_attachment_id', 'task_orders', type_='foreignkey')
    op.drop_column('task_orders', 'performance_length')
    op.drop_column('task_orders', 'attachment_id')
    # ### end Alembic commands ###
