# -*- coding: utf-8 -*-

from flask.ext.lastuser.sqlalchemy import ProfileMixin
from nodular import Node, NodeMixin
from . import registry

__all__ = ['Profile']


# ProfileMixin is the last base class here to prevent its buid definition
# from conflicting with Node's.
class Profile(NodeMixin, Node, ProfileMixin):
    __tablename__ = 'profile'

    def permissions(self, user, inherited=None):
        perms = super(Profile, self).permissions(user, inherited)
        perms.add('view')  # Grant everyone view access
        return perms


registry.register_node(Profile)
