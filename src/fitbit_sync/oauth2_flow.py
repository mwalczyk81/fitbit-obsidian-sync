import inspect
import os
import threading
import webbrowser

import cherrypy
from fitbit import Fitbit


class OAuth2Server:
    def __init__(self, client_id, client_secret, redirect_uri="http://localhost:8080"):
        self.redirect_uri = redirect_uri
        self.success_html = (
            "<h1>Authorization successful. You can close this window.</h1>"
        )
        self.client_id = client_id
        self.client_secret = client_secret

    def browser_authorize(self):
        self.redirect_url = None
        self.server = self._start_local_server()
        self.oauth_client = Fitbit(
            self.client_id, self.client_secret, redirect_uri=self.redirect_uri
        )
        url, _ = self.oauth_client.client.authorize_token_url()
        webbrowser.open(url)
        self._wait_for_redirect()
        self._shutdown_server()
        token = self.oauth_client.client.fetch_access_token(self.redirect_url)
        self.fitbit = Fitbit(
            self.client_id,
            self.client_secret,
            access_token=token["access_token"],
            refresh_token=token["refresh_token"],
            expires_at=token["expires_at"],
            refresh_cb=None,
        )

    def _start_local_server(self):
        cherrypy.config.update({"server.socket_port": 8080})
        cherrypy.quickstart(self)

    def _shutdown_server(self):
        cherrypy.engine.exit()

    def _wait_for_redirect(self):
        while not hasattr(self, "redirect_url"):
            pass

    @cherrypy.expose
    def index(self, **params):
        self.redirect_url = cherrypy.url() + "?" + cherrypy.request.query_string
        return self.success_html
