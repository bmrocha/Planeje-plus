"""Update budget model with new fields

Revision ID: c2db5c2185a7
Revises: 06566c7081b0
Create Date: 2024-11-30 00:14:10.366469

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2db5c2185a7'
down_revision = '06566c7081b0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('attachment')
    op.drop_table('agency')
    with op.batch_alter_table('budget', schema=None) as batch_op:
        batch_op.add_column(sa.Column('requested_name', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('sector', sa.String(length=100), nullable=False))
        batch_op.drop_column('requested_agency')
        batch_op.drop_column('agency')
        batch_op.drop_column('justification')
        batch_op.drop_column('company')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('agency')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agency', sa.VARCHAR(length=50), nullable=True))

    with op.batch_alter_table('budget', schema=None) as batch_op:
        batch_op.add_column(sa.Column('company', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('justification', sa.TEXT(), nullable=True))
        batch_op.add_column(sa.Column('agency', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('requested_agency', sa.VARCHAR(length=100), nullable=False))
        batch_op.drop_column('sector')
        batch_op.drop_column('requested_name')

    op.create_table('agency',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.VARCHAR(length=100), nullable=False),
    sa.Column('created_by', sa.INTEGER(), nullable=False),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('attachment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('budget_id', sa.INTEGER(), nullable=False),
    sa.Column('filename', sa.VARCHAR(length=200), nullable=True),
    sa.Column('path', sa.VARCHAR(length=500), nullable=True),
    sa.ForeignKeyConstraint(['budget_id'], ['budget.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###
