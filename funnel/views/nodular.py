# -*- coding: utf-8 -*-

from __future__ import absolute_import

from nodular import NodePublisher
from .. import app
from ..models import registry

homepublisher = NodePublisher(None, registry, '/home', '/')
profilepublisher = NodePublisher(None, registry, '/profiles', '/')

def init_root(root):
    homepublisher.init_root(root)
    profilepublisher.init_root(root)


@app.route('/')
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def index(path=u''):
    return homepublisher.publish(path)


@app.route('/', subdomain="<profile>", defaults={'path': u''})
@app.route('/<path:path>', subdomain="<profile>",
    methods=['GET', 'POST', 'PUT', 'DELETE'])
def profileurls(profile, path):
    return profilepublisher.publish(path)
