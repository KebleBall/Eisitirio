"""empty message

Revision ID: 3cbca143cf2d
Revises: 57ed98de66db
Create Date: 2016-05-17 17:11:09.910745

"""

# revision identifiers, used by Alembic.
revision = '3cbca143cf2d'
down_revision = '57ed98de66db'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('phone_verification_code', sa.Unicode(length=6), nullable=True))
    op.add_column('user', sa.Column('phone_verified', sa.Boolean(), nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'phone_verified')
    op.drop_column('user', 'phone_verification_code')
    ### end Alembic commands ###
