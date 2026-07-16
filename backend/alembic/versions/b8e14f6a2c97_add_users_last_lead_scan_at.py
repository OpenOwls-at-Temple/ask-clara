"""add users last_lead_scan_at for manual scan limit

Revision ID: b8e14f6a2c97
Revises: 473b757cc096
Create Date: 2026-07-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8e14f6a2c97'
down_revision: Union[str, None] = '473b757cc096'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_lead_scan_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_lead_scan_at')
