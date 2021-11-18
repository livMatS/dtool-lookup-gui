#
# Copyright 2021 Lars Pastewka
#
# ### MIT license
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import asyncio

from dtool_lookup_api.core.config import Config
from dtool_lookup_api.core.LookupClient import authenticate

class SignalHandler:
    def __init__(self, main_application, event_loop, builder, settings):
        self.main_application = main_application
        self.event_loop = event_loop
        self.builder = builder
        self.settings = settings

        self.settings_window = self.builder.get_object('settings-window')
        self.auth_dialog = self.builder.get_object('auth-dialog')

    def show(self):
        self.settings_window.show()

    def _load_handlers(self, object):
        """Scan object for signal handlers and add them to a (class-global) """
        if isinstance(object, dict):
            methods = object.items()
        else:
            methods = map(lambda n: (n, getattr(object, n, None)), dir(object))

        for method_name, method in methods:
            if method_name.startswith('_'):
                continue
            if callable(method):
                logger.debug("Registering callback %s" % (method_name))
                if method_name in self.handlers:
                    self.handlers[method_name].append(method)
                else:
                    self.handlers[method_name] = Trampoline([method])

    def on_settings_window_show(self, widget):
        if Config.lookup_url is not None:
            self.builder.get_object('lookup-url-entry').set_text(Config.lookup_url)
        if Config.token is not None:
            self.builder.get_object('token-entry').set_text(Config.token)
        if Config.auth_url is not None:
            self.builder.get_object('authenticator-url-entry').set_text(Config.auth_url)

    def on_settings_window_delete(self, widget, event):
        # Don't delete, simply hide the window
        widget.hide()

        # Write back configuration
        Config.lookup_url = self.builder.get_object('lookup-url-entry').get_text()
        Config.token = self.builder.get_object('token-entry').get_text()
        Config.auth_url = self.builder.get_object('authenticator-url-entry').get_text()

        # Reconnect since settings may have been changed
        asyncio.create_task(self.main_application.lookup_tab.connect())

        # Return True to avoid destruction of the window
        return True

    def on_renew_token_clicked(self, widget):
        if Config.username is not None:
            self.builder.get_object('username-entry').set_text(Config.username)
        if Config.password is not None:
            self.builder.get_object('password-entry').set_text(Config.password)
        self.auth_dialog.show()

    async def retrieve_token(self, auth_url, username, password):
        self.main_application.error_bar.hide()
        try:
            token = await authenticate(auth_url, username, password)
        except Exception as e:
            self.main_application.show_error(str(e))
            return
        self.builder.get_object('token-entry').set_text(token)

    def on_auth_ok_clicked(self, widget):
        self.auth_dialog.hide()
        asyncio.create_task(self.retrieve_token(
            self.builder.get_object('authenticator-url-entry').get_text(),
            self.builder.get_object('username-entry').get_text(),
            self.builder.get_object('password-entry').get_text()
        ))

    def on_auth_cancel_clicked(self, widget):
        self.auth_dialog.hide()
