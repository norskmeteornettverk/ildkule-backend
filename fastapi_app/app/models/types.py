"""Shared SQLAlchemy column types.

These helpers keep the ORM and the MySQL bootstrap schema aligned while still
working cleanly with SQLite in tests.
"""

from sqlalchemy import Integer
from sqlalchemy.dialects import mysql


def unsigned_int():
    """Return an integer type that becomes UNSIGNED on MySQL."""

    return Integer().with_variant(mysql.INTEGER(unsigned=True), "mysql")
