"""
Medicine catalog model for autocomplete suggestions.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from clinic_app.database.connection import Base


class MedicineCatalog(Base):
    __tablename__ = "medicine_catalog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    form: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Tab, Cap, Syp, Inj, Oint, etc.
    default_strength: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. 500mg, 10mg

    def __repr__(self) -> str:
        return f"<MedicineCatalog {self.name}>"
