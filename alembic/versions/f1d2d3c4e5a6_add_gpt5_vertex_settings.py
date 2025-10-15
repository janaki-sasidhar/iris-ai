"""Add provider-specific settings columns

Revision ID: f1d2d3c4e5a6
Revises: 7c91f10cb583
Create Date: 2025-10-15 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1d2d3c4e5a6'
down_revision: Union[str, None] = '7c91f10cb583'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gemini_thinking_tokens', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('gpt_reasoning_effort', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('gpt_verbosity', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('gpt_search_context_size', sa.String(length=10), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('gpt_search_context_size')
        batch_op.drop_column('gpt_verbosity')
        batch_op.drop_column('gpt_reasoning_effort')
        batch_op.drop_column('gemini_thinking_tokens')

