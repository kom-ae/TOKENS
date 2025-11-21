from flask import flash, render_template, request, redirect, url_for

from constants import DEFAULT_USER_PIN
from tokens.tokens import Token
from tokens.utils import get_tokens
from tokens_app.forms import FormFormatToken
from tokens.exceptions import FormatException

from . import app


@app.route('/', methods=['GET', 'POST'])
def index_view():
    tokens: dict[str, Token] = {}
    try:
        tokens = get_tokens()
    except FileNotFoundError as err:
        flash(str(err), 'danger')
    form = FormFormatToken()
    content = {'form': form, 'tokens': tokens}
    if form.validate_on_submit():

        sn_raw: str = form.serial_num_raw.data
        if sn_raw not in tokens:
            flash(f'Токен с sn_raw={sn_raw} не подключен.', 'info')
            return redirect(url_for('index_view'))
        user_pin: str = (form.new_pin_user.data
                         if form.new_pin_user.data else DEFAULT_USER_PIN)
        label: str = form.label.data

        action = request.form.get('submit_format')
        if action == '1':
            token = tokens[sn_raw]
            try:
                token.format(user_pin=user_pin, label=label)
                flash(
                    f'Токен SN_raw={sn_raw} label={label} отформатирован.',
                    category='success'
                )
            except FormatException as err:
                flash(str(err), category='danger')
            tokens = get_tokens()
            return redirect(url_for('index_view'))

    return render_template('index.html', **content)
