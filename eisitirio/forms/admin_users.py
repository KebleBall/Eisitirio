# coding: utf-8
"""Forms for views related to administrative tasks performed on users."""

from __future__ import unicode_literals

import flask_wtf
import wtforms
from wtforms import validators

from eisitirio import app
from eisitirio.forms import common

APP = app.APP

class AdminFeeForm(flask_wtf.Form):
    """Form for charging the user an admin fee."""

    reason = wtforms.TextAreaField(
        label='Reason for Admin Fee',
        validators=[
            validators.DataRequired(
                message='A reason must be given for charging the admin fee.'
            )
        ]
    )

    amount = wtforms.FormField(
        common.make_pounds_pence_subform_class(
            validate_range=True,
            message='The fee amount must be greater than 0.',
            min=1
        ),
        label='Fee Amount'
    )
