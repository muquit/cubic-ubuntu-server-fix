#!/usr/bin/python3

########################################################################
#                                                                      #
# finish_page.py                                                       #
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

import glob
import locale
import os
import time

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import IMAGE_FILE_NAME
from cubic.constants import MIB, GIB
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_0500_MS, SLEEP_1500_MS
from cubic.navigator import handle_navigation
from cubic.pages import options_page
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import emulator
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'finish_page'

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

    if action == 'cancel':

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style='text-button',
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Close',
            next_action='close',
            next_button_style='destructive-action',
            is_next_sensitive=True,
            is_next_visible=True)

        validate_test_header_bar_button()

        return

    if action == 'finish':

        store_generated_iso_values()

        displayer.update_entry('finish_page__custom_iso_version_number_entry', model.custom.iso_version_number)
        displayer.update_entry('finish_page__custom_iso_file_name_entry', model.custom.iso_file_name)
        displayer.update_entry('finish_page__custom_iso_disk_size_entry', get_size_description(model.iso_file_size))
        displayer.update_entry('finish_page__custom_iso_directory_entry', model.custom.iso_directory)
        displayer.update_entry('finish_page__custom_iso_volume_id_entry', model.custom.iso_volume_id)
        displayer.update_entry('finish_page__custom_iso_release_name_entry', model.custom.iso_release_name)
        displayer.update_entry('finish_page__custom_iso_disk_name_entry', model.custom.iso_disk_name)
        displayer.update_entry('finish_page__custom_iso_checksum_entry', model.status.iso_checksum)
        displayer.update_entry('finish_page__custom_iso_checksum_file_name_entry', model.status.iso_checksum_file_name)

        displayer.update_status('finish_page__delete_project_files', BLANK)
        displayer.activate_check_button('finish_page__delete_project_files_check_button', False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Close',
            next_action='close',
            next_button_style='destructive-action',
            is_next_sensitive=True,
            is_next_visible=True)

        validate_test_header_bar_button()

        return

    elif action == 'next':

        # For testing only.

        displayer.update_entry('finish_page__custom_iso_version_number_entry', model.custom.iso_version_number)
        displayer.update_entry('finish_page__custom_iso_file_name_entry', model.custom.iso_file_name)
        displayer.update_entry('finish_page__custom_iso_disk_size_entry', get_size_description(model.iso_file_size))
        displayer.update_entry('finish_page__custom_iso_directory_entry', model.custom.iso_directory)
        displayer.update_entry('finish_page__custom_iso_volume_id_entry', model.custom.iso_volume_id)
        displayer.update_entry('finish_page__custom_iso_release_name_entry', model.custom.iso_release_name)
        displayer.update_entry('finish_page__custom_iso_disk_name_entry', model.custom.iso_disk_name)
        displayer.update_entry('finish_page__custom_iso_checksum_entry', model.status.iso_checksum)
        displayer.update_entry('finish_page__custom_iso_checksum_file_name_entry', model.status.iso_checksum_file_name)

        displayer.update_status('finish_page__delete_project_files', BLANK)
        displayer.activate_check_button('finish_page__delete_project_files_check_button', False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Close',
            next_action='close',
            next_button_style='destructive-action',
            is_next_sensitive=True,
            is_next_visible=True)

        validate_test_header_bar_button()

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

    if action == 'cancel':

        return

    elif action == 'finish':

        return

    elif action == 'next':

        # For testing only.

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

        displayer.set_visible('finish_page__test_header_bar_button', False)

        return

    elif action == 'test':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('finish_page__test_header_bar_button', False)

        return

    if action == 'close':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_sensitive('finish_page__test_header_bar_button', False)

        displayer.set_sensitive('finish_page__delete_project_files_check_button', False)

        options_page.preseed_tab.remove_tree()
        options_page.boot_tab.remove_tree()

        # Save the model values.
        # model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        # Delete project files.

        check_button = model.builder.get_object('finish_page__delete_project_files_check_button')
        is_active = check_button.get_active()
        logger.log_value('Delete the project files?', is_active)
        if is_active:
            displayer.update_status('finish_page__delete_project_files', PROCESSING)
            time.sleep(SLEEP_0500_MS)
            delete_project_files()
            displayer.update_status('finish_page__delete_project_files', OK)
            # Pause to allow the user to see the result.
            time.sleep(SLEEP_1500_MS)

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_sensitive('finish_page__test_header_bar_button', False)

        options_page.preseed_tab.remove_tree()
        options_page.boot_tab.remove_tree()

        # Save the model values.
        # model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_clicked__finish_page__test_header_bar_button(widget):

    logger.log_title('Clicked generate page test button')

    handle_navigation('test')


def on_clicked__finish_page__custom_iso_file_name_open_button(widget):

    file_path = os.path.join(model.custom.iso_directory, model.custom.iso_file_name)
    if os.path.isfile(file_path):
        file_utilities.select_file_in_browser(file_path)
    else:
        file_utilities.open_directory_in_browser(model.custom.iso_directory)


def on_clicked__finish_page__custom_iso_checksum_file_name_open_button(widget):

    file_path = os.path.join(model.custom.iso_directory, model.status.iso_checksum_file_name)
    if os.path.isfile(file_path):
        file_utilities.select_file_in_browser(file_path)
    else:
        file_utilities.open_directory_in_browser(model.custom.iso_directory)


########################################################################
# Support Functions
########################################################################


def get_size_description(size_in_bytes):

    if size_in_bytes > GIB:
        size_in_gib = size_in_bytes / GIB
        size_description = f'{locale.format_string("%.2f", size_in_gib, True)} GiB ({size_in_bytes:n} bytes)'
    else:
        size_in_mib = size_in_bytes / MIB
        size_description = f'{locale.format_string("%.2f", size_in_mib, True)} MiB ({size_in_bytes:n} bytes)'

    return size_description


def store_generated_iso_values():
    """
    Save the generated ISO values from the model.
      - iso_version_number
      - iso_file_name
      - iso_directory
      - iso_volume_id
      - iso_release_name
      - iso_disk_name
      - iso_release_notes_url
      - iso_checksum
      - iso_checksum_file_name
    """

    logger.log_label('Save the generated ISO values from the model')

    # Update fields.
    model.generated.iso_version_number = model.custom.iso_version_number
    model.generated.iso_file_name = model.custom.iso_file_name
    model.generated.iso_directory = model.custom.iso_directory
    model.generated.iso_volume_id = model.custom.iso_volume_id
    model.generated.iso_release_name = model.custom.iso_release_name
    model.generated.iso_disk_name = model.custom.iso_disk_name
    model.generated.iso_release_notes_url = model.custom.iso_release_notes_url
    # model.generated.iso_checksum = model.status.iso_checksum
    # model.generated.iso_checksum_file_name = model.status.iso_checksum_file_name


def unmount_original_iso():

    is_error = False

    #
    # Unmount and delete the original disk mount point.
    #
    logger.log_value('Unmount the original disk and delete the mount point', model.project.iso_mount_point)
    if os.path.exists(model.project.iso_mount_point):
        # Unmount the original disk image.
        result, exit_status, signal_status = iso_utilities.unmount(model.project.iso_mount_point)
        if not signal_status:
            # Delete the mount point.
            logger.log_value('Delete the original disk mount point', model.project.iso_mount_point)
            result, exit_status, signal_status = file_utilities.delete_directory(model.project.iso_mount_point)
            if not signal_status:
                logger.log_value('Deleted the original disk mount point', model.project.iso_mount_point)
                pass
            else:
                logger.log_value('Unable to delete the original disk mount point', model.project.iso_mount_point)
                is_error = True
        else:
            logger.log_value('Unable to unmount the original disk and delete the mount point', model.project.iso_mount_point)
            is_error = True
    else:
        logger.log_value('Skipping. The original disk mount point does not exist', model.project.iso_mount_point)

    return is_error


def delete_project_files():

    is_error = False

    #
    # Delete the configuration file
    #
    logger.log_value('Delete the configuration file', model.project.configuration.file_path)
    # time.sleep(SLEEP_1000_MS)
    if os.path.exists(model.project.configuration.file_path):
        result, exit_status, signal_status = file_utilities.delete_file(model.project.configuration.file_path)
        if not signal_status:
            # OK
            pass
        else:
            is_error = True
    else:
        # Skip
        pass

    #
    # Delete the custom root directory.
    #
    logger.log_value('Delete the custom root directory', model.project.custom_root_directory)
    # time.sleep(SLEEP_1000_MS)
    if os.path.exists(model.project.custom_root_directory):
        result, exit_status, signal_status = file_utilities.delete_path_as_root(model.project.custom_root_directory)
        if not signal_status:
            # OK
            pass
        else:
            is_error = True
    else:
        # Skip
        pass

    #
    # Delete the custom disk directory.
    #
    logger.log_value('Delete the custom disk directory', model.project.custom_disk_directory)
    # time.sleep(SLEEP_1000_MS)
    if os.path.exists(model.project.custom_disk_directory):
        result, exit_status, signal_status = file_utilities.delete_directory(model.project.custom_disk_directory)
        if not signal_status:
            # OK
            pass
        else:
            is_error = True
    else:
        # Skip
        pass

    #
    # Delete the ISO partition image files.
    #
    file_path_pattern = os.path.join(model.project.directory, IMAGE_FILE_NAME % '[1-9]')
    image_file_paths = glob.glob(file_path_pattern)
    logger.log_value('Delete the ISO partition image files', image_file_paths)
    # time.sleep(SLEEP_1000_MS)

    if image_file_paths:
        file_utilities.delete_files_with_pattern(file_path_pattern)
        # Check if all image files were deleted.
        image_file_paths = glob.glob(file_path_pattern)
        if image_file_paths:
            is_error = True
    else:
        # Skip
        pass

    return is_error


########################################################################
# Validation Functions
########################################################################


def validate_page():

    return True


########################################################################
# Test Functions
########################################################################


def validate_test_header_bar_button():

    # Do not show the Test button if the dummy Qemu package is
    # installed. The version of qemu-system-x86 should be >=1:4.2; the
    # dummy package version is 0.0.
    if constructor.get_package_version('qemu-system-x86') == '0.0':
        logger.log_value('Is the dummy Qemu package installed', 'Yes')
        displayer.set_sensitive('finish_page__test_header_bar_button', False)
        displayer.set_visible('finish_page__test_header_bar_button', False)
        logger.log_value('Enable testing?', 'No')
        return

    # Do not enable the Test button if the generated ISO file does not
    # exist.
    custom_iso_file_path = os.path.join(model.generated.iso_directory, model.generated.iso_file_name)
    if not os.path.exists(custom_iso_file_path):
        logger.log_value('Does the custom ISO file exist?', 'No')
        displayer.set_sensitive('finish_page__test_header_bar_button', False)
        displayer.set_visible('finish_page__test_header_bar_button', True)
        logger.log_value('Enable testing?', 'No')
        return

    # Do not enable the Test button if there is less than 1.5 GiB
    # available memory.
    is_adequate = emulator.check_available_memory()
    if not is_adequate:
        displayer.set_sensitive('finish_page__test_header_bar_button', False)
        displayer.set_visible('finish_page__test_header_bar_button', True)
        logger.log_value('System has adequate available memory to enable testing?', 'No')
        logger.log_value('Enable testing?', 'No')
        return

    # Enable and show the Test button.
    displayer.set_sensitive('finish_page__test_header_bar_button', True)
    displayer.set_visible('finish_page__test_header_bar_button', True)
    logger.log_value('The generated ISO file path is', custom_iso_file_path)
    logger.log_value('System has adequate available memory to enable testing?', 'Yes')
    logger.log_value('Enable testing?', 'Yes')
