from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import insert, delete

from constants import DEFAULT_USER_PIN
from tokens.exceptions import FormatException
from tokens.tokens import Token
from tokens.utils import get_tokens
from tokens_app.forms import FormFormatToken

from . import app, db
from .ldap import get_users_from_ou_kerberos
from .models import Users_LDAP, Date_Load_Data


@app.route('/load_ldap', methods=['GET'])
def load_ldap():
    users = get_users_from_ou_kerberos()

    with db.engine.connect() as conn:
        conn.execute(delete(Date_Load_Data))
        conn.execute(insert(Date_Load_Data).values({'count': len(users)}))
        conn.execute(delete(Users_LDAP))
        conn.execute(insert(Users_LDAP).values(users))
        conn.commit()
    return redirect(url_for('index_view'))


@app.route('/', methods=['GET', 'POST'])
def index_view():

    date_load = Date_Load_Data.query.first()

    tokens: dict[str, Token] = {}
    try:
        tokens = get_tokens()
    except FileNotFoundError as err:
        flash(str(err), 'danger')
    form = FormFormatToken()
    content = {'form': form, 'tokens': tokens, 'date_load': date_load}
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
            # tokens = get_tokens()
            return redirect(url_for('index_view'))

    return render_template('index.html', **content)
