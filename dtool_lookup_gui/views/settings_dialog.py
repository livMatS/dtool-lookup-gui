#
# Copyright 2021 Johannes Hörmann
#           2021 Lars Pastewka
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
import logging
import os

import jwt

from gi.repository import Gio, Gtk

from dtool_lookup_api.core.config import Config
from dtool_lookup_api.core.LookupClient import authenticate

from ..models.settings import settings
from .authentication_dialog import AuthenticationDialog
from .s3_configuration_dialog import S3ConfigurationDialog
from .smb_configuration_dialog import SMBConfigurationDialog


_DTOOL_CONFIG_PREFIXES = {
    'DTOOL_S3_ENDPOINT_': 's3',
    'DTOOL_SMB_SERVER_NAME_': 'smb',
}


logger = logging.getLogger(__name__)


def _get_base_uri(key):
    for prefix, schema in _DTOOL_CONFIG_PREFIXES.items():
        if key.startswith(prefix):
            return f'{schema}://{key[len(prefix):]}'
    return None


@Gtk.Template(filename=f'{os.path.dirname(__file__)}/settings_dialog.ui')
class SettingsDialog(Gtk.Window):
    __gtype_name__ = 'DtoolSettingsDialog'

    lookup_url_entry = Gtk.Template.Child()
    token_entry = Gtk.Template.Child()
    authenticator_url_entry = Gtk.Template.Child()
    dependency_keys_entry = Gtk.Template.Child()
    verify_ssl_certificate_switch = Gtk.Template.Child()
    base_uris_list_box = Gtk.Template.Child()

    def __init__(self, parent, **kwargs):
        super().__init__(**kwargs)

        settings.settings.bind("dependency-keys", self.dependency_keys_entry, 'text', Gio.SettingsBindFlags.DEFAULT)

        if Config.lookup_url is not None:
            self.lookup_url_entry.set_text(Config.lookup_url)
        if Config.token is not None:
            self.token_entry.set_text(Config.token)
        if Config.auth_url is not None:
            self.authenticator_url_entry.set_text(Config.auth_url)
        if Config.verify_ssl is not None:
            self.verify_ssl_certificate_switch.set_state(Config.verify_ssl)
        asyncio.create_task(self._refresh_list_of_endpoints())

    async def _refresh_list_of_endpoints(self):
        await self.base_uris_list_box.refresh(on_configure=self.on_configure_base_uri_clicked, local=False,
                                              search_results=False)

        # Plus button for adding new endpoints
        row = Gtk.ListBoxRow()
        image = Gtk.Image.new_from_icon_name('list-add-symbolic', Gtk.IconSize.BUTTON)
        image.set_margin_top(20)
        image.set_margin_bottom(20)
        image.set_margin_start(12)
        image.set_margin_end(12)
        row.connect('state-changed', self.on_base_uri_state_changed)
        row.add(image)
        self.base_uris_list_box.add(row)

        self.base_uris_list_box.show_all()

    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        # Write back configuration
        Config.lookup_url = self.lookup_url_entry.get_text()
        Config.token = self.token_entry.get_text()
        Config.auth_url = self.authenticator_url_entry.get_text()
        Config.verify_ssl = self.verify_ssl_certificate_switch.get_state()

        # Reconnect since settings may have been changed
        #asyncio.create_task(self.main_application.lookup_tab.connect())

        # Destroy window
        return False

    @Gtk.Template.Callback()
    def on_renew_token_clicked(self, widget):
        def authenticate(username, password):
            asyncio.create_task(self.retrieve_token(
                self.authenticator_url_entry.get_text(),
                username,
                password))

            # Reconnect since settings may have been changed
            #asyncio.create_task(self.main_application.lookup_tab.connect())

        AuthenticationDialog(authenticate, Config.username, Config.password).show()

    async def retrieve_token(self, auth_url, username, password):
        #self.main_application.error_bar.hide()
        try:
            token = await authenticate(auth_url, username, password)
        except Exception as e:
            logger.error(str(e))
            return
        #self.builder.get_object('token-entry').set_text(token)
        self.token_entry.set_text(token)
        await self._refresh_list_of_endpoints()

    _configuration_dialogs = {
        's3': S3ConfigurationDialog,
        'smb': SMBConfigurationDialog,
    }

    def on_configure_base_uri_clicked(self, widget):
        base_uri = widget.get_parent().get_parent().base_uri
        self._configuration_dialogs[base_uri.scheme](
            lambda: asyncio.create_task(self._refresh_list_of_endpoints()), base_uri.uri_name).show()

    def on_base_uri_state_changed(self, widget, state):
        if state == Gtk.StateType.ACTIVE:
            S3ConfigurationDialog(lambda: asyncio.create_task(self._refresh_list_of_endpoints())).show()
