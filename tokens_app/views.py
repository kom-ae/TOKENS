from flask import render_template

from . import app


@app.route('/', methods=['GET', 'POST'])
def index_view():
    pass
