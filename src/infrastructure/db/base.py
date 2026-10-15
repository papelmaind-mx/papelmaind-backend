from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import UUID
import uuid

# Naming convention útil para Alembic
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


def uuid7() -> uuid.UUID:
    """Prefer uuid7 si está instalado; fallback uuid4 solo en dev."""
    try:
        from uuid_utils import uuid7 as _uuid7  # type: ignore
        return uuid.UUID(str(_uuid7()))
    except Exception:
        try:
            from uuid7 import uuid7 as _uuid7  # type: ignore
            return uuid.UUID(str(_uuid7()))
        except Exception:
            return uuid.uuid4()
