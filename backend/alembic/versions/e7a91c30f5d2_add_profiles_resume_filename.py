"""add profiles resume_filename for uploaded-file display

Revision ID: e7a91c30f5d2
Revises: b8e14f6a2c97
Create Date: 2026-07-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a91c30f5d2'
down_revision: Union[str, None] = 'b8e14f6a2c97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('profiles', sa.Column('resume_filename', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('profiles', 'resume_filename')
