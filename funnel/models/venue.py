# -*- coding: utf-8 -*-

from nodular import Node, RevisionedNodeMixin
from . import db, registry

__all__ = ['Venue', 'VenueRoom']


class Venue(RevisionedNodeMixin, Node):
    __tablename__ = 'venue'


registry.register_node(Venue)


class VenueRevision(Venue.RevisionMixin, db.Model):
    # Insert content columns here
    pass


class VenueRoom(RevisionedNodeMixin, Node):
    __tablename__ = 'venue_room'


registry.register_node(VenueRoom, parent_nodetypes=[Venue])


class VenueRoomRevision(VenueRoom.RevisionMixin, db.Model):
    # Insert content columns here
    pass
