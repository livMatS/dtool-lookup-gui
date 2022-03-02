#
# Copyright 2021-2022 Johannes Laurin Hörmann
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
import datetime
import logging
import os

import dtoolcore

from gi.repository import Gio, GLib, Gtk

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

_DTOOL_README_TEMPLATE_FPATH_KEY = "DTOOL_README_TEMPLATE_FPATH"
_DTOOL_USER_FULL_NAME_KEY = "DTOOL_USER_FULL_NAME"
_DTOOL_USER_EMAIL_KEY = "DTOOL_USER_EMAIL"


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

    dtool_user_full_name_entry = Gtk.Template.Child()
    dtool_user_email_entry = Gtk.Template.Child()
    dtool_readme_template_fpath_file_chooser_button = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        settings.settings.bind("dependency-keys", self.dependency_keys_entry, 'text', Gio.SettingsBindFlags.DEFAULT)

        # register own refresh method as listener for app-central dtool-config-changed signal
        self.get_application().connect("dtool-config-changed", self.on_dtool_config_changed)

        self._refresh_settings_dialog()

    def _refresh_settings_dialog(self):
        logger.debug("Refresh settings dialog.")

        # access lookup config via lookup api
        if Config.lookup_url is not None:
            logger.debug(f"Current lookup server url: {Config.lookup_url}")
            self.lookup_url_entry.set_text(Config.lookup_url)
        else:
            logger.debug("No lookup server url configured.")
            self.lookup_url_entry.set_text('')

        if Config.token is not None:
            logger.debug(f"Current lookup server token: {Config.token}")
            self.token_entry.set_text(Config.token)
        else:
            logger.debug("No lookup server token configured.")
            self.token_entry.set_text('')

        if Config.auth_url is not None:
            logger.debug(f"Current lookup server auth url: {Config.auth_url}")
            self.authenticator_url_entry.set_text(Config.auth_url)
        else:
            logger.debug("No lookup server auth url configured.")
            self.authenticator_url_entry.set_text('')

        if Config.verify_ssl is not None:
            logger.debug(f"Current lookup server verify ssl: {Config.verify_ssl}")
            # following line throws segmentation fault
            self.verify_ssl_certificate_switch.set_state(Config.verify_ssl)
        else:
            logger.debug("No lookup server verify ssl configured, set True.")
            self.verify_ssl_certificate_switch.set_state(True)

        # access basic config via default dtool config
        self.dtool_user_full_name_entry.set_text(
            dtoolcore.utils.get_config_value(_DTOOL_USER_FULL_NAME_KEY, default=""))

        self.dtool_user_email_entry.set_text(
            dtoolcore.utils.get_config_value(_DTOOL_USER_EMAIL_KEY, default=""))

        dtool_readme_template_fpath = dtoolcore.utils.get_config_value(_DTOOL_README_TEMPLATE_FPATH_KEY)
        if dtool_readme_template_fpath is not None:
            logger.debug(f"Current readme template: {dtool_readme_template_fpath}")
            self.dtool_readme_template_fpath_file_chooser_button.set_filename(dtool_readme_template_fpath)

        logger.debug("Refresh list of endpoints.")
        asyncio.create_task(self._refresh_list_of_endpoints())

    async def _refresh_list_of_endpoints(self):
        logger.debug("Refresh base uris list box.")
        await self.base_uris_list_box.refresh(on_configure=self.on_configure_base_uri_clicked, local=False,
                                              search_results=False)

        logger.debug("Add button for new end points.")
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

        logger.debug("base uris list box show all.")
        self.base_uris_list_box.show_all()
        logger.debug("Done refreshing settings dialog.")

    def on_dtool_config_changed(self, widget):
        """Signal handler for dtool-method-changed."""
        self._refresh_settings_dialog()

    # signal handlers
    @Gtk.Template.Callback()
    def on_delete(self, widget, event):
        # Write back lookup configuration via lookup api
        Config.lookup_url = self.lookup_url_entry.get_text()
        Config.token = self.token_entry.get_text()
        Config.auth_url = self.authenticator_url_entry.get_text()
        Config.verify_ssl = self.verify_ssl_certificate_switch.get_state()

        # write back basic config via default dtool api
        dtool_user_full_name = self.dtool_user_full_name_entry.get_text()
        if dtool_user_full_name != dtoolcore.utils.get_config_value(_DTOOL_USER_FULL_NAME_KEY, default=""):
            logger.debug(f"{_DTOOL_USER_FULL_NAME_KEY} changed to {dtool_user_full_name}, write to config.")
            dtoolcore.utils.write_config_value_to_file(_DTOOL_USER_FULL_NAME_KEY, dtool_user_full_name)

        dtool_user_email = self.dtool_user_email_entry.get_text()
        if dtool_user_email != dtoolcore.utils.get_config_value(_DTOOL_USER_EMAIL_KEY, default=""):
            logger.debug(f"{_DTOOL_USER_EMAIL_KEY} changed to {dtool_user_email}, write to config.")
            dtoolcore.utils.write_config_value_to_file(_DTOOL_USER_EMAIL_KEY, dtool_user_email)

        dtool_readme_template_fpath = self.dtool_readme_template_fpath_file_chooser_button.get_filename()
        if (dtool_readme_template_fpath is not None
                and dtool_readme_template_fpath != dtoolcore.utils.get_config_value(_DTOOL_README_TEMPLATE_FPATH_KEY)):
            logger.debug(f"{_DTOOL_README_TEMPLATE_FPATH_KEY} changed to {dtool_readme_template_fpath}, write to config.")
            dtoolcore.utils.write_config_value_to_file(_DTOOL_README_TEMPLATE_FPATH_KEY, dtool_readme_template_fpath)

        return self.hide_on_delete()

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

    @Gtk.Template.Callback()
    def on_reset_config_clicked(self, widget):
        """Process clicked signal from reset-config button."""
        self.get_action_group("app").activate_action('reset-config')

    @Gtk.Template.Callback()
    def on_import_config_clicked(self, widget):
        """Process clicked signal from import-config button."""
        dialog = Gtk.FileChooserDialog(title=f"Import dtool config from file", parent=self,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(Gtk.STOCK_CANCEL,
                           Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OPEN,
                           Gtk.ResponseType.OK)
        dialog.set_select_multiple(False)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            dest_filename = dialog.get_filename()
            self.get_action_group("app").activate_action('import-config', GLib.Variant.new_string(dest_filename))

        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    @Gtk.Template.Callback()
    def on_export_config_clicked(self, widget):
        """Process clicked signal from import-config button."""
        dialog = Gtk.FileChooserDialog(title=f"Export dtool config to file", parent=self,
                                       action=Gtk.FileChooserAction.SAVE)
        dialog.add_buttons(Gtk.STOCK_CANCEL,
                           Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK,
                           Gtk.ResponseType.OK)
        suggested_file_name = f"{datetime.datetime.now().isoformat()}-{self.get_application().get_application_id()}-dtool.json"
        dialog.set_current_name(suggested_file_name)
        dialog.set_do_overwrite_confirmation(True)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            dest_filename = dialog.get_filename()
            self.get_action_group("app").activate_action('export-config', GLib.Variant.new_string(dest_filename))

        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

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