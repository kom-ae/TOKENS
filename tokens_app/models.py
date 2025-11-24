from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime

from tokens_app import db


class Users_LDAP(db.Model):
    """Пользователи загружаемые из LDAP."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sAMAccountName: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[str] = mapped_column(
        String(1024),
        index=True,
        nullable=True
    )
    cn: Mapped[str] = mapped_column(String(64), index=True)


class Date_Load_Data(db.Model):
    """Данные о загрузке данных из LDAP."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now()
    )
