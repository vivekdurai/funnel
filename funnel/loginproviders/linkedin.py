from __future__ import annotations

from urllib.parse import quote
from uuid import uuid4

from flask import current_app, redirect, request, session

from sentry_sdk import capture_exception
import requests
import simplejson

from baseframe import _

from ..registry import LoginCallbackError, LoginProvider
from ..typing import ReturnLoginProvider

__all__ = ['LinkedInProvider']


class LinkedInProvider(LoginProvider):
    auth_url = 'https://www.linkedin.com/uas/oauth2/authorization?response_type=code&client_id={client_id}&scope={scope}&redirect_uri={redirect_uri}&state={state}'
    token_url = 'https://www.linkedin.com/uas/oauth2/accessToken'  # nosec  # noqa: S105
    user_info = 'https://api.linkedin.com/v2/me?projection=(id,localizedFirstName,localizedLastName)'
    user_email = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'

    def __init__(
        self, name, title, key, secret, at_login=True, priority=False, icon=None
    ) -> None:
        self.name = name
        self.title = title
        self.at_login = at_login
        self.priority = priority
        self.icon = icon

        self.key = key
        self.secret = secret

    def do(self, callback_url):
        session['linkedin_state'] = str(uuid4())
        session['linkedin_callback'] = callback_url
        return redirect(
            self.auth_url.format(
                client_id=self.key,
                redirect_uri=quote(callback_url),
                scope='r_liteprofile r_emailaddress',
                state=session['linkedin_state'],
            )
        )

    def callback(self) -> ReturnLoginProvider:
        state = session.pop('linkedin_state', None)
        callback_url = session.pop('linkedin_callback', None)
        if state is None or request.args.get('state') != state:
            raise LoginCallbackError(
                _("We detected a possible attempt at cross-site request forgery")
            )
        if 'error' in request.args:
            if request.args['error'] == 'access_denied':
                raise LoginCallbackError(_("You denied the LinkedIn login request"))
            elif request.args['error'] == 'redirect_uri_mismatch':
                # TODO: Log this as an exception for the server admin to look at
                raise LoginCallbackError(
                    _("This server's callback URL is misconfigured")
                )
            else:
                raise LoginCallbackError(_("Unknown failure"))
        code = request.args.get('code', None)
        try:
            response = requests.post(
                self.token_url,
                headers={'Accept': 'application/json'},
                params={
                    'grant_type': 'authorization_code',
                    'client_id': self.key,
                    'client_secret': self.secret,
                    'code': code,
                    'redirect_uri': callback_url,
                },
            ).json()
        except (
            requests.exceptions.RequestException,
            simplejson.JSONDecodeError,
        ) as exc:
            current_app.logger.error("LinkedIn OAuth2 error: %s", repr(exc))
            capture_exception(exc)
            raise LoginCallbackError(
                _("LinkedIn had an intermittent problem. Try again?")
            )
        if 'error' in response:
            raise LoginCallbackError(response['error'])
        try:
            info = requests.get(
                self.user_info,
                timeout=30,
                params={'oauth2_access_token': response['access_token']},
                headers={'x-li-format': 'json'},
            ).json()
        except (
            requests.exceptions.RequestException,
            simplejson.JSONDecodeError,
        ) as exc:
            current_app.logger.error("LinkedIn OAuth2 error: %s", repr(exc))
            capture_exception(exc)
            raise LoginCallbackError(
                _("LinkedIn had an intermittent problem. Try again?")
            )

        if not info.get('id'):
            raise LoginCallbackError(
                _("Unable to retrieve user details from LinkedIn. Please try again")
            )

        try:
            email_info = requests.get(
                self.user_email,
                timeout=30,
                params={'oauth2_access_token': response['access_token']},
                headers={'x-li-format': 'json'},
            ).json()
        except (
            requests.exceptions.RequestException,
            simplejson.JSONDecodeError,
        ) as exc:
            current_app.logger.error("LinkedIn email_info error: %s", repr(exc))
            capture_exception(exc)
            raise LoginCallbackError(
                _("LinkedIn had an intermittent problem. Try again?")
            )

        email_address = ''
        if 'elements' in email_info and email_info['elements']:
            email_address = email_info['elements'][0]['handle~']['emailAddress']

        return {
            'email': email_address,
            'userid': info.get('id'),
            'username': None,
            'fullname': (
                (info.get('localizedFirstName') or '')
                + ' '
                + (info.get('localizedLastName') or '')
            ).strip(),
            'avatar_url': '',
            'oauth_token': response['access_token'],
            'oauth_token_secret': None,  # OAuth 2 doesn't need token secrets
            'oauth_token_type': None,
        }
