from __future__ import annotations

from flask import current_app, redirect, request, session

from oauth2client import client
from sentry_sdk import capture_exception
import requests
import simplejson

from baseframe import _

from ..registry import LoginCallbackError, LoginProvider
from ..typing import ReturnLoginProvider

__all__ = ['GoogleProvider']


class GoogleProvider(LoginProvider):
    form = None  # Don't need a form for Google
    info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def __init__(self, name, title, client_id, **kwargs) -> None:
        self.client_id = client_id
        self.secret = kwargs['secret']
        super().__init__(name, title, **kwargs)

    def flow(self, callback_url):
        return client.OAuth2WebServerFlow(
            client_id=self.client_id,
            client_secret=self.secret,
            scope=['profile', 'email'],
            redirect_uri=callback_url,
        )

    def do(self, callback_url):
        session['google_callback'] = callback_url
        return redirect(self.flow(callback_url).step1_get_authorize_url())

    def callback(self) -> ReturnLoginProvider:
        if 'google_callback' in session:
            callback_url = session.pop('google_callback')
        else:
            raise LoginCallbackError(
                _("Duplicate callback. Did you go back in your browser history?")
            )
        if request.args.get('error'):
            if request.args['error'] == 'access_denied':
                raise LoginCallbackError(_("You denied the Google login request"))
            else:
                raise LoginCallbackError(_("Unknown failure"))
        code = request.args.get('code', None)
        try:
            credentials = self.flow(callback_url).step2_exchange(code)
            response = requests.get(
                self.info_url,
                timeout=30,
                headers={
                    'Authorization': (
                        credentials.token_response['token_type']  # 'Bearer', etc
                        + ' '
                        + credentials.access_token
                    )
                },
            ).json()
        except (
            client.FlowExchangeError,
            requests.exceptions.RequestException,
            simplejson.JSONDecodeError,
        ) as exc:
            current_app.logger.error("Google OAuth2 error: %s", repr(exc))
            capture_exception(exc)
            raise LoginCallbackError(
                _("Google had an intermittent problem. Try again?")
            )
        if response.get('error'):
            raise LoginCallbackError(
                _("Unable to login via Google: {error}").format(
                    error=response['error'].get('message', '')
                )
            )
        return {
            'email': credentials.id_token['email'],
            'userid': credentials.id_token['email'],
            'username': credentials.id_token['email'],
            'fullname': (response.get('name') or '').strip(),
            'avatar_url': response.get('picture'),
            'oauth_token': credentials.access_token,
            'oauth_token_secret': None,  # OAuth 2 doesn't need token secrets
            'oauth_token_type': credentials.token_response['token_type'],
        }
