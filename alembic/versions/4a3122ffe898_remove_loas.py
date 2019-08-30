"""Remove LOAs

Revision ID: 4a3122ffe898
Revises: fda6bd7e1b65
Create Date: 2019-08-29 16:28:45.017550

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4a3122ffe898' # pragma: allowlist secret
down_revision = 'fda6bd7e1b65' # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('clins_task_order_id_fkey', 'clins', type_='foreignkey')
    op.create_foreign_key('clins_task_order_id_fkey', 'clins', 'task_orders', ['task_order_id'], ['id'])
    op.drop_column('clins', 'loas')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('clins', sa.Column('loas', postgresql.ARRAY(sa.VARCHAR()), server_default=sa.text("'{}'::character varying[]"), autoincrement=False, nullable=True))
    op.drop_constraint('clins_task_order_id_fkey', 'clins', type_='foreignkey')
    op.create_foreign_key('clins_task_order_id_fkey', 'clins', 'task_orders', ['task_order_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###
