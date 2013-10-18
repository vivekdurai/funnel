#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import coaster.app
from flask import Flask
from flask.ext.mail import Mail
from flask.ext.lastuser import Lastuser
from flask.ext.lastuser.sqlalchemy import UserManager
from nodular import Node
from baseframe import baseframe, assets, Version
from ._version import __version__


app = Flask(__name__, instance_relative_config=True)
mail = Mail()
lastuser = Lastuser()


# --- Assets ------------------------------------------------------------------

version = Version(__version__)
assets['jquery.oembed.js'][version] = 'js/libs/jquery.oembed.js'
assets['showdown.js'][version] = 'js/libs/showdown.js'
assets['funnel.js'][version] = 'js/scripts.js'
assets['funnel.css'][version] = 'css/app.css'

# --- Root node ---------------------------------------------------------------

root = None

# --- Import rest of the app --------------------------------------------------

from . import models, forms, views
from .models import db, registry


# --- Configuration------------------------------------------------------------

def init_for(env):
    coaster.app.init_app(app, env)
    db.init_app(app)
    db.app = app
    mail.init_app(app)
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(db, models.User))
    baseframe.init_app(app, requires=[
        'jquery.form', 'jquery.oembed', 'showdown', 'codemirror-markdown', 'pygments', 'baseframe-bs3', 'funnel',
        ])


def load_root():
    global root
    root = Node.query.filter_by(name=u'funnel', parent=None).first()
    if root is None:
        root = Node(name=u'funnel', title=u'Funnel Root', parent=None)
        db.session.add(root)
    if u'home' not in root.nodes:
        root.nodes[u'home'] = Node(title=u'Home')
    if u'profiles' not in root.nodes:
        root.nodes[u'profiles'] = Node(title=u'Profiles')
    db.session.commit()
    views.nodular.init_root(root)
