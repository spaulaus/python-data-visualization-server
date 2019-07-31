import keyring
import psycopg2

import plotly
import plotly.graph_objs as go

import pandas as pd
import json

import time

from flask import Flask, render_template, request, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'you-will-never-guess'


class HistogramSelection(FlaskForm):
    crate = StringField('Crate', validators=[DataRequired()])
    slot = StringField('Slot', validators=[DataRequired()])
    channel = StringField('Channel', validators=[DataRequired()])
    table = StringField('Table', validators=[DataRequired()])
    submit = SubmitField('Display Energy Histogram')


def create_plot(table, crate, slot, chan):
    try:
        connection = psycopg2.connect(user='postgres',
                                      password=keyring.get_password('localhost', 'postgres'),
                                      host='localhost', port=5432, database='bagel')
        start_time = time.time()
        cursor = connection.cursor()
        sql = 'select energy from %s where energy > 0 and energy < 10000 and crate=%s and slot=%s and channel=%s;' % (table, crate, slot, chan)
        cursor.execute(sql)
        df = pd.DataFrame.from_dict(cursor.fetchall())

        data = [
            go.Histogram(
                x=df[0],  # assign x as the dataframe column 'x'
            )
        ]

        graphJSON = json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)

        print(time.time() - start_time)

        return graphJSON
    except psycopg2.Error as ex:
        print("Error connecting to db.", ex)


@app.route('/hist')
def hist():
    bar = create_plot('test', 0, 2, 5)
    return render_template('energy.html', plot=bar)


@app.route('/', methods=['GET', 'POST'])
def choose_histogram():
    form = HistogramSelection()
    if request.method == 'POST':
        bar = create_plot(form.table._value(), form.crate._value(), form.slot._value(),
                          form.channel._value())
        return render_template('energy.html', plot=bar)
    return render_template('form.html', title='Energy Histogram', form=form)


if __name__ == '__main__':
    app.run()
