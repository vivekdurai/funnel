from __future__ import annotations

from typing import Dict, Iterable, Optional, Set

from sqlalchemy.ext.declarative import declared_attr

from werkzeug.utils import cached_property

from coaster.sqlalchemy import DynamicAssociationProxy, immutable, with_roles

from . import db
from .helpers import reopen
from .membership_mixin import ImmutableUserMembershipMixin
from .project import Project
from .user import User

__all__ = ['ProjectCrewMembership', 'project_child_role_map']

# Roles in a project and their remapped names in objects attached to a project
project_child_role_map: Dict[str, str] = {
    'editor': 'project_editor',
    'promoter': 'project_promoter',
    'usher': 'project_usher',
    'crew': 'project_crew',
    'participant': 'project_participant',
    'reader': 'reader',
}


class ProjectCrewMembership(ImmutableUserMembershipMixin, db.Model):
    """Users can be crew members of projects, with specified access rights."""

    __tablename__ = 'project_crew_membership'

    #: Legacy data has no granted_by
    __null_granted_by__ = True

    #: List of is_role columns in this model
    __data_columns__ = ('is_editor', 'is_promoter', 'is_usher')

    __roles__ = {
        'all': {
            'read': {'urls', 'user', 'is_editor', 'is_promoter', 'is_usher', 'project'}
        }
    }
    __datasets__ = {
        'primary': {
            'urls',
            'uuid_b58',
            'offered_roles',
            'is_editor',
            'is_promoter',
            'is_usher',
            'user',
            'project',
        },
        'without_parent': {
            'urls',
            'uuid_b58',
            'offered_roles',
            'is_editor',
            'is_promoter',
            'is_usher',
            'user',
        },
        'related': {
            'urls',
            'uuid_b58',
            'offered_roles',
            'is_editor',
            'is_promoter',
            'is_usher',
        },
    }

    project_id = immutable(
        db.Column(None, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    )
    project = immutable(
        db.relationship(
            Project,
            backref=db.backref(
                'crew_memberships', lazy='dynamic', cascade='all', passive_deletes=True
            ),
        )
    )
    parent = db.synonym('project')
    parent_id = db.synonym('project_id')

    # Project crew roles (at least one must be True):

    #: Editors can edit all common and editorial details of an event
    is_editor = db.Column(db.Boolean, nullable=False, default=False)
    #: Promoters are responsible for promotion and have write access
    #: to common details plus read access to everything else. Unlike
    #: editors, they cannot edit the schedule
    is_promoter = db.Column(db.Boolean, nullable=False, default=False)
    #: Ushers help participants find their way around an event and have
    #: the ability to scan badges at the door
    is_usher = db.Column(db.Boolean, nullable=False, default=False)

    @declared_attr
    def __table_args__(cls):
        """Table arguments."""
        args = list(super().__table_args__)
        kwargs = args.pop(-1) if args and isinstance(args[-1], dict) else None
        args.append(
            db.CheckConstraint(
                db.or_(
                    cls.is_editor.is_(True),
                    cls.is_promoter.is_(True),
                    cls.is_usher.is_(True),
                ),
                name='project_crew_membership_has_role',
            )
        )
        if kwargs:
            args.append(kwargs)
        return tuple(args)

    @cached_property
    def offered_roles(self) -> Set[str]:
        """Roles offered by this membership record."""
        roles = {'crew', 'participant'}
        if self.is_editor:
            roles.add('editor')
        if self.is_promoter:
            roles.add('promoter')
        if self.is_usher:
            roles.add('usher')
        return roles

    def roles_for(self, actor: Optional[User], anchors: Iterable = ()) -> Set:
        roles = super().roles_for(actor, anchors)
        if 'editor' in self.project.roles_for(actor, anchors):
            roles.add('project_editor')
        if 'admin' in self.project.profile.roles_for(actor, anchors):
            roles.add('profile_admin')
        return roles


# Project relationships: all crew, vs specific roles
@reopen(Project)
class __Project:
    active_crew_memberships = with_roles(
        db.relationship(
            ProjectCrewMembership,
            lazy='dynamic',
            primaryjoin=db.and_(
                ProjectCrewMembership.project_id == Project.id,
                ProjectCrewMembership.is_active,
            ),
            viewonly=True,
        ),
        grants_via={'user': {'editor', 'promoter', 'usher', 'participant', 'crew'}},
    )

    active_editor_memberships = db.relationship(
        ProjectCrewMembership,
        lazy='dynamic',
        primaryjoin=db.and_(
            ProjectCrewMembership.project_id == Project.id,
            ProjectCrewMembership.is_active,
            ProjectCrewMembership.is_editor.is_(True),
        ),
        viewonly=True,
    )

    active_promoter_memberships = db.relationship(
        ProjectCrewMembership,
        lazy='dynamic',
        primaryjoin=db.and_(
            ProjectCrewMembership.project_id == Project.id,
            ProjectCrewMembership.is_active,
            ProjectCrewMembership.is_promoter.is_(True),
        ),
        viewonly=True,
    )

    active_usher_memberships = db.relationship(
        ProjectCrewMembership,
        lazy='dynamic',
        primaryjoin=db.and_(
            ProjectCrewMembership.project_id == Project.id,
            ProjectCrewMembership.is_active,
            ProjectCrewMembership.is_usher.is_(True),
        ),
        viewonly=True,
    )

    crew = DynamicAssociationProxy('active_crew_memberships', 'user')
    editors = DynamicAssociationProxy('active_editor_memberships', 'user')
    promoters = DynamicAssociationProxy('active_promoter_memberships', 'user')
    ushers = DynamicAssociationProxy('active_usher_memberships', 'user')


# Similarly for users (add as needs come up)
@reopen(User)
class __User:
    # This relationship is only useful to check if the user has ever been a crew member.
    # Most operations will want to use one of the active membership relationships.
    projects_as_crew_memberships = db.relationship(
        ProjectCrewMembership,
        lazy='dynamic',
        foreign_keys=[ProjectCrewMembership.user_id],
        viewonly=True,
    )
    projects_as_crew_active_memberships = db.relationship(
        ProjectCrewMembership,
        lazy='dynamic',
        primaryjoin=db.and_(
            ProjectCrewMembership.user_id == User.id, ProjectCrewMembership.is_active
        ),
        viewonly=True,
    )

    projects_as_crew = DynamicAssociationProxy(
        'projects_as_crew_active_memberships', 'project'
    )

    projects_as_editor_active_memberships = db.relationship(
        ProjectCrewMembership,
        lazy='dynamic',
        primaryjoin=db.and_(
            ProjectCrewMembership.user_id == User.id,
            ProjectCrewMembership.is_active,
            ProjectCrewMembership.is_editor.is_(True),
        ),
        viewonly=True,
    )

    projects_as_editor = DynamicAssociationProxy(
        'projects_as_editor_active_memberships', 'project'
    )
