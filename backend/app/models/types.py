"""Shared column helpers for the ORM models."""
from enum import Enum

from sqlalchemy import Enum as SAEnum


def enum_column(enum_cls: type[Enum]) -> SAEnum:
    """Portable enum column that stores the enum *value* (not its name).

    ``native_enum=False`` renders as VARCHAR + CHECK, which behaves
    identically on SQLite and MySQL — important for the Phase 9 DB switch.
    """
    return SAEnum(
        enum_cls,
        values_callable=lambda e: [member.value for member in e],
        native_enum=False,
        validate_strings=True,
    )
