from __future__ import annotations

import gettext
import re

from flask_babelhg import get_locale

import pycountry

from baseframe import _, __
from baseframe.forms.sqlalchemy import QuerySelectField
import baseframe.forms as forms

from ..models import Venue, VenueRoom

__all__ = ['VenueForm', 'VenuePrimaryForm', 'VenueRoomForm']

valid_color_re = re.compile(r'^[a-fA-F\d]{6}|[a-fA-F\d]{3}$')


@Venue.forms('main')
class VenueForm(forms.Form):
    title = forms.StringField(
        __("Name"),
        description=__("Name of the venue"),
        validators=[forms.validators.DataRequired(), forms.validators.Length(max=250)],
        filters=[forms.filters.strip()],
    )
    description = forms.MarkdownField(
        __("Description"), description=__("An optional note about the venue")
    )
    address1 = forms.StringField(
        __("Address (line 1)"),
        validators=[forms.validators.Optional(), forms.validators.Length(max=160)],
        filters=[forms.filters.strip()],
    )
    address2 = forms.StringField(
        __("Address (line 2)"),
        validators=[forms.validators.Optional(), forms.validators.Length(max=160)],
        filters=[forms.filters.strip()],
    )
    city = forms.StringField(
        __("City"),
        validators=[forms.validators.Optional(), forms.validators.Length(max=30)],
        filters=[forms.filters.strip()],
    )
    state = forms.StringField(
        __("State"),
        validators=[forms.validators.Optional(), forms.validators.Length(max=30)],
        filters=[forms.filters.strip()],
    )
    postcode = forms.StringField(
        __("Post code"),
        validators=[forms.validators.Optional(), forms.validators.Length(max=20)],
        filters=[forms.filters.strip()],
    )
    country = forms.SelectField(
        __("Country"),
        validators=[forms.validators.Optional(), forms.validators.Length(max=2)],
        choices=[],
        default='IN',
    )
    coordinates = forms.CoordinatesField(
        __("Location"),
        description=__("Pick a location on the map"),
        validators=[forms.validators.Optional(), forms.validators.ValidCoordinates()],
    )

    def set_queries(self):
        pycountry_locale = gettext.translation(
            'iso3166-2', pycountry.LOCALES_DIR, languages=[str(get_locale()), 'en']
        )
        countries = [
            (pycountry_locale.gettext(country.name), country.alpha_2)
            for country in pycountry.countries
        ]
        countries.sort()
        self.country.choices = [(code, name) for (name, code) in countries]


@VenueRoom.forms('main')
class VenueRoomForm(forms.Form):
    title = forms.StringField(
        __("Name"),
        description=__("Name of the room"),
        validators=[forms.validators.DataRequired(), forms.validators.Length(max=250)],
        filters=[forms.filters.strip()],
    )
    description = forms.MarkdownField(
        __("Description"), description=__("An optional note about the room")
    )
    bgcolor = forms.StringField(
        __("Room colour"),
        validators=[forms.validators.DataRequired(), forms.validators.Length(max=6)],
        description=__("RGB colour for the room. Enter without the '#'. E.g. CCCCCC"),
        default="CCCCCC",
    )

    def validate_bgcolor(self, field):
        if not valid_color_re.match(field.data):
            raise forms.ValidationError(_("Please enter a valid color code"))


@Venue.forms('primary')
class VenuePrimaryForm(forms.Form):
    venue = QuerySelectField(
        __("Venue"),
        validators=[forms.validators.DataRequired()],
        get_pk=lambda v: v.uuid_b58,
        get_label='title',
        allow_blank=False,
        widget_attrs={'autocorrect': 'none', 'autocapitalize': 'none'},
    )

    def set_queries(self):
        self.venue.query = self.edit_parent.venues
