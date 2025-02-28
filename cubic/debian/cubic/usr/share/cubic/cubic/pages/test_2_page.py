#!/usr/bin/python3

########################################################################
#                                                                      #
# test_2_page.py                                                       #
#                                                                      #
# Copyright (C) 2021 PJ Singh <psingh.cubic@gmail.com>                 #
#                                                                      #
########################################################################

########################################################################
#                                                                      #
# This file is part of Cubic - Custom Ubuntu ISO Creator.              #
#                                                                      #
# Cubic is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or    #
# (at your option) any later version.                                  #
#                                                                      #
# Cubic is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the         #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with Cubic. If not, see <http://www.gnu.org/licenses/>.        #
#                                                                      #
########################################################################

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

import locale
import os

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import MIB, GIB
from cubic.navigator import handle_navigation
from cubic.utilities import displayer
from cubic.utilities import emulator
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'test_2_page'

########################################################################
# Navigation Functions
########################################################################


def setup(action, old_page=None):
    """
    Prepare this page for display. This function is executed while the
    previous page is still shown.

    Args:
    action : str
        The action from the previous page.
    old_page : str
        The previous page; optional.

    Returns:
    : None
        To continue to this page.
    error : str
        To automatically transition to an error page.
    """

    if action == 'test':

        displayer.update_label('test_2_page__banner_label', '', False)

        displayer.empty_box('test_2_page__alerts_box')

        displayer.update_entry('test_2_page__custom_iso_version_number_entry', model.generated.iso_version_number)
        displayer.update_entry('test_2_page__custom_iso_file_name_entry', model.generated.iso_file_name)
        displayer.update_entry('test_2_page__custom_iso_directory_entry', model.generated.iso_directory)
        displayer.update_entry('test_2_page__custom_iso_volume_id_entry', model.generated.iso_volume_id)
        displayer.update_entry('test_2_page__custom_iso_release_name_entry', model.generated.iso_release_name)
        displayer.update_entry('test_2_page__custom_iso_disk_name_entry', model.generated.iso_disk_name)
        # displayer.update_entry('test_2_page__custom_iso_checksum_entry', model.generated.iso_checksum)
        # displayer.update_entry('test_2_page__custom_iso_checksum_file_name_entry', model.generated.iso_checksum_file_name)
        '''
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='cancel',
            back_button_style='suggested-action',
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style=None,
            is_next_sensitive=False,
            is_next_visible=False)
        '''

        emulator.start_emulator(update_status)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for setup{NORMAL}')

        return 'unknown'


def enter(action, old_page=None):
    """
    Preform functions on this page after it is shown. This function is
    executed after the previous page is hidden.

    Args:
    action : str
        The action from the previous page.
    old_page : str
        The previous page; optional.

    Returns:
    : None
        To stay on this page.
    action : str
        To automatically transition to another page.
    error : str
        To automatically transition to an error page.
    """

    if action == 'test':

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for enter{NORMAL}')

        return 'unknown'


def leave(action, new_page=None):
    """
    Preform functions on this page before leaving it. This function is
    executed while this page is visible.

    Args:
    action : str
        The action on this page.
    old_page : str
        The next page to show; optional.

    Returns:
    : None
        To continue to the next page.
    error : str
        To automatically transition to an error page.
    """

    if action == 'cancel':

        # Remove the status call back to prevent the navigation on
        # 'cancel' action from being invoked twice (by this function and
        # by the status call back function.
        emulator.remove_status_callback()

        displayer.update_label('test_2_page__banner_label', '', False)

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'quit':

        # Remove the status call back to prevent the navigation on
        # 'cancel' action from being invoked twice (by this function and
        # by the status call back function.
        emulator.remove_status_callback()

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_clicked__test_2_page__custom_iso_file_name_open_button(widget):

    file_path = os.path.join(model.custom.iso_directory, model.custom.iso_file_name)
    if os.path.isfile(file_path):
        file_utilities.select_file_in_browser(file_path)
    else:
        file_utilities.open_directory_in_browser(model.custom.iso_directory)


def on_clicked__test_2_page__custom_iso_checksum_file_name_open_button(widget):
    """
    This function is not used.
    """

    file_path = os.path.join(model.custom.iso_directory, model.status.iso_checksum_file_name)
    if os.path.isfile(file_path):
        file_utilities.select_file_in_browser(file_path)
    else:
        file_utilities.open_directory_in_browser(model.custom.iso_directory)


########################################################################
# Support Functions
########################################################################


def update_status(status):
    """
    A callback function supplied by the client in order to be notified
    whenever the emulator starts or exits.

    Arguments:
    status : int
        emulator.EXITED, emulator.RUNNING, or emulator.ERROR
    """

    if status == emulator.EXITED:

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='cancel',
            back_button_style='text-button',
            is_back_sensitive=True,
            is_back_visible=True,
            is_next_visible=False)

        handle_navigation('cancel')

    elif status == emulator.RUNNING:

        displayer.update_label('test_2_page__banner_label', 'Testing the generated disk image...', False)

        is_virtualization_supported = emulator.host_has_virtualization_support()
        if not is_virtualization_supported:
            message = '• Warning. The host system does not support virtualization. Performance will be degraded.'
            displayer.insert_box_label('test_2_page__alerts_box', message, is_error=True)
        else:
            message = '• The host system supports virtualization for improved performance.'
            displayer.insert_box_label('test_2_page__alerts_box', message)

        if model.emulator_memory > GIB:
            size_in_gib = model.emulator_memory / GIB
            message = f'• The memory available for testing is {locale.format_string("%.2f", size_in_gib, True)} GiB.'
            displayer.insert_box_label('test_2_page__alerts_box', message)
        else:
            size_in_mib = model.emulator_memory / MIB
            message = f'• The memory available for testing is {locale.format_string("%.2f", size_in_mib, True)} MiB.'
            displayer.insert_box_label('test_2_page__alerts_box', message)

        # is_gtk_display_supported = emulator.host_has_gtk_display_support()
        # if not is_gtk_display_supported:
        #     message = '• Warning. The host system does not support GTK display features.'
        #     displayer.insert_box_label('test_2_page__alerts_box', message, is_error=True)
        # else:
        #     message = '• The host system supports GTK display features.'
        #     displayer.insert_box_label('test_2_page__alerts_box', message)

        message = '• Use Ctrl-Alt-F to toggle full screen.'
        displayer.insert_box_label('test_2_page__alerts_box', message)

        message = '• Use Ctrl-Alt-G (or Ctrl-Alt) to toggle mouse and keyboard capture.'
        displayer.insert_box_label('test_2_page__alerts_box', message)

        displayer.reset_buttons(
            back_button_label='❬Stop',
            back_action='cancel',
            back_button_style='destructive-action',
            is_back_sensitive=True,
            is_back_visible=True,
            is_next_visible=False)

    elif status == emulator.ERROR:

        displayer.empty_box('test_2_page__alerts_box')

        message = 'Error. Unable to test the generated disk image.'
        displayer.update_label('test_2_page__banner_label', message, True)
        displayer.set_label_error('test_2_page__banner_label', True)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='cancel',
            back_button_style='suggested-action',
            is_back_sensitive=True,
            is_back_visible=True,
            is_next_visible=False)

    else:

        pass
