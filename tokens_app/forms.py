from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Optional, DataRequired

from constants import MAX_LEN_LABEL, MAX_LEN_PIN, MIN_USER_PIN


class FormFormatToken(FlaskForm):
    """Форма с данными для форматирования токена."""
    model = StringField(
        label='Модель',
        render_kw={'readonly': True},
        # validators=[DataRequired()]
    )
    min_pin_user = StringField(label='Min pin', render_kw={'readonly': True})
    serial_num_raw = StringField(
        label='SN программный',
        render_kw={'readonly': True},
        # validators=[DataRequired()]
    )
    serial_num = StringField(
        label='SN на корпусе',
        render_kw={'readonly': True},
        # validators=[DataRequired()]
    )
    label = StringField(
        label='Имя токена',
        validators=[Length(max=MAX_LEN_LABEL)]
    )
    new_pin_user = StringField(
        label='Новый pin пользователя',
        validators=[
            Length(
                message=(f'Длина должна быть от {MIN_USER_PIN} до '
                         f'{MAX_LEN_PIN} символов'),
                min=MIN_USER_PIN,
                max=MAX_LEN_PIN
            ),
            Optional()
        ]
    )
    submit_format = SubmitField(label='Форматировать')
