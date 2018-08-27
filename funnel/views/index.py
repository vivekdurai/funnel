# -*- coding: utf-8 -*-

from flask import g, render_template, redirect, jsonify
from datetime import datetime
from coaster.views import jsonp, load_model, render_with
from .. import app
from ..models import Profile, ProposalSpace, Proposal
from .space import space_data


def jsonify_spaces(data):
    spaces_dict = []
    for space in data['spaces']:
        spaces_dict.append(dict(space.current_access()))
    return jsonify(spaces=spaces_dict)


@app.route('/')
@render_with({'text/html': 'index.html.jinja2', 'application/json': jsonify_spaces})
def index():
    g.profile = None
    g.permissions = []
    spaces = ProposalSpace.fetch_sorted().filter(ProposalSpace.profile != None).all()
    return dict(spaces=spaces)


@app.route('/api/whoami')
def whoami():
    if g.user:
        return jsonify(message="Hey {0}!".format(g.user.fullname), code=200)
    else:
        return jsonify(message="Hmm, so who _are_ you?", code=401)


@app.route('/json')
def all_spaces_json():
    g.profile = None
    g.permissions = []
    spaces = ProposalSpace.fetch_sorted().filter(ProposalSpace.profile != None).all()
    return jsonp(spaces=map(space_data, spaces))


@app.route('/json', subdomain='<profile>')
@load_model(Profile, {'name': 'profile'}, 'g.profile', permission='view')
def spaces_json(profile):
    spaces = ProposalSpace.fetch_sorted().filter_by(profile=profile).all()
    return jsonp(spaces=map(space_data, spaces))


@app.route('/', subdomain='<profile>')
@load_model(Profile, {'name': 'profile'}, 'g.profile', permission='view')
@render_with({'text/html': 'index.html.jinja2', 'application/json': jsonify_spaces})
def profile_view(profile):
    spaces = ProposalSpace.fetch_sorted().filter(
        ProposalSpace.profile == profile, ProposalSpace.parent_space == None
    ).all()
    return dict(spaces=spaces)


# Legacy routes for funnel to talkfunnel migration
# Figure out how to restrict these routes to just the funnel.hasgeek.com domain

@app.route('/<space>/')
@load_model(ProposalSpace, {'legacy_name': 'space'}, 'space')
def space_redirect(space):
    return redirect(space.url_for())


@app.route('/<space>/json')
@load_model(ProposalSpace, {'legacy_name': 'space'}, 'space')
def space_redirect_json(space):
    return redirect(space.url_for('json'))


@app.route('/<space>/csv')
@load_model(ProposalSpace, {'legacy_name': 'space'}, 'space')
def space_redirect_csv(space):
    return redirect(space.url_for('csv'))


@app.route('/<space>/<int:id>-<name>')
@app.route('/<space>/<int:id>')
@load_model(Proposal, {'id': 'id'}, 'proposal')
def proposal_redirect(proposal):
    return redirect(proposal.url_for())
