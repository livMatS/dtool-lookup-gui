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

from gi.repository import Gtk

from dtoolcore.utils import get_config_value, write_config_value_to_file, generous_parse_uri
from dtool_lookup_api.core.config import Config
from dtool_lookup_api.core.LookupClient import authenticate


def _is_configured(base_uri):
    if base_uri.scheme == 's3':
        return get_config_value(f'DTOOL_S3_ENDPOINT_{base_uri.netloc}') is not None
    else:
        return False


class SignalHandler:
    def __init__(self, parent):
        self.main_application = parent.main_application
        self.event_loop = parent.event_loop
        self.builder = parent.builder
        self.settings = parent.settings

        self.settings_window = self.builder.get_object('settings-window')
        self.auth_dialog = self.builder.get_object('auth-dialog')
        self.s3_configuration_dialog = self.builder.get_object('s3-configuration-dialog')

    def show(self):
        self.settings_window.show()

    def on_settings_window_show(self, widget):
        if Config.lookup_url is not None:
            self.builder.get_object('lookup-url-entry').set_text(Config.lookup_url)
        if Config.token is not None:
            self.builder.get_object('token-entry').set_text(Config.token)
        if Config.auth_url is not None:
            self.builder.get_object('authenticator-url-entry').set_text(Config.auth_url)
        asyncio.create_task(self._refresh_list_of_endpoints())

    async def _refresh_list_of_endpoints(self):
        endpoints_list_box = self.builder.get_object('endpoints-list-box')
        for child in endpoints_list_box.get_children():
            child.destroy()
        base_uris = await self.main_application.lookup_tab.lookup.list_base_uris()

        for base_uri in base_uris:
            parsed_uri = generous_parse_uri(base_uri["base_uri"])
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            hbox.set_margin_top(12)
            hbox.set_margin_bottom(12)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(xalign=0)
            label.set_markup(f'<b>{base_uri["base_uri"]}</b>')
            vbox.pack_start(label, True, True, 0)
            label = Gtk.Label(xalign=0)
            if _is_configured(parsed_uri):
                label.set_markup('This endpoint was reported by the lookup server and it is configured locally.')
            else:
                label.set_markup('This endpoint was reported by the lookup server, but it is not configured locally')
            vbox.pack_start(label, True, True, 0)
            hbox.pack_start(vbox, True, True, 0)
            button = Gtk.Button(image=Gtk.Image.new_from_icon_name('emblem-system-symbolic', Gtk.IconSize.BUTTON))
            button.connect('clicked', self.on_configure_endpoint_clicked)
            # We currently can only configure S3 endpoints through the GUI
            button.set_sensitive(parsed_uri.scheme == 's3')
            button.base_uri = parsed_uri
            hbox.pack_end(button, False, False, 0)
            row.add(hbox)
            endpoints_list_box.add(row)

        row = Gtk.ListBoxRow()
        image = Gtk.Image.new_from_icon_name('list-add-symbolic', Gtk.IconSize.BUTTON)
        image.set_margin_top(20)
        image.set_margin_bottom(20)
        image.set_margin_start(12)
        image.set_margin_end(12)
        row.connect('state-changed', self.on_add_endpoint_clicked)
        row.add(image)
        endpoints_list_box.add(row)

        endpoints_list_box.show_all()

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
        await self._refresh_list_of_endpoints()

    def on_auth_ok_clicked(self, widget):
        self.auth_dialog.hide()
        asyncio.create_task(self.retrieve_token(
            self.builder.get_object('authenticator-url-entry').get_text(),
            self.builder.get_object('username-entry').get_text(),
            self.builder.get_object('password-entry').get_text()
        ))

        # Reconnect since settings may have been changed
        asyncio.create_task(self.main_application.lookup_tab.connect())

    def on_auth_cancel_clicked(self, widget):
        self.auth_dialog.hide()

    def on_configure_endpoint_clicked(self, widget):
        base_uri = widget.base_uri
        if base_uri.scheme == 's3':
            s3_endpoint = get_config_value(f'DTOOL_S3_ENDPOINT_{base_uri.netloc}')
            s3_access_key = get_config_value(f'DTOOL_S3_ACCESS_KEY_ID_{base_uri.netloc}')
            s3_secret_key = get_config_value(f'DTOOL_S3_SECRET_ACCESS_KEY_{base_uri.netloc}')
            s3_prefix = get_config_value(f'DTOOL_S3_DATASET_PREFIX')
            if s3_endpoint:
                self.builder.get_object('s3-endpoint-url-entry').set_text(s3_endpoint)
            if s3_access_key:
                self.builder.get_object('s3-access-key-entry').set_text(s3_access_key)
            if s3_secret_key:
                self.builder.get_object('s3-secret-key-entry').set_text(s3_secret_key)
            if s3_prefix:
                self.builder.get_object('s3-prefix-entry').set_text(s3_prefix)

            self.s3_configuration_dialog.base_uri = base_uri
            self.s3_configuration_dialog.show()

    def on_add_endpoint_state_changed(self, widget, state):
        print('add endpoint', widget, state)

    def on_s3_configuration_apply_clicked(self, widget):
        self.s3_configuration_dialog.hide()

        base_uri = self.s3_configuration_dialog.base_uri
        write_config_value_to_file(f'DTOOL_S3_ENDPOINT_{base_uri.netloc}',
                                   self.builder.get_object('s3-endpoint-url-entry').get_text())
        write_config_value_to_file(f'DTOOL_S3_ACCESS_KEY_ID_{base_uri.netloc}',
                                   self.builder.get_object('s3-access-key-entry').get_text())
        write_config_value_to_file(f'DTOOL_S3_SECRET_ACCESS_KEY_{base_uri.netloc}',
                                   self.builder.get_object('s3-secret-key-entry').get_text())
        write_config_value_to_file(f'DTOOL_S3_DATASET_PREFIX',
                                   self.builder.get_object('s3-prefix-entry').get_text())

    def on_s3_configuration_cancel_clicked(self, widget):
        self.s3_configuration_dialog.hide()
