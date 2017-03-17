# -*- coding: utf-8 -*-

from flask.ext.lastuser.sqlalchemy import UserBase2, TeamBase
from . import db

__all__ = ['User', 'Team']


# --- Models ------------------------------------------------------------------

class User(UserBase2, db.Model):
    __tablename__ = 'user'

    @classmethod
    def get_by_mentions(cls, content):
        mentions = [word for word in content.split(" ") if word.startswith('@')]
        return cls.query.filter(cls.username.in_(mentions))


class Team(TeamBase, db.Model):
    __tablename__ = 'team'
