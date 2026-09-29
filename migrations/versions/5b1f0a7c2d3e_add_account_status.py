"""add account validation status to users

Revision ID: 5b1f0a7c2d3e
Revises: 939b238e936a
Create Date: 2026-09-29 19:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5b1f0a7c2d3e'
down_revision: Union[str, Sequence[str], None] = '939b238e936a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

account_status = sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='accountstatus')


def upgrade() -> None:
    account_status.create(op.get_bind(), checkfirst=True)
    # Les comptes existants restent utilisables : ils sont considérés comme validés
    op.add_column('users', sa.Column('account_status', account_status, nullable=False, server_default='APPROVED'))
    op.add_column('users', sa.Column('reviewedAt', sa.DateTime(), nullable=True))
    # Les nouveaux comptes attendent la validation d'un administrateur
    op.alter_column('users', 'account_status', server_default='PENDING')


def downgrade() -> None:
    op.drop_column('users', 'reviewedAt')
    op.drop_column('users', 'account_status')
    account_status.drop(op.get_bind(), checkfirst=True)
