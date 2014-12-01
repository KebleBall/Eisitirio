# coding: utf-8
from flask import Flask
from os import environ

app = Flask(__name__)

app.config.from_pyfile('config/default.py')
