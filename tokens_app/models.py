from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tokens_app import db


class UsersLdap(db.Model):
    """Пользователи загружаемые из LDAP."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sAMAccountName: Mapped[str] = mapped_column(String(256), index=True)
    description: Mapped[str] = mapped_column(
        String(1024),
        index=True,
        nullable=True
    )
    cn: Mapped[str] = mapped_column(String(64), index=True)

    tokens: Mapped[list['Token']] = relationship(
        'Token',
        back_populates='user',
        lazy='selectin',
        cascade='all, delete-orphan',
    )


class DateLoadData(db.Model):
    """Данные о загрузке данных из LDAP."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.localtimestamp(),
    )


class Token(db.Model):
    """Токены привязанные к пользователям в качестве 2FA."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users_ldap.id', ondelete='CASCADE'),
        nullable=False
    )
    user: Mapped[UsersLdap] = relationship(
        'Users_LDAP',
        back_populates='tokens',
        lazy='selectin'
    )
