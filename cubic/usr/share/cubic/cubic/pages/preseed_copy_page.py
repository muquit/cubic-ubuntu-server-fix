#!/usr/bin/python3

########################################################################
#                                                                      #
# preseed_copy_page.py                                                 #
#                                                                      #
# Copyright (C) 2020 PJ Singh <psingh.cubic@gmail.com>                 #
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

import os
import time
import urllib

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import FINAL_PERCENT
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_1000_MS
from cubic.navigator import InterruptException
from cubic.pages import options_page
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.progressor import track_progress

########################################################################
# Global Variables & Constants
########################################################################

name = 'preseed_copy_page'

total_files = 0
file_number = 0

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

    if action == 'copy-preseed':

        # The selected uris and current directory are set in FilesTab.selected_uris() method.

        count = len(model.selected_uris)
        count_text = constructor.number_as_text(count)
        files_text = constructor.get_plural('file', 'files', count)
        message = f'Copy {count_text} {files_text} to {model.current_directory}...'

        # Create a file details list of files to be copied.
        file_details_list = create_file_details_list(model.selected_uris)

        displayer.update_label('preseed_copy_page__progress_message', message, False)
        displayer.update_progress_bar_text('preseed_copy_page__copy_files_progress_bar', None)
        displayer.update_progress_bar_percent('preseed_copy_page__copy_files_progress_bar', 0)
        displayer.update_status('preseed_copy_page__progress', BLANK)
        displayer.update_list_store('preseed_copy_page__file_details__list_store', file_details_list)

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

    if action == 'copy-preseed':

        displayer.reset_buttons(
            back_button_label='Cancel',
            back_action='cancel',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Copy',
            next_action='copy-preseed',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

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

    if action == 'cancel':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'copy-preseed':

        displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=False)

        is_error = copy_files(model.current_directory, model.selected_uris)
        if is_error: return 'error'  # Stay on this page.

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Pause to allow the user to see the result.
        time.sleep(SLEEP_1000_MS)

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Update the model to acknowledge changes.
        # (Only necessary on the Boot Copy page).
        # model.options.boot_configurations = options_page.boot_tab.get_required_file_paths()

        options_page.preseed_tab.remove_tree()
        options_page.boot_tab.remove_tree()

        # Save the model values.
        model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    elif action == 'error':

        # Handle the error from the leave() function.

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################

########################################################################
# Support Functions
########################################################################


def create_file_details_list(uris):

    file_details_list = []

    for file_number, uri in enumerate(uris):
        file_path = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
        file_details_list.append([0, file_path])

    return file_details_list


########################################################################
# Copy Files Functions
########################################################################


def copy_files(current_directory, uris):

    logger.log_label('Copy file(s)')

    global total_files
    total_files = len(uris)

    # It is necessary to strip the leading '/' from the current
    # directory, otherwise os.path.join() considers the current
    # directory to be an absolute path and discards the custom root
    # directory prefix: "If a component is an absolute path, all
    # previous components are thrown away and os.path.joining continues
    # from the absolute path component."
    # (See https://docs.python.org/3/library/os.path.html).
    target_directory = os.path.abspath(os.path.join(model.project.custom_disk_directory, current_directory.strip(os.path.sep)))

    logger.log_value('The current directory is', current_directory)
    logger.log_value('The custom disk directory is', model.project.custom_disk_directory)
    logger.log_value('The target directory is', target_directory)

    displayer.update_status('preseed_copy_page__progress', PROCESSING)

    global file_number
    try:
        for file_number, uri in enumerate(uris):
            file_path = urllib.parse.unquote(urllib.parse.urlparse(uri).path)
            if total_files == 1:
                message = f'Copying one file to {current_directory}...'
            else:
                message = f'Copying file {(file_number+1):n} of {total_files:n} to {current_directory}...'
            displayer.update_label('preseed_copy_page__progress_message', message, False)
            displayer.scroll_to_tree_view_row('preseed_copy_page__tree_view', file_number)
            displayer.select_tree_view_row('preseed_copy_page__tree_view', file_number)
            copy_file(file_path, file_number, target_directory, total_files)
    except InterruptException as exception:
        displayer.update_status('preseed_copy_page__progress', ERROR)
        if 'No space left on device' in str(exception):
            # message = f'<span foreground="red">Error. Unable to copy files to {current_directory}. Not enough space on the disk.</span>'
            message = f'Error. Unable to copy files to {current_directory}. Not enough space on the disk.'
        else:
            # message = f'<span foreground="red">Error. Unable to copy files to {current_directory}.</span>'
            message = f'Error. Unable to copy files to {current_directory}.'
        displayer.update_label('preseed_copy_page__progress_message', message, True)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        displayer.update_status('preseed_copy_page__progress', ERROR)
        if 'No space left on device' in str(exception):
            # message = f'<span foreground="red">Error. Unable to copy files to {current_directory}. Not enough space on the disk.</span>'
            message = f'Error. Unable to copy files to {current_directory}. Not enough space on the disk.'
        else:
            # message = f'<span foreground="red">Error. Unable to copy files to {current_directory}.</span>'
            message = f'Error. Unable to copy files to {current_directory}.'
        displayer.update_label('preseed_copy_page__progress_message', message, True)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    displayer.update_status('preseed_copy_page__progress', OK)
    number_text = constructor.number_as_text(total_files)
    plural_text = constructor.get_plural('file', 'files', total_files)
    message = f'Copied {number_text} {plural_text} to {current_directory}.'
    displayer.update_label('preseed_copy_page__progress_message', message, False)
    return False  # (No error)


def copy_file(file_path, file_number, directory, total_files):

    logger.log_label(f'Copy file number {file_number+1} of {total_files}')

    logger.log_value('The file is', file_path)
    logger.log_value('The target directory is', directory)

    program = os.path.join(model.application.directory, 'commands', 'copy-path')
    command = ['pkexec', program, file_path, directory]

    # The progress callback function.
    def progress_callback(percent):
        global total_files
        global file_number
        total_percent = (FINAL_PERCENT * file_number + percent) / total_files
        displayer.update_progress_bar_percent('preseed_copy_page__copy_files_progress_bar', total_percent)
        displayer.update_list_store_progress_bar_percent('preseed_copy_page__file_details__list_store', file_number, percent)
        if total_percent % 10 == 0:
            logger.log_value('Completed', f'{total_percent:n}%')

    track_progress(command, progress_callback, quantity=total_files)
