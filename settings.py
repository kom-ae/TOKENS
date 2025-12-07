import os


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    WTF_CSRF_TIME_LIMIT = 86400
    WTF_CSRF_FIELD_ERROR = ('Срок действия токена безопасности истёк. '
                            'Пожалуйста, обновите страницу.')
