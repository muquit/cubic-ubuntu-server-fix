#!/usr/bin/python3

########################################################################
#                                                                      #
# alert_page.py                                                        #
#                                                                      #
# Copyright (C) 2024 PJ Singh <psingh.cubic@gmail.com>                 #
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

from cubic.constants import BOLD_RED, NORMAL
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'alert_page'

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

    if action == 'alert':

        display_version = constructor.get_display_version(model.project.first_version)
        displayer.update_entry('alert_page__project_cubic_version_entry', display_version)
        displayer.update_entry('alert_page__project_directory_entry', model.project.directory)
        displayer.update_entry('alert_page__custom_iso_version_number_entry', model.custom.iso_version_number)
        displayer.update_entry('alert_page__custom_iso_volume_id_entry', model.custom.iso_volume_id)
        displayer.update_entry('alert_page__custom_iso_release_name_entry', model.custom.iso_release_name)
        displayer.update_entry('alert_page__custom_iso_disk_name_entry', model.custom.iso_disk_name)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Continue❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'error':

        # Handle the error from the leave() function.

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

    if action == 'alert':

        return

    elif action == 'error':

        # Handle the error from the leave() function.

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

    if action == 'back':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'next':

        # The following fields must be set before leaving this page:
        #
        # 1. model.project.cubic_version
        # 2. model.project.create_date
        # 3. model.project.directory
        # 4. model.project.configuration
        # 5. model.project.iso_mount_point
        # 6. model.project.custom_root_directory
        # 7. model.project.custom_disk_directory

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_clicked__alert_page__project_directory_open_button(widget):

    file_utilities.open_directory_in_browser(model.project.directory)
