"""convert_test_case_type_to_string

Revision ID: 8484c07ec3d6
Revises: db0c65595fea
Create Date: 2025-05-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8484c07ec3d6'
down_revision: Union[str, None] = 'db0c65595fea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert test_case type from enum to string."""
    # Create a new column as VARCHAR
    op.add_column('test_cases', sa.Column('type_new', sa.String(), nullable=True))
    
    # Copy data from enum to string column
    op.execute("UPDATE test_cases SET type_new = type::text")
    
    # Make the new column not nullable
    op.alter_column('test_cases', 'type_new', nullable=False)
    
    # Drop the old column
    op.drop_column('test_cases', 'type')
    
    # Rename the new column to the original name
    op.alter_column('test_cases', 'type_new', new_column_name='type')
    
    # Drop the enum type (only if no other columns use it)
    op.execute("DROP TYPE IF EXISTS testcasetype")


def downgrade() -> None:
    """Convert test_case type from string back to enum."""
    # Create the enum type again
    op.execute("CREATE TYPE testcasetype AS ENUM ('LLM', 'CONVERSATIONAL', 'MULTIMODAL')")
    
    # Create a new column with the enum type
    op.add_column('test_cases', sa.Column('type_enum', sa.Enum('LLM', 'CONVERSATIONAL', 'MULTIMODAL', 
                                                         name='testcasetype'), nullable=True))
    
    # Copy data from string to enum column
    op.execute("UPDATE test_cases SET type_enum = type::testcasetype")
    
    # Make the new column not nullable
    op.alter_column('test_cases', 'type_enum', nullable=False)
    
    # Drop the string column
    op.drop_column('test_cases', 'type')
    
    # Rename the new column to the original name
    op.alter_column('test_cases', 'type_enum', new_column_name='type')