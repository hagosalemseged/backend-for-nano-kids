"""remove_lesson_translation_unique_constraint

Revision ID: 2b3a9a90d9f8
Revises: e8cd3670805f
Create Date: 2026-07-12 17:20:14.898829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b3a9a90d9f8'
down_revision: Union[str, None] = 'e8cd3670805f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("uq_lesson_language", "lesson_translations", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint("uq_lesson_language", "lesson_translations", ["unit_id", "language_id"])
