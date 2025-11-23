from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String

from tokens_app import db


class Users_LDAP(db.Model):
    """Пользователи загружаемые из LDAP."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(20), index=True)
    tab_num: Mapped[str] = mapped_column(String, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(256), index=True)
