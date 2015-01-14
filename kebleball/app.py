# coding: utf-8
import flask

app = flask.Flask('kebleball')

app.config.from_pyfile('config/default.py')
