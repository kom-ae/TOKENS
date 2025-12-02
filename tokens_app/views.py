import threading
from flask import (Response, flash, jsonify, redirect, render_template,
                   request, url_for)
from sqlalchemy import delete, insert

from constants import DEFAULT_USER_PIN
from tokens.exceptions import FormatException
from tokens.tokens import Token
from tokens.utils import get_tokens
from tokens_app.forms import FormFormatToken

from . import app, db
from .ldap import get_users_from_ou_kerberos
from .models import Date_Load_Data, Users_LDAP

task = {}


@app.route('/update_tokens')
def update_tokens() -> Response:
    """Получение токенов.

    Возвращает информацию о токенах в JSON формате
    для заполнения таблицы токенов без перезагрузки страницы.
    """
    tokens: dict[str, Token] = {}
    try:
        tokens = get_tokens()
    except FileNotFoundError as err:
        flash(str(err), 'danger')
        return redirect(url_for('index_view'))

    return jsonify(
        [
            {
                'model': token.model,
                'serial_num_raw': token.serial_num_raw,
                'serial_num': token.serial_num,
                'label': token.label,
                'min_pin_user': token.min_pin_user,
            } for token in tokens.values()
        ]
    )


@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify()

    results = Users_LDAP.query.where(
        Users_LDAP.cn.like(f'{query}%'.lower()) |
        Users_LDAP.description.like(f'%{query}%') |
        Users_LDAP.sAMAccountName.like(f'%{query}%')
    ).limit(limit).all()

    return jsonify([
        {
            'cn': user.cn.title(),
            'description': user.description,
            'sAMAccountName': user.sAMAccountName

        } for user in results
    ])


@app.route('/load_ldap', methods=['GET'])
def load_ldap():
    users = get_users_from_ou_kerberos()

    with db.engine.connect() as conn:
        conn.execute(delete(Date_Load_Data))
        conn.execute(delete(Users_LDAP))
        conn.commit()
        conn.execute(insert(Date_Load_Data).values({'count': len(users)}))
        conn.execute(insert(Users_LDAP).values(users))
        conn.commit()
    return redirect(url_for('index_view'))


@app.route('/start_format', methods=['POST'])
def start_format() -> Response:
    """Форматирование токена в отдельном потоке."""

    task_id = request.form.get('task_id')
    tokens: dict[str, Token] = {}
    try:
        tokens = get_tokens()
    except FileNotFoundError as err:
        return jsonify({'status': 'error', 'error': str(err)})

    sn_raw: str = request.form.get('serial_num_raw')
    if sn_raw not in tokens:
        return jsonify({
            'status': 'error',
            'error': f'Токен с sn_raw={sn_raw} не подключен.'
        })

    form = FormFormatToken()
    form.model.data = request.form.get('model', '')
    form.min_pin_user.data = request.form.get('min_pin_user', '')
    form.serial_num_raw.data = request.form.get('serial_num_raw', '')
    form.serial_num.data = request.form.get('serial_num', '')
    form.label.data = request.form.get('label', '')
    form.new_pin_user.data = request.form.get('new_pin_user', '')

    if form.validate_on_submit():
        user_pin: str = (form.new_pin_user.data
                         if form.new_pin_user.data else DEFAULT_USER_PIN)
        label: str = form.label.data
        token = tokens[sn_raw]

        threading.Thread(target=thread_format, args=(
            token,
            user_pin,
            label,
            task_id,
        )).start()

        return jsonify({'status': 'started', 'task_id': task_id})
    else:
        message_errors = []
        for field, errors in form.errors.items():
            field_msg = getattr(form, field, field).label.text
            for error in errors:
                message_errors.append(f'{field_msg}: {error.rstrip('.')}.')
        return jsonify({
            'status': 'error',
            'error': message_errors
            })


def thread_format(
        token: Token,
        user_pin: str,
        label: str,
        task_id: str
) -> Response:
    try:
        token.format(user_pin=user_pin, label=label)
        task[task_id] = {'status': 'completed', 'sn_raw': token.serial_num_raw}
    except FormatException as err:
        task[task_id] = {
            'status': 'error',
            'error': f'Ошибка форматирования: {str(err)}'
        }


@app.route('/check_status/<task_id>')
def check_status(task_id: str):
    """Проверяет статус процесса форматирования токена."""
    if task_id in task:
        if task[task_id]['status'] == 'completed':
            return jsonify(task.pop(task_id))
        return jsonify(task[task_id])
    return jsonify({'status': 'not_found'})


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
            return redirect(url_for('index_view'))

    return render_template('index.html', **content)
