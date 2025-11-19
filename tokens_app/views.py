from flask import render_template

from tokens.utils import get_tokens
from tokens.tokens import Token

from . import app


@app.route('/', methods=['GET', 'POST'])
def index_view():
    tokens: dict[str, Token] = get_tokens()

    return render_template('index.html', tokens=tokens)
