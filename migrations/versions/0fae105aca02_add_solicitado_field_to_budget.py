"""Add solicitado field to Budget

Revision ID: 0fae105aca02
Revises: c2db5c2185a7
Create Date: 2024-12-02 10:21:36.475796

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0fae105aca02'
down_revision = 'c2db5c2185a7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('budget', schema=None) as batch_op:
        batch_op.add_column(sa.Column('solicitado', sa.String(length=100), nullable=False))

    with op.batch_alter_table('email_config', schema=None) as batch_op:
        batch_op.drop_column('updated_at')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('role',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)

    with op.batch_alter_table('email_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DATETIME(), nullable=True))

    with op.batch_alter_table('budget', schema=None) as batch_op:
        batch_op.drop_column('solicitado')

    # ### end Alembic commands ###
