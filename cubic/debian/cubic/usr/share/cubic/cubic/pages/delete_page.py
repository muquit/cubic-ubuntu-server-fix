#!/usr/bin/python3

########################################################################
#                                                                      #
# delete_page.py                                                       #
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
import os
import time

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import IMAGE_FILE_NAME
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_0500_MS, SLEEP_1000_MS
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'delete_page'
custom = None

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

    if action == 'delete':

        displayer.update_entry('delete_page__project_directory_entry', model.project.directory)

        # TODO: If custom.iso_file_name does not exist, then display a message below the entry.
        file_path = os.path.join(model.custom.iso_directory, model.custom.iso_file_name)
        if os.path.isfile(file_path):
            displayer.update_entry('delete_page__custom_iso_file_name_entry', model.custom.iso_file_name)
        else:
            displayer.update_entry('delete_page__custom_iso_file_name_entry', '(not available)')

        displayer.update_entry('delete_page__custom_iso_version_number_entry', model.custom.iso_version_number)
        # displayer.update_entry('delete_page__custom_iso_directory_entry', model.custom.iso_directory)
        displayer.update_entry('delete_page__custom_iso_volume_id_entry', model.custom.iso_volume_id)
        displayer.update_entry('delete_page__custom_iso_release_name_entry', model.custom.iso_release_name)
        displayer.update_entry('delete_page__custom_iso_disk_name_entry', model.custom.iso_disk_name)

        displayer.update_status('delete_page__project_configuration_file', BULLET)
        displayer.update_label('delete_page__project_configuration_file_message', '', False)

        displayer.update_status('delete_page__project_iso_mount_point', BULLET)
        displayer.update_label('delete_page__project_iso_mount_point_message', '', False)

        displayer.update_status('delete_page__custom_root_directory', BULLET)
        displayer.update_label('delete_page__custom_root_directory_message', '', False)

        displayer.update_status('delete_page__custom_disk_directory', BULLET)
        displayer.update_label('delete_page__custom_disk_directory_message', '', False)

        displayer.update_status('delete_page__custom_iso_and_checksum', BULLET)

        file_path_pattern = os.path.join(model.project.directory, '*.iso')
        iso_file_paths = glob.glob(file_path_pattern)

        file_path_pattern = os.path.join(model.project.directory, '*.md5')
        iso_checksum_file_paths = glob.glob(file_path_pattern)

        if iso_checksum_file_paths and iso_file_paths:
            count = len(iso_file_paths)
            iso_count_text = constructor.number_as_text(count)
            iso_files_text = constructor.get_plural('file', 'files', count)
            count = len(iso_checksum_file_paths)
            md5_count_text = constructor.number_as_text(count)
            md5_files_text = constructor.get_plural('file', 'files', count)
            label = f'Delete {iso_count_text} ISO disk image {iso_files_text} and {md5_count_text} MD5 checksum {md5_files_text}.'
            enable = True
        elif iso_file_paths:
            count = len(iso_file_paths)
            iso_count_text = constructor.number_as_text(count)
            iso_files_text = constructor.get_plural('file', 'files', count)
            label = f'Delete {iso_count_text} ISO disk image {iso_files_text}.'
            enable = True
        elif iso_checksum_file_paths:
            count = len(iso_checksum_file_paths)
            md5_count_text = constructor.number_as_text(count)
            md5_files_text = constructor.get_plural('file', 'files', count)
            label = f'Delete {md5_count_text} MD5 checksum {md5_files_text}.'
            enable = True
        else:
            label = 'There are no ISO files or MD5 files in this project directory.'
            enable = False

        displayer.reset_buttons(
            back_button_label='Cancel',
            back_action='cancel',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Delete',
            next_action='delete',
            next_button_style='destructive-action',
            is_next_sensitive=True,
            is_next_visible=True)

        displayer.update_check_button_label('delete_page__custom_iso_and_checksum_check_button', label)
        displayer.activate_check_button('delete_page__custom_iso_and_checksum_check_button', enable)
        displayer.set_sensitive('delete_page__custom_iso_and_checksum_check_button', enable)

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

    if action == 'delete':

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

        # Use "button_style='text-button'" if the buttons are reset in
        # the leave/error section.
        #
        # displayer.reset_buttons(back_button_style='text-button', is_back_sensitive=False, next_button_style='text-button', is_next_sensitive=False)

        return

    elif action == 'delete':

        # The following fields must be set before leaving this page:
        #
        # 1. model.project.cubic_version
        #    - Set to model.application.cubic_version in the
        #      initialize_model() function.
        # 2. model.project.create_date
        #    - Set to current date in the initialize_model() function.
        # 3. model.project.directory
        # 4. model.project.configuration
        # 5. model.project.iso_mount_point
        # 6. model.project.custom_root_directory
        # 7. model.project.custom_disk_directory

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        is_error = delete_project_files()

        if is_error: return 'error'  # Stay on this page.

        # Initialize the model.
        initialize_model()
        # Pause to allow the user to see the results.
        time.sleep(SLEEP_1000_MS)

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    elif action == 'error':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        displayer.reset_buttons(is_back_sensitive=True, is_next_sensitive=False)

        # If the following is used, use button_style='text-button' in
        # the leave/cancel section.
        #
        # displayer.reset_buttons(
        #     back_button_label='❬Back',
        #     back_action='cancel',
        #     back_button_style='suggested-action',
        #     is_back_sensitive=True,
        #     is_back_visible=True,
        #     next_button_label='Delete',
        #     next_action='delete',
        #     next_button_style='destructive-action',
        #     is_next_sensitive=False,
        #     is_next_visible=True)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_clicked__delete_page__project_directory_open_button(widget):

    file_utilities.open_directory_in_browser(model.project.directory)


def on_clicked__delete_page__custom_iso_file_name_open_button(widget):

    file_path = os.path.join(model.custom.iso_directory, model.custom.iso_file_name)
    if os.path.isfile(file_path):
        file_utilities.select_file_in_browser(file_path)
    else:
        file_utilities.open_directory_in_browser(model.custom.iso_directory)


########################################################################
# Support Functions
########################################################################


def delete_project_files_TEST():

    is_error = False

    # ------------------------------------------------------------------
    # Unmount and delete the original disk mount point.
    # ------------------------------------------------------------------

    logger.log_value('Unmount the original disk and delete the mount point', model.project.iso_mount_point)
    displayer.update_status('delete_page__project_iso_mount_point', PROCESSING)
    time.sleep(SLEEP_1000_MS)
    displayer.update_status('delete_page__project_iso_mount_point', OK)
    displayer.update_label('delete_page__project_iso_mount_point_message', 'Testing testing testing.', False)
    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the configuration file.
    # ------------------------------------------------------------------

    logger.log_value('Delete the configuration file', model.project.configuration.file_path)
    displayer.update_status('delete_page__project_configuration_file', PROCESSING)
    time.sleep(SLEEP_1000_MS)
    displayer.update_status('delete_page__project_configuration_file', OK)
    displayer.update_label('delete_page__project_configuration_file_message', 'Testing testing testing.', False)
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the custom root directory.
    # ------------------------------------------------------------------

    logger.log_value('Delete the custom root directory', model.project.custom_root_directory)
    displayer.update_status('delete_page__custom_root_directory', PROCESSING)
    time.sleep(SLEEP_1000_MS)
    displayer.update_status('delete_page__custom_root_directory', OK)
    displayer.update_label('delete_page__custom_root_directory_message', 'Testing testing testing.', False)
    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the custom disk directory.
    # ------------------------------------------------------------------

    logger.log_value('Delete the custom disk directory', model.project.custom_disk_directory)
    displayer.update_status('delete_page__custom_disk_directory', PROCESSING)
    time.sleep(SLEEP_1000_MS)
    displayer.update_status('delete_page__custom_disk_directory', OK)
    displayer.update_label('delete_page__custom_disk_directory_message', 'Testing testing testing.', False)
    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the custom disk checksum files and custom disk image files.
    # ------------------------------------------------------------------

    displayer.update_status('delete_page__custom_iso_and_checksum', PROCESSING)
    time.sleep(SLEEP_1000_MS)
    displayer.update_status('delete_page__custom_iso_and_checksum', OK)
    displayer.update_label('delete_page__custom_iso_and_checksum_message', 'Testing testing testing.', False)
    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    return is_error


def delete_project_files():

    displayer.set_sensitive('delete_page__custom_iso_and_checksum_check_button', False)

    is_error = False

    # ------------------------------------------------------------------
    # Unmount and delete the original disk mount point.
    # ------------------------------------------------------------------

    logger.log_value('Unmount the original disk and delete the mount point', model.project.iso_mount_point)
    displayer.update_status('delete_page__project_iso_mount_point', PROCESSING)
    time.sleep(SLEEP_1000_MS)

    if os.path.exists(model.project.iso_mount_point):
        # Unmount the original disk image.
        result, exit_status, signal_status = iso_utilities.unmount(model.project.iso_mount_point)
        if not signal_status:
            displayer.update_status('delete_page__project_iso_mount_point', OK)
            displayer.update_label('delete_page__project_iso_mount_point_message', '', False)
            time.sleep(SLEEP_0500_MS)
            # Delete the mount point.
            logger.log_value('Delete the original disk mount point', model.project.iso_mount_point)
            result, exit_status, signal_status = file_utilities.delete_directory(model.project.iso_mount_point)
            if not signal_status:
                displayer.update_status('delete_page__project_iso_mount_point', OK)
                displayer.update_label('delete_page__project_iso_mount_point_message', '', False)
            else:
                displayer.update_status('delete_page__project_iso_mount_point', ERROR)
                displayer.update_label('delete_page__project_iso_mount_point_message', 'Unable to delete the mount point.', True)
                is_error = True
        else:
            displayer.update_status('delete_page__project_iso_mount_point', ERROR)
            displayer.update_label('delete_page__project_iso_mount_point_message', 'Unable to unmount the iso.', True)
            is_error = True
    else:
        displayer.update_status('delete_page__project_iso_mount_point', OK)
        displayer.update_label('delete_page__project_iso_mount_point_message', 'Nothing to unmount.', False)

    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the configuration file.
    # ------------------------------------------------------------------

    logger.log_value('Delete the configuration file', model.project.configuration.file_path)
    displayer.update_status('delete_page__project_configuration_file', PROCESSING)
    time.sleep(SLEEP_1000_MS)

    if os.path.exists(model.project.configuration.file_path):
        result, exit_status, signal_status = file_utilities.delete_file(model.project.configuration.file_path)
        if not signal_status:
            displayer.update_status('delete_page__project_configuration_file', OK)
            displayer.update_label('delete_page__project_configuration_file_message', '', False)
        else:
            displayer.update_status('delete_page__project_configuration_file', ERROR)
            displayer.update_label('delete_page__project_configuration_file_message', 'Unable to delete this file.', True)
            is_error = True
    else:
        displayer.update_status('delete_page__project_configuration_file', OK)
        displayer.update_label('delete_page__project_configuration_file_message', 'Nothing to delete. This file does not exist.', False)

    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the custom root directory.
    # ------------------------------------------------------------------

    logger.log_value('Delete the custom root directory', model.project.custom_root_directory)
    displayer.update_status('delete_page__custom_root_directory', PROCESSING)
    time.sleep(SLEEP_1000_MS)

    if os.path.exists(model.project.custom_root_directory):
        result, exit_status, signal_status = file_utilities.delete_path_as_root(model.project.custom_root_directory)
        if not signal_status:
            displayer.update_status('delete_page__custom_root_directory', OK)
            displayer.update_label('delete_page__custom_root_directory_message', '', False)
        else:
            displayer.update_status('delete_page__custom_root_directory', ERROR)
            displayer.update_label('delete_page__custom_root_directory_message', 'Unable to delete the customized Linux files.', True)
            is_error = True
    else:
        displayer.update_status('delete_page__custom_root_directory', OK)
        displayer.update_label('delete_page__custom_root_directory_message', 'Nothing to delete. These files not exist.', False)

    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the custom disk directory and ISO partition image files.
    # ------------------------------------------------------------------

    logger.log_value('Delete the custom disk directory', model.project.custom_disk_directory)
    displayer.update_status('delete_page__custom_disk_directory', PROCESSING)
    time.sleep(SLEEP_1000_MS)

    file_path_pattern = os.path.join(model.project.directory, IMAGE_FILE_NAME % '[1-9]')
    image_file_paths = glob.glob(file_path_pattern)
    if os.path.exists(model.project.custom_disk_directory) or image_file_paths:

        is_error_1 = False
        if os.path.exists(model.project.custom_disk_directory):
            # Delete the custom disk directory
            result, exit_status, signal_status = file_utilities.delete_directory(model.project.custom_disk_directory)
            logger.log_value('The result is', result)
            logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')
            if signal_status:
                is_error_1 = True

        is_error_2 = False
        if image_file_paths:
            file_utilities.delete_files_with_pattern(file_path_pattern)
            # Check if all image files were deleted.
            image_file_paths = glob.glob(file_path_pattern)
            if image_file_paths:
                is_error_2 = True

        if is_error_1 or is_error_2:
            displayer.update_status('delete_page__custom_disk_directory', ERROR)
            displayer.update_label('delete_page__custom_disk_directory_message', 'Unable to delete the customized disk image files.', True)
            is_error = True
        else:
            displayer.update_status('delete_page__custom_disk_directory', OK)
            displayer.update_label('delete_page__custom_disk_directory_message', '', False)

    else:
        displayer.update_status('delete_page__custom_disk_directory', OK)
        displayer.update_label('delete_page__custom_disk_directory_message', 'Nothing to delete. These files do not exist.', False)

    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    # ------------------------------------------------------------------
    # Delete the custom disk checksum files and custom disk image files.
    # ------------------------------------------------------------------

    check_button = model.builder.get_object('delete_page__custom_iso_and_checksum_check_button')
    is_active = check_button.get_active()

    logger.log_value('Delete the custom disk checksum files and the custom disk image files?', is_active)
    if is_active:

        displayer.update_status('delete_page__custom_iso_and_checksum', PROCESSING)
        time.sleep(SLEEP_1000_MS)

        file_path_pattern = os.path.join(model.project.directory, '*.md5')
        iso_checksum_file_paths = glob.glob(file_path_pattern)

        file_path_pattern = os.path.join(model.project.directory, '*.iso')
        iso_file_paths = glob.glob(file_path_pattern)

        is_error_1 = False
        for file_path in iso_checksum_file_paths:
            # file_name = os.path.basename(file_path)
            logger.log_value('Delete the custom disk checksum file', file_path)
            result, exit_status, signal_status = file_utilities.delete_file(file_path)
            logger.log_value('The result is', result)
            logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')

            if signal_status:
                is_error_1 = True

        is_error_2 = False
        for file_path in iso_file_paths:
            # file_name = os.path.basename(file_path)
            logger.log_value('Delete the custom disk image file', file_path)
            result, exit_status, signal_status = file_utilities.delete_file(file_path)
            logger.log_value('The result is', result)
            logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')

            if signal_status:
                is_error_2 = True

        if is_error_1 or is_error_2:
            displayer.update_status('delete_page__custom_iso_and_checksum', ERROR)
            is_error = True
        else:
            displayer.update_status('delete_page__custom_iso_and_checksum', OK)

    else:

        displayer.update_status('delete_page__custom_iso_and_checksum', OK)

    # Pause to allow the user to see the result.
    time.sleep(SLEEP_1000_MS)

    return is_error


def initialize_model():

    logger.log_label('Initialize')

    model.project.cubic_version = model.application.cubic_version
    model.project.create_date = constructor.get_current_time_stamp()
    model.project.modify_date = None
    # model.project.directory = None
    # model.project.configuration = None
    # model.project.iso_mount_point = None
    # model.project.custom_root_directory = None
    # model.project.custom_disk_directory = None

    model.original.iso_file_name = None
    model.original.iso_directory = None
    model.original.iso_volume_id = None
    model.original.iso_release_name = None
    model.original.iso_disk_name = None
    model.original.iso_release_notes_url = None

    model.custom.iso_version_number = None
    model.custom.iso_file_name = None
    model.custom.iso_directory = None
    model.custom.iso_volume_id = None
    model.custom.iso_release_name = None
    model.custom.iso_disk_name = None
    model.custom.iso_release_notes_url = None

    # Set all possible values for each attribute to invalid (False).
    # (See Structures class).
    #
    # Casper Section
    #   model.layout.casper_directory
    #   model.layout.initrd_file_name
    #   model.layout.vmlinuz_file_name
    # General Section
    #   model.layout.squashfs_directory
    #   model.layout.squashfs_file_name
    #   model.layout.manifest_file_name
    #   model.layout.minimal_remove_file_name
    #   model.layout.standard_remove_file_name
    #   model.layout.size_file_name
    # Minimal Section
    #   model.layout.minimal_squashfs_file_name
    #   model.layout.minimal_manifest_file_name
    #   model.layout.minimal_size_file_name
    # Standard Section
    #   model.layout.standard_squashfs_file_name
    #   model.layout.standard_manifest_file_name
    #   model.layout.standard_size_file_name
    # Installer / Live Section
    #   model.layout.installer_sources_file_name
    #   model.layout.installer_squashfs_file_name
    #   model.layout.installer_manifest_file_name
    #   model.layout.installer_size_file_name
    #   model.layout.installer_generic_squashfs_file_name
    #   model.layout.installer_generic_manifest_file_name
    #   model.layout.installer_generic_size_file_name
    model.layout.reset()

    model.status.is_success_copy = None
    model.status.is_success_extract = None
    model.status.iso_template = None
    model.status.iso_checksum = None
    model.status.iso_checksum_file_name = None

    model.options.update_os_release = None
    model.options.has_minimal_install = None
    model.options.boot_configurations = None
    model.options.compression = None
