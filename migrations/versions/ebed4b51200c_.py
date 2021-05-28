"""empty message

Revision ID: ebed4b51200c
Revises: 2d49572c7884
Create Date: 2021-05-28 11:51:20.524162

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebed4b51200c'
down_revision = '2d49572c7884'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('venue', sa.Column('genres', sa.String()))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('venue', 'genres')
    # ### end Alembic commands ###