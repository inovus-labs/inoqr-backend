"""add update_at triggers

Revision ID: 9ff893042d51
Revises: ccc5dcf0d685
Create Date: 2026-09-20 12:57:44.105013

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9ff893042d51"
down_revision: Union[str, Sequence[str], None] = "ccc5dcf0d685"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        CREATE TRIGGER trg_folders_updated_at
        BEFORE UPDATE ON folders
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at();
    """)

    op.execute("""
        CREATE TRIGGER trg_qr_codes_updated_at
        BEFORE UPDATE ON qr_codes
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at();
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DROP TRIGGER IF EXISTS trg_folders_updated_at ON folders;
        DROP TRIGGER IF EXISTS trg_qr_codes_updated_at ON qr_codes;

        DROP FUNCTION IF EXISTS update_updated_at();
    """)
    pass
