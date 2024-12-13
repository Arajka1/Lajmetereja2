"""Update visitor_stats schema

Revision ID: 601f48a67a2d
Revises: 
Create Date: 2024-11-18 02:28:56.556119
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = "601f48a67a2d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Krijon ose përditëson tabelën 'visitor_stats'.
    """
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if "visitor_stats" not in tables:
        # Krijo tabelën nëse nuk ekziston
        op.create_table(
            "visitor_stats",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("ip", sa.String(length=100), nullable=False),
            sa.Column(
                "endpoint", sa.String(length=1000), nullable=False
            ),  # Rritja në 1000
            sa.Column(
                "timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()
            ),
            sa.Column("device", sa.String(length=200), nullable=True),
            sa.Column("browser", sa.String(length=200), nullable=True),
            sa.Column("timezone", sa.String(length=100), nullable=True),
            sa.Column("location", sa.String(length=200), nullable=True),
        )
    else:
        # Përditëso kolonat që mungojnë ose ndrysho specifikimet
        columns = [col["name"] for col in inspector.get_columns("visitor_stats")]

        with op.batch_alter_table("visitor_stats", schema=None) as batch_op:
            if "ip" not in columns:
                batch_op.add_column(
                    sa.Column("ip", sa.String(length=100), nullable=False)
                )
            if "endpoint" not in columns:
                batch_op.add_column(
                    sa.Column("endpoint", sa.String(length=1000), nullable=False)
                )
            else:
                # Përditëso kolonën 'endpoint' në 1000 karaktere
                batch_op.alter_column(
                    "endpoint", type_=sa.String(length=1000), existing_nullable=False
                )

            if "timestamp" not in columns:
                batch_op.add_column(
                    sa.Column(
                        "timestamp",
                        sa.DateTime(),
                        nullable=False,
                        server_default=sa.func.now(),
                    )
                )
            if "device" not in columns:
                batch_op.add_column(
                    sa.Column("device", sa.String(length=200), nullable=True)
                )
            if "browser" not in columns:
                batch_op.add_column(
                    sa.Column("browser", sa.String(length=200), nullable=True)
                )
            if "timezone" not in columns:
                batch_op.add_column(
                    sa.Column("timezone", sa.String(length=100), nullable=True)
                )
            if "location" not in columns:
                batch_op.add_column(
                    sa.Column("location", sa.String(length=200), nullable=True)
                )


def downgrade():
    """
    Kthen mbrapsht ndryshimet ose heq tabelën nëse është e nevojshme.
    """
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if "visitor_stats" in tables:
        columns = [col["name"] for col in inspector.get_columns("visitor_stats")]

        with op.batch_alter_table("visitor_stats", schema=None) as batch_op:
            if "location" in columns:
                batch_op.drop_column("location")
            if "timezone" in columns:
                batch_op.drop_column("timezone")
            if "browser" in columns:
                batch_op.drop_column("browser")
            if "device" in columns:
                batch_op.drop_column("device")
            if "endpoint" in columns:
                batch_op.alter_column(
                    "endpoint", type_=sa.String(length=100)
                )  # Kthehu në 100 karaktere

        # Nëse dëshiron të heqësh komplet tabelën (opsionale)
        op.drop_table("visitor_stats")
