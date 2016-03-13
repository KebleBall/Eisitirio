# coding: utf-8
"""Common components of forms."""

import wtforms
import wtforms_components
from wtforms import validators


class BlankIsZeroIntegerField(wtforms_components.IntegerField):
    """Integer field which treats a blank input as 0."""

    def process_formdata(self, valuelist):
        """Coerce the user input to an integer."""
        if valuelist:
            if valuelist[0] == '':
                self.data = 0
            else:
                try:
                    self.data = int(valuelist[0])
                except ValueError:
                    self.data = None
                    raise ValueError(self.gettext('Not a valid integer value'))


class PoundsPenceRange(object):
    """Validator for limiting the range of a PoundsPence FormField."""

    def __init__(self, message=None, **kwargs):
        self.message = message

        if 'min' in kwargs:
            self.min = kwargs['min']
        elif 'pounds_min' in kwargs or 'pence_min' in kwargs:
            self.min = (
                100 * kwargs.get('pounds_min', 0) +
                kwargs.get('pence_min', 0)
            )
        else:
            self.min = None

        if 'max' in kwargs:
            self.max = kwargs['max']
        elif 'pounds_max' in kwargs or 'pence_max' in kwargs:
            self.max = (
                100 * kwargs.get('pounds_max', 0) +
                kwargs.get('pence_max', 0)
            )
        else:
            self.max = None

    def __call__(self, form, field):
        value = field.data * 100 + form.pence.data

        if self.min is not None and value < self.min:
            if self.message is not None:
                raise wtforms.ValidationError(self.message)
            else:
                raise wtforms.ValidationError(
                    'Value must not be less than £{0:d}.{1:02d}'.format(
                        self.min / 100,
                        self.min % 100
                    )
                )

        if self.max is not None and value > self.max:
            if self.message is not None:
                raise wtforms.ValidationError(self.message)
            else:
                raise wtforms.ValidationError(
                    'Value must not be greater than £{0:d}.{1:02d}'.format(
                        self.max / 100,
                        self.max % 100
                    )
                )


def make_pounds_pence_subform_class(validate_range=False, **kwargs):
    """Make a subform for pounds and pence, optionally validating the amount."""

    if validate_range:
        pounds_validators = [PoundsPenceRange(**kwargs)]
    else:
        pounds_validators = []

    pounds_validators.append(
        validators.NumberRange(
            min=0,
            message='Pounds value must not be negative.'
        )
    )

    class PoundsPence(wtforms.Form):
        """Subform for getting an amount in pounds and pence."""

        pounds = BlankIsZeroIntegerField(
            label='Pounds',
            validators=pounds_validators
        )
        pence = BlankIsZeroIntegerField(
            label='Pence',
            validators=[
                validators.NumberRange(
                    min=0,
                    max=99,
                    message='Pence value must be between 0 and 99.'
                )
            ]
        )

    return PoundsPence
