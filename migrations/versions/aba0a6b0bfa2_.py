"""empty message

Revision ID: aba0a6b0bfa2
Revises: 40901b4f11c3
Create Date: 2016-02-06 13:55:05.651423

"""

# revision identifiers, used by Alembic.
revision = 'aba0a6b0bfa2'
down_revision = '40901b4f11c3'

from alembic import op
import sqlalchemy as sa
from sqlalchemy import sql


def upgrade():
    op.alter_column(
        'transaction',
        'payment_method',
        existing_type=sa.Enum(
            'Battels',
            'Card',
            'OldCard',
            'Free',
            'Dummy'
        ),
        type_=sa.Enum(
            'Battels',
            'Card',
            'Free',
            'Dummy'
        ),
        nullable=False
    )

    op.alter_column(
        'statistic',
        'group',
        existing_type=sa.Enum(
            'Colleges',
            'Payments',
            'Sales',
        ),
        type_=sa.Enum(
            'Colleges',
            'Payments',
            'Sales',
            'college_users',
        ),
        nullable=False
    )

    conn = op.get_bind()

    conn.execute(sql.text("""
        UPDATE `statistic`
        SET `group`=:new_group
        WHERE `group`=:old_group
    """), old_group='Colleges', new_group='college_users')

    conn.execute(sql.text("""
        DELETE FROM `statistic`
        WHERE `group`!=:group
    """), group='college_users')

    op.alter_column(
        'statistic',
        'group',
        existing_type=sa.Enum(
            'Colleges',
            'Payments',
            'Sales',
            'college_users',
        ),
        type_=sa.Enum(
            'college_users',
            'payment_methods',
            'ticket_types',
            'total_ticket_sales',
            'guest_ticket_sales',
            'waiting',
        ),
        nullable=False
    )

def downgrade():
    op.alter_column(
        'statistic',
        'group',
        existing_type=sa.Enum(
            'college_users',
            'payment_methods',
            'ticket_types',
            'total_ticket_sales',
            'guest_ticket_sales',
            'waiting',
        ),
        type_=sa.Enum(
            'college_users',
            'payment_methods',
            'ticket_types',
            'total_ticket_sales',
            'guest_ticket_sales',
            'waiting',
            'Colleges',
        ),
        nullable=False
    )

    conn = op.get_bind()

    conn.execute(sql.text("""
        UPDATE `statistic`
        SET `group`=:new_group
        WHERE `group`=:old_group
    """), old_group='college_users', new_group='Colleges')

    conn.execute(sql.text("""
        DELETE FROM `statistic`
        WHERE `group`!=:group
    """), group='Colleges')

    op.alter_column(
        'statistic',
        'group',
        existing_type=sa.Enum(
            'college_users',
            'payment_methods',
            'ticket_types',
            'total_ticket_sales',
            'guest_ticket_sales',
            'waiting',
            'Colleges',
        ),
        type_=sa.Enum(
            'Colleges',
            'Payments',
            'Sales',
        ),
        nullable=False
    )

    op.alter_column(
        'transaction',
        'payment_method',
        existing_type=sa.Enum(
            'Battels',
            'Card',
            'Free',
            'Dummy'
        ),
        type_=sa.Enum(
            'Battels',
            'Card',
            'OldCard',
            'Free',
            'Dummy'
        ),
        nullable=False
    )
