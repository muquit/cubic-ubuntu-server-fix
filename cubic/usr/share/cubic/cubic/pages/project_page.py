#!/usr/bin/python3

########################################################################
#                                                                      #
# project_page.py                                                      #
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
"""
The following fields must be set before entering this page:

1. model.project.cubic_version
2. model.project.create_date
3. model.project.directory
4. model.project.configuration
5. model.project.iso_mount_point
6. model.project.custom_root_directory
7. model.project.custom_disk_directory
"""

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

import os
import re
import urllib

from cubic.choosers import directory_chooser
from cubic.choosers import iso_image_chooser
from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import GZIP
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.navigator import handle_navigation
from cubic.utilities.structures import Fields, IsoFields, IsoFieldsHistory
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

name = 'project_page'
custom = None
original = None
status = None
options = None
custom_history = IsoFieldsHistory()

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

    global original
    global custom
    global status
    global options
    global installer

    if action == 'back':

        # Set status from the model, because values may have changed on
        # subsequent pages (Extract page, Generate page).
        status = initialize_status_from_model()

        # Set options from the model, because values may have changed on
        # subsequent pages (Packages page, Options page,
        # Compression page).
        options = initialize_options_from_model()

        # Validation is not required since nothing changed.
        # validate_page()

        # Navigation buttons are also set in the validate_page() function.
        if status.iso_template and       \
           status.is_success_analyze and \
           status.is_success_copy and    \
           status.is_success_extract:
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Customize❭',
                next_action='next-terminal',
                next_button_style='suggested-action',
                is_next_sensitive=True,
                is_next_visible=True)
        else:
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style=None,
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style='suggested-action',
                is_next_sensitive=True,
                is_next_visible=True)

        validate_test_header_bar_button()

        # Show the Delete button because the project already exists.
        displayer.set_visible('project_page__delete_header_bar_button', True)

        displayer.set_visible('project_page__header_bar_box', True)

        return

    elif action == 'cancel':

        # Validation is not required since nothing changed.
        # validate_page()

        # Navigation buttons are also set in the validate_page() function.
        if status.iso_template and       \
           status.is_success_analyze and \
           status.is_success_copy and    \
           status.is_success_extract:
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style='text-button',
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Customize❭',
                next_action='next-terminal',
                next_button_style='suggested-action',
                is_next_sensitive=True,
                is_next_visible=True)
        else:
            displayer.reset_buttons(
                back_button_label='❬Back',
                back_action='back',
                back_button_style='text-button',
                is_back_sensitive=True,
                is_back_visible=True,
                next_button_label='Next❭',
                next_action='next',
                next_button_style='suggested-action',
                is_next_sensitive=True,
                is_next_visible=True)

        validate_test_header_bar_button()

        # Show the Delete button because the project already exists.
        displayer.set_visible('project_page__delete_header_bar_button', True)

        displayer.set_visible('project_page__header_bar_box', True)

        return

    elif action == 'delete':

        original = None
        custom = None

        # Set status before initializing original, because
        # the original ISO file name validator requires
        # is_success_analyze, is_success_copy, and
        # is_success_extract.
        status = initialize_status()
        options = initialize_options()

        original = initialize_original()
        custom = initialize_custom()
        store_generated_iso_values()

        custom_history.reset()

        display_original_fields(original)
        display_custom_fields(custom)

        validate_page()

        validate_test_header_bar_button()

        # Hide the Delete button because the project was deleted.
        displayer.set_visible('project_page__delete_header_bar_button', False)

        displayer.set_visible('project_page__header_bar_box', True)

        return

    elif action == 'next':

        original = None
        custom = None

        if model.project.modify_date:

            # There is a saved configuration.

            configured_original_iso_file_path = os.path.join(model.original.iso_directory, model.original.iso_file_name)
            mount_original_iso(configured_original_iso_file_path)

            # Set the original and custom ISO release notes URLs on the
            # model. Because the original ISO release notes URL can only
            # be set after the original ISO is mounted, both of these
            # values are not set on the Start page.
            model.original.iso_release_notes_url = iso_utilities.get_iso_release_notes_url(model.project.iso_mount_point)
            model.custom.iso_release_notes_url = iso_utilities.get_iso_release_notes_url(model.project.custom_disk_directory)

            # Set status before initializing original, because
            # the original ISO file name validator requires
            # is_success_analyze, is_success_copy, and
            # is_success_extract.
            status = initialize_status_from_model()
            options = initialize_options_from_model()

            original = initialize_original_from_model()
            custom = initialize_custom_from_model()
            store_generated_iso_values()

            custom_history.reset()
            if custom.is_valid:
                custom_history.insert(custom)

            display_original_fields(original)
            display_custom_fields(custom)

            validate_page()

            validate_test_header_bar_button()

            # Show the Delete button because the project already exists.
            displayer.set_visible('project_page__delete_header_bar_button', True)

            displayer.set_visible('project_page__header_bar_box', True)

        else:

            # Set the original and custom ISO release notes URLs on the
            # model.
            model.original.iso_release_notes_url = None
            model.custom.iso_release_notes_url = None

            # Set status before initializing original, because
            # the original ISO file name validator requires
            # is_success_analyze, is_success_copy, and
            # is_success_extract.
            status = initialize_status()
            options = initialize_options()

            original = initialize_original()
            custom = initialize_custom()

            custom_history.reset()

            display_original_fields(original)
            display_custom_fields(custom)

            validate_page()

            validate_test_header_bar_button()

            # Hide the Delete button because the project does not exist.
            displayer.set_visible('project_page__delete_header_bar_button', False)

            displayer.set_visible('project_page__header_bar_box', True)

            if model.arguments.file_path and model.arguments.directory == model.project.directory:
                selected_original_iso_file_path(model.arguments.file_path)

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

    if action == 'back':

        return

    elif action == 'cancel':

        return

    elif action == 'delete':

        return

    elif action == 'next':

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

        displayer.set_visible('project_page__header_bar_box', False)

        displayer.set_visible('project_page__test_header_bar_button', False)

        # Hide the Delete button on other pages.
        displayer.set_visible('project_page__delete_header_bar_button', False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    elif action == 'test':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('project_page__header_bar_box', False)

        displayer.set_visible('project_page__test_header_bar_button', False)

        # Hide the Delete button on other pages.
        displayer.set_visible('project_page__delete_header_bar_button', False)

        return

    elif action == 'delete':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('project_page__header_bar_box', False)

        displayer.set_visible('project_page__test_header_bar_button', False)

        # Hide the Delete button on other pages.
        displayer.set_visible('project_page__delete_header_bar_button', False)

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('project_page__header_bar_box', False)

        displayer.set_visible('project_page__test_header_bar_button', False)

        # Hide the Delete button on other pages.
        displayer.set_visible('project_page__delete_header_bar_button', False)

        # Copy the values to the model.

        # Project
        # model.project.cubic_version = model.application.cubic_version
        # model.project.create_date = model.project.create_date
        model.project.modify_date = constructor.get_current_time_stamp()
        # model.project.directory = model.project.directory

        # Original
        model.original.iso_file_name = original.iso_file_name.value
        model.original.iso_directory = original.iso_directory.value
        model.original.iso_volume_id = original.iso_volume_id.value
        model.original.iso_release_name = original.iso_release_name.value
        model.original.iso_disk_name = original.iso_disk_name.value
        model.original.iso_release_notes_url = original.iso_release_notes_url.value

        # Custom
        model.custom.iso_version_number = custom.iso_version_number.value
        model.custom.iso_file_name = custom.iso_file_name.value
        model.custom.iso_directory = custom.iso_directory.value
        model.custom.iso_volume_id = custom.iso_volume_id.value
        model.custom.iso_release_name = custom.iso_release_name.value
        model.custom.iso_disk_name = custom.iso_disk_name.value
        model.custom.iso_release_notes_url = custom.iso_release_notes_url.value

        # Status
        model.status.is_success_analyze = status.is_success_analyze
        model.status.is_success_copy = status.is_success_copy
        model.status.is_success_extract = status.is_success_extract
        model.status.iso_template = status.iso_template
        model.status.iso_checksum = status.iso_checksum
        model.status.iso_checksum_file_name = status.iso_checksum_file_name

        # Options
        model.options.update_os_release = custom.update_os_release.value
        model.options.has_minimal_install = options.has_minimal_install
        model.options.boot_configurations = options.boot_configurations
        model.options.compression = options.compression

        # Save the model values.
        model.project.configuration.save()
        save_iso_release_notes_url()

        if custom.is_valid and custom != custom_history.current():
            custom_history.insert(custom)

        return

    elif action == 'next-terminal':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('project_page__header_bar_box', False)

        displayer.set_visible('project_page__test_header_bar_button', False)

        # Hide the Delete button on other pages.
        displayer.set_visible('project_page__delete_header_bar_button', False)

        # Copy the values to the model.

        # Project
        # model.project.cubic_version = model.application.cubic_version
        # model.project.create_date = model.project.create_date
        model.project.modify_date = constructor.get_current_time_stamp()
        # model.project.directory = model.project.directory

        # Original
        model.original.iso_file_name = original.iso_file_name.value
        model.original.iso_directory = original.iso_directory.value
        model.original.iso_volume_id = original.iso_volume_id.value
        model.original.iso_release_name = original.iso_release_name.value
        model.original.iso_disk_name = original.iso_disk_name.value
        model.original.iso_release_notes_url = original.iso_release_notes_url.value

        # Custom
        model.custom.iso_version_number = custom.iso_version_number.value
        model.custom.iso_file_name = custom.iso_file_name.value
        model.custom.iso_directory = custom.iso_directory.value
        model.custom.iso_volume_id = custom.iso_volume_id.value
        model.custom.iso_release_name = custom.iso_release_name.value
        model.custom.iso_disk_name = custom.iso_disk_name.value
        model.custom.iso_release_notes_url = custom.iso_release_notes_url.value

        # Status
        model.status.is_success_analyze = status.is_success_analyze
        model.status.is_success_copy = status.is_success_copy
        model.status.is_success_extract = status.is_success_extract
        model.status.iso_template = status.iso_template
        model.status.iso_checksum = status.iso_checksum
        model.status.iso_checksum_file_name = status.iso_checksum_file_name

        # Options
        model.options.update_os_release = custom.update_os_release.value
        model.options.has_minimal_install = options.has_minimal_install
        model.options.boot_configurations = options.boot_configurations
        model.options.compression = options.compression

        # Save the model values.
        model.project.configuration.save()
        save_iso_release_notes_url()

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_sensitive('project_page__header_bar_box', False)

        displayer.set_sensitive('project_page__test_header_bar_button', False)

        displayer.set_sensitive('project_page__delete_header_bar_button', False)

        # Do not save the model values because they must be acknowledged first.
        # model.project.configuration.save()
        # save_iso_release_notes_url()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('project_page__header_bar_box', False)

        displayer.set_visible('project_page__test_header_bar_button', False)

        displayer.set_visible('project_page__delete_header_bar_button', False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'


########################################################################
# File Chooser Functions
########################################################################


def mount_original_iso(original_iso_file_path):

    if not iso_utilities.is_mounted(model.project.iso_mount_point):
        # Nothing is mounted on the mount point.
        # Create the mount point (if necessary) and mount this iso.
        file_utilities.make_directory(model.project.iso_mount_point)
        user_id = os.getuid()
        group_id = os.getgid()
        iso_utilities.mount(original_iso_file_path, model.project.iso_mount_point, user_id, group_id)
    elif not iso_utilities.is_mounted(model.project.iso_mount_point, original_iso_file_path):
        # A different ISO is mounted on the mount point.
        # Unmount the other iso, and then mount this iso.
        user_id = os.getuid()
        group_id = os.getgid()
        iso_utilities.unmount(model.project.iso_mount_point)
        iso_utilities.mount(original_iso_file_path, model.project.iso_mount_point, user_id, group_id)
    else:
        # This ISO is already mounted.
        pass


def selected_original_iso_file_path(original_iso_file_path):

    # logger.log_value('The selected file path is', original_iso_file_path)

    global original
    global custom
    global status
    global options
    global installer

    if os.path.isfile(original_iso_file_path):

        # A valid ISO file was supplied.

        if model.project.modify_date:

            # There is a saved configuration.

            configured_original_iso_file_path = os.path.join(model.original.iso_directory, model.original.iso_file_name)
            if configured_original_iso_file_path == original_iso_file_path:

                # The saved configuration is valid.

                mount_original_iso(original_iso_file_path)

                # Set status before initializing original, because
                # the original ISO file name validator requires
                # is_success_analyze, is_success_copy, and
                # is_success_extract.
                status = initialize_status_from_model()
                options = initialize_options_from_model()

                original = initialize_original_from_model()
                custom = initialize_custom_from_model()

                custom_history.reset()
                if custom.is_valid:
                    custom_history.insert(custom)

                display_original_fields(original)
                display_custom_fields(custom)

                validate_page()

            else:

                # The saved configuration is invalid.

                if custom.is_valid and custom != custom_history.current():
                    custom_history.insert(custom)

                mount_original_iso(original_iso_file_path)

                # Set status before initializing original, because
                # the original ISO file name validator requires
                # is_success_analyze, is_success_copy, and
                # is_success_extract.
                status = initialize_status_from_model()
                # Overwrite ISO configuration and boot files.
                # Always set is success copy to False whenever ISO
                # template is set to None.
                status.is_success_analyze = False
                status.is_success_copy = False
                # status.is_success_extract = False or True
                status.iso_template = None
                options = initialize_options()

                original = initialize_original_from_iso(original_iso_file_path)
                # Do not use custom values from the saved configuration.
                custom = initialize_custom_from_iso()

                display_original_fields(original)
                display_custom_fields(custom)

                validate_page()

        else:

            # There is no saved configuration.

            # Mount the disk for initialize_original_from_iso().
            mount_original_iso(original_iso_file_path)

            # Set status before initializing original, because
            # the original ISO file name validator requires
            # is_success_analyze, is_success_copy, and
            # is_success_extract.
            status = initialize_status()
            options = initialize_options()

            original = initialize_original_from_iso(original_iso_file_path)
            custom = initialize_custom_from_iso()

            custom_history.reset()
            if custom.is_valid:
                custom_history.insert(custom)

            display_original_fields(original)
            display_custom_fields(custom)

            validate_page()

        # Update the previous application ISO file path to the newly
        # selected file path.
        model.application.iso_file_path = original_iso_file_path

    else:

        # A valid ISO file was not supplied.

        iso_utilities.unmount(model.project.iso_mount_point)

        # Set status before initializing original, because
        # the original ISO file name validator requires
        # is_success_analyze, is_success_copy, and
        # is_success_extract.
        status = initialize_status()
        options = initialize_options()

        original = initialize_original()
        custom = initialize_custom()

        custom_history.reset()

        display_original_fields(original)
        display_custom_fields(custom)

        validate_page()


def selected_custom_iso_directory(directory):

    # logger.log_value('The selected directory is', original_iso_file_path)

    # Set custom fields.
    custom.iso_directory.value = directory

    # Display custom fields.
    displayer.update_entry('project_page__custom_iso_directory_entry', custom.iso_directory.value)


########################################################################
# Initialization Functions
########################################################################

# ----------------------------------------------------------------------
# Initialize to Default Values
# ----------------------------------------------------------------------


def initialize_original():

    logger.log_label('Initialize the original fields')

    fields = IsoFields('original')

    # Add validators.
    fields.iso_file_name.validator = validate_original_iso_file_name
    fields.iso_directory.validator = validate_original_iso_directory
    fields.iso_volume_id.validator = validate_original_iso_volume_id
    fields.iso_release_name.validator = validate_original_iso_release_name
    fields.iso_disk_name.validator = validate_original_iso_disk_name
    fields.iso_release_notes_url.validator = validate_original_iso_release_notes_url

    return fields


def initialize_custom():

    logger.log_label('Initialize the custom fields')

    fields = IsoFields('custom')

    # Add validators.
    fields.iso_version_number.validator = validate_custom_iso_version_number
    fields.iso_file_name.validator = validate_custom_iso_file_name
    fields.iso_directory.validator = validate_custom_iso_directory
    fields.iso_volume_id.validator = validate_custom_iso_volume_id
    fields.iso_release_name.validator = validate_custom_iso_release_name
    fields.iso_disk_name.validator = validate_custom_iso_disk_name
    fields.iso_release_notes_url.validator = validate_custom_iso_release_notes_url
    fields.update_os_release.validator = validate_custom_update_os_release

    return fields


def initialize_status():

    logger.log_label('Initialize the status fields')

    fields = Fields('status')

    fields.is_success_analyze = False
    fields.is_success_copy = False
    fields.is_success_extract = False
    fields.iso_template = None
    fields.iso_checksum = None
    fields.iso_checksum_file_name = None

    return fields


def initialize_options():

    logger.log_label('Initialize the options fields')

    fields = Fields('options')

    # The field update_os_release is stored in "custom" IsoFields
    # instead of "options" Fields, so changes can be tracked in
    # custom_history to permit undo and redo. This value is initialized
    # to True in the initialize_custom() function.
    # fields.update_os_release = True
    fields.has_minimal_install = None
    fields.boot_configurations = []
    fields.compression = GZIP

    return fields


# ----------------------------------------------------------------------
# Initialize from ISO
# ----------------------------------------------------------------------


def initialize_original_from_iso(original_iso_file_path):
    """
    Initialize the following original fields from the original ISO and
    register the validators.
      - iso_file_name
      - iso_directory
      - iso_volume_id
      - iso_release_name
      - iso_disk_name
      - iso_release_notes_url
    The original ISO does not have an iso_version_number, so the
    iso_version_number value and validator are not set. The
    iso_version_number value defaults to None, and the is_valid property
    is set to True to compensate for the unregistered validator.
    """

    logger.log_label('Initialize the original fields from the ISO')

    fields = IsoFields('original')

    # Update fields.
    fields.iso_directory.value, fields.iso_file_name.value = os.path.split(original_iso_file_path)
    # fields.iso_file_name.value
    # fields.iso_directory.value
    fields.iso_volume_id.value = iso_utilities.get_iso_volume_id(original_iso_file_path)
    fields.iso_release_name.value = iso_utilities.get_iso_release_name(model.project.iso_mount_point)
    fields.iso_disk_name.value = iso_utilities.get_iso_disk_name(model.project.iso_mount_point)
    fields.iso_release_notes_url.value = iso_utilities.get_iso_release_notes_url(model.project.iso_mount_point)

    # Add validators.
    # Do not add a validator for ISO version number, because the
    # original section does not display this field. However, explicitly
    # set iso_version_number.is_valid to True, because IsoFields.is_valid
    # checks if all fields are valid.
    fields.iso_version_number.is_valid = True
    fields.iso_file_name.validator = validate_original_iso_file_name
    fields.iso_directory.validator = validate_original_iso_directory
    fields.iso_volume_id.validator = validate_original_iso_volume_id
    fields.iso_release_name.validator = validate_original_iso_release_name
    fields.iso_disk_name.validator = validate_original_iso_disk_name
    fields.iso_release_notes_url.validator = validate_original_iso_release_notes_url
    # Do not add a validator for update OS release, because the original
    # section does not display this field. However, explicitly set
    # update_os_release.is_valid to True, because IsoFields.is_valid
    # checks if all fields are valid.
    fields.update_os_release.is_valid = True

    return fields


def initialize_custom_from_iso():
    """
    Initialize the following custom fields by constructing them from the
    original ISO values, and register the validators.
      - iso_version_number
      - iso_file_name
      - iso_directory (always set to the project directory)
      - iso_volume_id
      - iso_release_name
      - iso_disk_name
      - iso_release_notes_url
      - update_os_release (always initialize to True)
    """
    logger.log_label('Initialize the custom fields from the ISO')

    fields = IsoFields('custom')

    # Update fields.
    fields.iso_version_number.value = constructor.construct_custom_iso_version_number()
    fields.iso_file_name.value = constructor.construct_custom_iso_file_name(original.iso_file_name.value, fields.iso_version_number.value)
    fields.iso_directory.value = model.project.directory
    fields.iso_volume_id.value = constructor.construct_custom_iso_volume_id(original.iso_volume_id.value, fields.iso_version_number.value)
    fields.iso_release_name.value = constructor.construct_custom_iso_release_name(original.iso_release_name.value)
    fields.iso_disk_name.value = constructor.construct_custom_iso_disk_name(fields.iso_volume_id.value, fields.iso_release_name.value)
    fields.iso_release_notes_url.value = original.iso_release_notes_url.value
    fields.update_os_release.value = True

    # Add validators.
    fields.iso_version_number.validator = validate_custom_iso_version_number
    fields.iso_file_name.validator = validate_custom_iso_file_name
    fields.iso_directory.validator = validate_custom_iso_directory
    fields.iso_volume_id.validator = validate_custom_iso_volume_id
    fields.iso_release_name.validator = validate_custom_iso_release_name
    fields.iso_disk_name.validator = validate_custom_iso_disk_name
    fields.iso_release_notes_url.validator = validate_custom_iso_release_notes_url
    fields.update_os_release.validator = validate_custom_update_os_release

    return fields


# ----------------------------------------------------------------------
# Initialize from Version
# ----------------------------------------------------------------------


def refresh_custom_using_version_number():
    """
    Initialize the following custom fields using the version number,
    and register the validators. All occurrences of the version number
    are replaced with a new version number based on the current date.
      - iso_version_number
      - iso_file_name
      - iso_directory (always set to the project directory)
      - iso_volume_id
      - iso_release_name
      - iso_disk_name
      - iso_release_notes_url
      - update_os_release (always initialize to True)
    """

    logger.log_label('Initialize the custom fields using the version number')

    fields = IsoFields('custom')

    # Update fields.
    # re.sub(search_string, replace_string, original_string)
    fields.iso_version_number.value = constructor.construct_custom_iso_version_number()
    if custom.iso_version_number.value:
        fields.iso_file_name.value = re.sub(custom.iso_version_number.value, fields.iso_version_number.value, custom.iso_file_name.value)
        fields.iso_directory.value = custom.iso_directory.value
        fields.iso_volume_id.value = re.sub(custom.iso_version_number.value, fields.iso_version_number.value, custom.iso_volume_id.value)[:32]
        fields.iso_release_name.value = re.sub(custom.iso_version_number.value, fields.iso_version_number.value, custom.iso_release_name.value)
        fields.iso_disk_name.value = re.sub(custom.iso_version_number.value, fields.iso_version_number.value, custom.iso_disk_name.value)
        fields.iso_release_notes_url.value = custom.iso_release_notes_url.value
        fields.update_os_release.value = True
    else:
        fields.iso_file_name.value = custom.iso_file_name.value
        fields.iso_directory.value = custom.iso_directory.value
        fields.iso_volume_id.value = custom.iso_volume_id.value[:32]
        fields.iso_release_name.value = custom.iso_release_name.value
        fields.iso_disk_name.value = custom.iso_disk_name.value
        fields.iso_release_notes_url.value = custom.iso_release_notes_url.value
        fields.update_os_release.value = True

    # Add validators.
    fields.iso_version_number.validator = validate_custom_iso_version_number
    fields.iso_file_name.validator = validate_custom_iso_file_name
    fields.iso_directory.validator = validate_custom_iso_directory
    fields.iso_volume_id.validator = validate_custom_iso_volume_id
    fields.iso_release_name.validator = validate_custom_iso_release_name
    fields.iso_disk_name.validator = validate_custom_iso_disk_name
    fields.iso_release_notes_url.validator = validate_custom_iso_release_notes_url
    fields.update_os_release.validator = validate_custom_update_os_release

    return fields


# ----------------------------------------------------------------------
# Initialize from Model
# ----------------------------------------------------------------------


def initialize_original_from_model():
    """
    Initialize the following original fields from the model, and
    register the validators.
      - iso_file_name
      - iso_directory
      - iso_volume_id
      - iso_release_name
      - iso_disk_name
      - iso_release_notes_url
    The original ISO does not have an iso_version_number, so the
    iso_version_number value and validator are not set. The
    iso_version_number value defaults to None, and the is_valid property
    is set to True to compensate for the unregistered validator.
    """

    logger.log_label('Initialize the original fields from the model')

    fields = IsoFields('original')

    # Update fields.
    fields.iso_file_name.value = model.original.iso_file_name
    fields.iso_directory.value = model.original.iso_directory
    fields.iso_volume_id.value = model.original.iso_volume_id
    fields.iso_release_name.value = model.original.iso_release_name
    fields.iso_disk_name.value = model.original.iso_disk_name
    fields.iso_release_notes_url.value = model.original.iso_release_notes_url

    # Add validators.
    # Do not add a validator for ISO version number, because the
    # original section does not display this field. However, explicitly
    # set iso_version_number.is_valid to True, because IsoFields.is_valid
    # checks if all fields are valid.
    fields.iso_version_number.is_valid = True
    fields.iso_file_name.validator = validate_original_iso_file_name
    fields.iso_directory.validator = validate_original_iso_directory
    fields.iso_volume_id.validator = validate_original_iso_volume_id
    fields.iso_release_name.validator = validate_original_iso_release_name
    fields.iso_disk_name.validator = validate_original_iso_disk_name
    fields.iso_release_notes_url.validator = validate_original_iso_release_notes_url
    # Do not add a validator for update OS release, because the original
    # section does not display this field. However, explicitly set
    # update_os_release.is_valid to True, because IsoFields.is_valid
    # checks if all fields are valid.
    fields.update_os_release.is_valid = True

    return fields


def initialize_custom_from_model():
    """
    Initialize the following custom fields from the model, and
    register the validators.
      - iso_version_number
      - iso_file_name
      - iso_directory
      - iso_volume_id
      - iso_release_name
      - iso_disk_name
      - iso_release_notes_url
      - update_os_release
    """

    logger.log_label('Initialize the custom fields from the model')

    fields = IsoFields('custom')

    # Update fields.
    fields.iso_version_number.value = model.custom.iso_version_number
    fields.iso_file_name.value = model.custom.iso_file_name
    fields.iso_directory.value = model.custom.iso_directory
    fields.iso_volume_id.value = model.custom.iso_volume_id
    fields.iso_release_name.value = model.custom.iso_release_name
    fields.iso_disk_name.value = model.custom.iso_disk_name
    fields.iso_release_notes_url.value = model.custom.iso_release_notes_url
    fields.update_os_release.value = model.options.update_os_release

    # Add validators.
    fields.iso_version_number.validator = validate_custom_iso_version_number
    fields.iso_file_name.validator = validate_custom_iso_file_name
    fields.iso_directory.validator = validate_custom_iso_directory
    fields.iso_volume_id.validator = validate_custom_iso_volume_id
    fields.iso_release_name.validator = validate_custom_iso_release_name
    fields.iso_disk_name.validator = validate_custom_iso_disk_name
    fields.iso_release_notes_url.validator = validate_custom_iso_release_notes_url
    fields.update_os_release.validator = validate_custom_update_os_release

    return fields


def initialize_status_from_model():
    """
    Initialize the following status fields from the model.
      - is_success_analyze
      - is_success_copy
      - is_success_extract
      - iso_template
      - iso_checksum = None
      - iso_checksum_file_name = None
    """

    logger.log_label('Initialize the status fields from the model')

    fields = Fields('status')

    fields.is_success_analyze = model.status.is_success_analyze
    fields.is_success_copy = model.status.is_success_copy
    fields.is_success_extract = model.status.is_success_extract
    fields.iso_template = model.status.iso_template
    # The saved ISO file size is never used.
    # The saved ISO checksum is never used.
    fields.iso_checksum = model.status.iso_checksum
    # The ISO checksum file_name is always constructed.
    fields.iso_checksum_file_name = model.status.iso_checksum_file_name

    return fields


def initialize_options_from_model():
    """
    Initialize the following options fields from the model.
      - (options.update_os_release)
      - has_minimal_install
      - boot_configurations
      - compression
    """

    logger.log_label('Initialize the options fields from the model')

    fields = Fields('options')

    # The field update_os_release is stored in "custom" IsoFields
    # instead of "options" Fields, so changes can be tracked in
    # custom_history to permit undo and redo. This value is initialized
    # from the model in the initialize_custom_from_model() function.
    # fields.update_os_release = model.options.update_os_release
    fields.has_minimal_install = model.options.has_minimal_install
    fields.boot_configurations = model.options.boot_configurations
    fields.compression = model.options.compression

    return fields


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


########################################################################
# Display Functions
########################################################################

# ----------------------------------------------------------------------
# Original Disk Section Display Functions
# ----------------------------------------------------------------------


def display_original_fields(fields):
    """
    Update each entry with the value, status, and message for each
    field. This function blocks all entry handlers to prevent automatic
    updates to the fields while the entries are updated; the handlers
    are unblocked after the entries have been updated. Remember to
    explicitly validate the page after invoking this function.
    """

    # Block handlers.
    displayer.idle_add(block_original_handlers)

    displayer.update_entry('project_page__original_iso_file_name_entry', fields.iso_file_name.value)
    displayer.update_status('project_page__original_iso_file_name', fields.iso_file_name.status)
    is_error = fields.iso_file_name.status == ERROR
    displayer.set_entry_error('project_page__original_iso_file_name_entry', is_error)
    displayer.update_label('project_page__original_iso_file_name_message', fields.iso_file_name.message, is_error)

    displayer.update_entry('project_page__original_iso_directory_entry', fields.iso_directory.value)
    displayer.update_status('project_page__original_iso_directory', fields.iso_directory.status)
    is_error = fields.iso_directory.status == ERROR
    displayer.set_entry_error('project_page__original_iso_directory_entry', is_error)
    displayer.update_label('project_page__original_iso_directory_message', fields.iso_directory.message, is_error)

    displayer.update_entry('project_page__original_iso_volume_id_entry', fields.iso_volume_id.value)
    displayer.update_status('project_page__original_iso_volume_id', fields.iso_volume_id.status)
    is_error = fields.iso_volume_id.status == ERROR
    displayer.set_entry_error('project_page__original_iso_volume_id_entry', is_error)
    displayer.update_label('project_page__original_iso_volume_id_message', fields.iso_volume_id.message, is_error)

    displayer.update_entry('project_page__original_iso_release_name_entry', fields.iso_release_name.value)
    displayer.update_status('project_page__original_iso_release_name', fields.iso_release_name.status)
    is_error = fields.iso_release_name.status == ERROR
    displayer.set_entry_error('project_page__original_iso_release_name_entry', is_error)
    displayer.update_label('project_page__original_iso_release_name_message', fields.iso_release_name.message, is_error)

    displayer.update_entry('project_page__original_iso_disk_name_entry', fields.iso_disk_name.value)
    displayer.update_status('project_page__original_iso_disk_name', fields.iso_disk_name.status)
    is_error = fields.iso_disk_name.status == ERROR
    displayer.set_entry_error('project_page__original_iso_disk_name_entry', is_error)
    displayer.update_label('project_page__original_iso_disk_name_message', fields.iso_disk_name.message, is_error)

    displayer.update_entry('project_page__original_iso_release_notes_url_entry', fields.iso_release_notes_url.value)
    displayer.update_status('project_page__original_iso_release_notes_url', fields.iso_release_notes_url.status)
    is_error = fields.iso_release_notes_url.status == ERROR
    displayer.set_entry_error('project_page__original_iso_release_notes_url_entry', is_error)
    displayer.update_label('project_page__original_iso_release_notes_url_message', fields.iso_release_notes_url.message, is_error)

    # Unblock handlers.
    displayer.idle_add(unblock_original_handlers)


def block_original_handlers():
    """
    This function must be invoked using GLib.idle_add().
    """

    entry = model.builder.get_object('project_page__original_iso_file_name_entry')
    entry.handler_block_by_func(on_changed__project_page__original_iso_file_name_entry)

    entry = model.builder.get_object('project_page__original_iso_directory_entry')
    entry.handler_block_by_func(on_changed__project_page__original_iso_directory_entry)

    entry = model.builder.get_object('project_page__original_iso_volume_id_entry')
    entry.handler_block_by_func(on_changed__project_page__original_iso_volume_id_entry)

    entry = model.builder.get_object('project_page__original_iso_release_name_entry')
    entry.handler_block_by_func(on_changed__project_page__original_iso_release_name_entry)

    entry = model.builder.get_object('project_page__original_iso_disk_name_entry')
    entry.handler_block_by_func(on_changed__project_page__original_iso_disk_name_entry)

    entry = model.builder.get_object('project_page__original_iso_release_notes_url_entry')
    entry.handler_block_by_func(on_changed__project_page__original_iso_release_notes_url_entry)


def unblock_original_handlers():
    """
    This function must be invoked using GLib.idle_add().
    """

    entry = model.builder.get_object('project_page__original_iso_file_name_entry')
    entry.handler_unblock_by_func(on_changed__project_page__original_iso_file_name_entry)

    entry = model.builder.get_object('project_page__original_iso_directory_entry')
    entry.handler_unblock_by_func(on_changed__project_page__original_iso_directory_entry)

    entry = model.builder.get_object('project_page__original_iso_volume_id_entry')
    entry.handler_unblock_by_func(on_changed__project_page__original_iso_volume_id_entry)

    entry = model.builder.get_object('project_page__original_iso_release_name_entry')
    entry.handler_unblock_by_func(on_changed__project_page__original_iso_release_name_entry)

    entry = model.builder.get_object('project_page__original_iso_disk_name_entry')
    entry.handler_unblock_by_func(on_changed__project_page__original_iso_disk_name_entry)

    entry = model.builder.get_object('project_page__original_iso_release_notes_url_entry')
    entry.handler_unblock_by_func(on_changed__project_page__original_iso_release_notes_url_entry)


# ----------------------------------------------------------------------
# Custom Disk Section Display Functions
# ----------------------------------------------------------------------


def display_custom_fields(fields):
    """
    Update each entry with the value, status, and message for each
    field. This function blocks all entry handlers to prevent automatic
    updates to the fields while the entries are updated; the handlers
    are unblocked after the entries have been updated. Remember to
    explicitly validate the page after invoking this function.
    """

    # Block handlers.
    displayer.idle_add(block_custom_handlers)

    displayer.update_entry('project_page__custom_iso_version_number_entry', fields.iso_version_number.value)
    displayer.update_status('project_page__custom_iso_version_number', fields.iso_version_number.status)
    is_error = fields.iso_version_number.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_version_number_entry', is_error)
    displayer.update_label('project_page__custom_iso_version_number_message', fields.iso_version_number.message, is_error)

    displayer.update_entry('project_page__custom_iso_file_name_entry', fields.iso_file_name.value)
    displayer.update_status('project_page__custom_iso_file_name', fields.iso_file_name.status)
    is_error = fields.iso_file_name.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_file_name_entry', is_error)
    displayer.update_label('project_page__custom_iso_file_name_message', fields.iso_file_name.message, is_error)

    displayer.update_entry('project_page__custom_iso_directory_entry', fields.iso_directory.value)
    displayer.update_status('project_page__custom_iso_directory', fields.iso_directory.status)
    is_error = fields.iso_directory.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_directory_entry', is_error)
    displayer.update_label('project_page__custom_iso_directory_message', fields.iso_directory.message, is_error)

    displayer.update_entry('project_page__custom_iso_volume_id_entry', fields.iso_volume_id.value)
    displayer.update_status('project_page__custom_iso_volume_id', fields.iso_volume_id.status)
    is_error = fields.iso_volume_id.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_volume_id_entry', is_error)
    displayer.update_label('project_page__custom_iso_volume_id_message', fields.iso_volume_id.message, is_error)

    displayer.update_entry('project_page__custom_iso_release_name_entry', fields.iso_release_name.value)
    displayer.update_status('project_page__custom_iso_release_name', fields.iso_release_name.status)
    is_error = fields.iso_release_name.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_release_name_entry', is_error)
    displayer.update_label('project_page__custom_iso_release_name_message', fields.iso_release_name.message, is_error)

    displayer.update_entry('project_page__custom_iso_disk_name_entry', fields.iso_disk_name.value)
    displayer.update_status('project_page__custom_iso_disk_name', fields.iso_disk_name.status)
    is_error = fields.iso_disk_name.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_disk_name_entry', is_error)
    displayer.update_label('project_page__custom_iso_disk_name_message', fields.iso_disk_name.message, is_error)

    displayer.update_entry('project_page__custom_iso_release_notes_url_entry', fields.iso_release_notes_url.value)
    displayer.update_status('project_page__custom_iso_release_notes_url', fields.iso_release_notes_url.status)
    is_error = fields.iso_release_notes_url.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_release_notes_url_entry', is_error)
    displayer.update_label('project_page__custom_iso_release_notes_url_message', fields.iso_release_notes_url.message, is_error)

    # The field update_os_release is stored in "custom" IsoFields
    # instead of "options" Fields, so changes can be tracked in
    # custom_history to permit undo and redo.
    displayer.activate_check_button('project_page__custom_update_os_release_check_button', fields.update_os_release.value)
    displayer.update_status('project_page__custom_update_os_release', fields.update_os_release.status)

    # Unblock handlers.
    displayer.idle_add(unblock_custom_handlers)


def block_custom_handlers():
    """
    This function must be invoked using GLib.idle_add().
    """

    entry = model.builder.get_object('project_page__custom_iso_version_number_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_version_number_entry)

    entry = model.builder.get_object('project_page__custom_iso_file_name_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_file_name_entry)

    entry = model.builder.get_object('project_page__custom_iso_directory_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_directory_entry)

    entry = model.builder.get_object('project_page__custom_iso_volume_id_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_volume_id_entry)

    entry = model.builder.get_object('project_page__custom_iso_release_name_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_release_name_entry)

    entry = model.builder.get_object('project_page__custom_iso_disk_name_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_disk_name_entry)

    entry = model.builder.get_object('project_page__custom_iso_release_notes_url_entry')
    entry.handler_block_by_func(on_changed__project_page__custom_iso_release_notes_url_entry)

    check_button = model.builder.get_object('project_page__custom_update_os_release_check_button')
    check_button.handler_block_by_func(on_toggled__project_page__custom_update_os_release_check_button)


def unblock_custom_handlers():
    """
    This function must be invoked using GLib.idle_add().
    """

    entry = model.builder.get_object('project_page__custom_iso_version_number_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_version_number_entry)

    entry = model.builder.get_object('project_page__custom_iso_file_name_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_file_name_entry)

    entry = model.builder.get_object('project_page__custom_iso_directory_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_directory_entry)

    entry = model.builder.get_object('project_page__custom_iso_volume_id_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_volume_id_entry)

    entry = model.builder.get_object('project_page__custom_iso_release_name_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_release_name_entry)

    entry = model.builder.get_object('project_page__custom_iso_disk_name_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_disk_name_entry)

    entry = model.builder.get_object('project_page__custom_iso_release_notes_url_entry')
    entry.handler_unblock_by_func(on_changed__project_page__custom_iso_release_notes_url_entry)

    check_button = model.builder.get_object('project_page__custom_update_os_release_check_button')
    check_button.handler_unblock_by_func(on_toggled__project_page__custom_update_os_release_check_button)


########################################################################
# Handler Functions
########################################################################

# ----------------------------------------------------------------------
# Navigation Handler Functions
# ----------------------------------------------------------------------


def on_clicked__project_page__test_header_bar_button(widget):

    logger.log_title('Clicked project page test button')

    handle_navigation('test')


def on_clicked__project_page__delete_header_bar_button(widget):

    logger.log_value('Clicked', 'Delete')

    handle_navigation('delete')


# ----------------------------------------------------------------------
# Original Disk Section Handler Functions
# ----------------------------------------------------------------------


def on_clicked__project_page__original_iso_file_name_open_button(widget):

    logger.log_label('Clicked project page original ISO file name open button')

    if original.iso_directory.value:
        # Use the project's the ISO directory and ISO file name.
        original_iso_file_path = os.path.join(original.iso_directory.value, original.iso_file_name.value)
    else:
        # Use the previous ISO file path.
        original_iso_file_path = model.application.iso_file_path

    iso_image_chooser.open(selected_original_iso_file_path, original_iso_file_path)


def on_changed__project_page__original_iso_file_name_entry(widget):

    logger.log_label('Original ISO file name changed')

    text = widget.get_text()
    if text:
        if text[-8:] == '.iso.iso':
            position = widget.get_property('cursor-position')
            widget.set_text(text[:-4])
            widget.set_position(position)
        elif text[-4:] != '.iso':
            position = widget.get_property('cursor-position')
            widget.set_text(f'{text}.iso')
            widget.set_position(position)
    original.iso_file_name.value = widget.get_text()

    displayer.update_status('project_page__original_iso_file_name', original.iso_file_name.status)
    is_error = original.iso_file_name.status == ERROR
    displayer.set_entry_error('project_page__original_iso_file_name_entry', is_error)
    displayer.update_label('project_page__original_iso_file_name_message', original.iso_file_name.message, is_error)

    validate_page()


def on_changed__project_page__original_iso_directory_entry(widget):

    logger.log_label('Original ISO directory changed')

    original.iso_directory.value = widget.get_text()

    displayer.update_status('project_page__original_iso_directory', original.iso_directory.status)
    is_error = original.iso_directory.status == ERROR
    displayer.set_entry_error('project_page__original_iso_directory_entry', is_error)
    displayer.update_label('project_page__original_iso_directory_message', original.iso_directory.message, is_error)

    validate_page()


def on_changed__project_page__original_iso_volume_id_entry(widget):

    logger.log_label('Original ISO volume id changed')

    original.iso_volume_id.value = widget.get_text()

    displayer.update_status('project_page__original_iso_volume_id', original.iso_volume_id.status)
    is_error = original.iso_volume_id.status == ERROR
    displayer.set_entry_error('project_page__original_iso_volume_id_entry', is_error)
    displayer.update_label('project_page__original_iso_volume_id_message', original.iso_volume_id.message, is_error)

    validate_page()


def on_changed__project_page__original_iso_release_name_entry(widget):

    logger.log_label('Original ISO release name changed')

    original.iso_release_name.value = widget.get_text()

    displayer.update_status('project_page__original_iso_release_name', original.iso_release_name.status)
    is_error = original.iso_release_name.status == ERROR
    displayer.set_entry_error('project_page__original_iso_release_name_entry', is_error)
    displayer.update_label('project_page__original_iso_release_name_message', original.iso_release_name.message, is_error)

    validate_page()


def on_changed__project_page__original_iso_disk_name_entry(widget):

    logger.log_label('Original ISO disk name changed')

    original.iso_disk_name.value = widget.get_text()

    displayer.update_status('project_page__original_iso_disk_name', original.iso_disk_name.status)
    is_error = original.iso_disk_name.status == ERROR
    displayer.set_entry_error('project_page__original_iso_disk_name_entry', is_error)
    displayer.update_label('project_page__original_iso_disk_name_message', original.iso_disk_name.message, is_error)

    validate_page()


def on_changed__project_page__original_iso_release_notes_url_entry(widget):

    logger.log_label('Original ISO release notes URL changed')

    original.iso_release_notes_url.value = widget.get_text()

    displayer.update_status('project_page__original_iso_release_notes_url', original.iso_release_notes_url.status)
    is_error = original.iso_release_notes_url.status == ERROR
    displayer.set_entry_error('project_page__original_iso_release_notes_url_entry', is_error)
    displayer.update_label('project_page__original_iso_release_notes_url_message', original.iso_release_notes_url.message, is_error)

    validate_page()


# ----------------------------------------------------------------------
# Custom Disk Section Handler Functions
# ----------------------------------------------------------------------


def on_clicked__project_page__undo_header_bar_button(widget):

    logger.log_label('Clicked project page undo header bar button')

    global custom

    if custom != custom_history.current():
        if custom.is_valid:
            custom_history.insert(custom)
            custom = custom_history.previous()
        else:
            custom_history.clear(custom)
            custom = custom_history.current()
    else:
        custom = custom_history.previous()
    display_custom_fields(custom)
    validate_page()


def on_clicked__project_page__redo_header_bar_button(widget):

    logger.log_label('Clicked project page redo header bar button')

    global custom

    custom = custom_history.next()
    display_custom_fields(custom)
    validate_page()


def on_clicked__project_page__custom_iso_version_number_refresh_button(widget):

    logger.log_label('Clicked project page custom ISO version number refresh button')

    global custom

    if custom.is_valid and custom != custom_history.current():
        custom_history.insert(custom)

    custom = refresh_custom_using_version_number()
    display_custom_fields(custom)
    validate_page()


def on_clicked__project_page__custom_iso_directory_open_button(widget):

    logger.log_label('Clicked project page custom ISO directory open button')

    directory_chooser.open(selected_custom_iso_directory, custom.iso_directory.value)


def on_changed__project_page__custom_iso_version_number_entry(widget):

    logger.log_label('Custom ISO version number changed')

    custom.iso_version_number.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_version_number', custom.iso_version_number.status)
    is_error = custom.iso_version_number.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_version_number_entry', is_error)
    displayer.update_label('project_page__custom_iso_version_number_message', custom.iso_version_number.message, is_error)

    # Propagate.

    iso_file_name = constructor.construct_custom_iso_file_name(original.iso_file_name.value, custom.iso_version_number.value)
    # custom.iso_file_name.value will be updated automatically when the
    # on_changed handler is invoked.
    displayer.update_entry('project_page__custom_iso_file_name_entry', iso_file_name)

    iso_volume_id = constructor.construct_custom_iso_volume_id(original.iso_volume_id.value, custom.iso_version_number.value)
    # custom.iso_volume_id.value will be updated automatically when the
    # on_changed handler is invoked.
    displayer.update_entry('project_page__custom_iso_volume_id_entry', iso_volume_id)

    validate_page()


def on_changed__project_page__custom_iso_file_name_entry(widget):

    logger.log_label('Custom ISO file name changed')

    text = widget.get_text()
    if text:
        if text[-8:] == '.iso.iso':
            position = widget.get_property('cursor-position')
            widget.set_text(text[:-4])
            widget.set_position(position)
        elif text[-4:] != '.iso':
            position = widget.get_property('cursor-position')
            widget.set_text(f'{text}.iso')
            widget.set_position(position)
    custom.iso_file_name.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_file_name', custom.iso_file_name.status)
    is_error = custom.iso_file_name.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_file_name_entry', is_error)
    displayer.update_label('project_page__custom_iso_file_name_message', custom.iso_file_name.message, is_error)

    validate_page()


def on_changed__project_page__custom_iso_directory_entry(widget):

    logger.log_label('Custom ISO directory changed')

    custom.iso_directory.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_directory', custom.iso_directory.status)
    is_error = custom.iso_directory.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_directory_entry', is_error)
    displayer.update_label('project_page__custom_iso_directory_message', custom.iso_directory.message, is_error)

    validate_page()


def on_changed__project_page__custom_iso_volume_id_entry(widget):

    logger.log_label('Custom ISO volume id changed')

    custom.iso_volume_id.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_volume_id', custom.iso_volume_id.status)
    is_error = custom.iso_volume_id.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_volume_id_entry', is_error)
    displayer.update_label('project_page__custom_iso_volume_id_message', custom.iso_volume_id.message, is_error)

    # Propagate.

    # custom.iso_disk_name.value will be updated automatically when the
    # on_changed handler is invoked.
    iso_disk_name = constructor.construct_custom_iso_disk_name(custom.iso_volume_id.value, custom.iso_release_name.value)
    displayer.update_entry('project_page__custom_iso_disk_name_entry', iso_disk_name)

    # custom.update_os_release.value will be updated
    # automatically when the on_toggled handler is invoked.
    if bool(custom.iso_volume_id.value):
        # Toggle the check box to be selected if ISO volume id is valid.
        if bool(custom.update_os_release.value): displayer.activate_check_button('project_page__custom_update_os_release_check_button', False)
        displayer.activate_check_button('project_page__custom_update_os_release_check_button', True)
    else:
        # Toggle the check box.
        displayer.activate_check_button('project_page__custom_update_os_release_check_button', not bool(custom.update_os_release.value))
        displayer.activate_check_button('project_page__custom_update_os_release_check_button', bool(custom.update_os_release.value))

    validate_page()


def on_changed__project_page__custom_iso_release_name_entry(widget):

    logger.log_label('Custom ISO release name changed')

    custom.iso_release_name.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_release_name', custom.iso_release_name.status)
    is_error = custom.iso_release_name.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_release_name_entry', is_error)
    displayer.update_label('project_page__custom_iso_release_name_message', custom.iso_release_name.message, is_error)

    # Propagate.

    # custom.iso_disk_name.value will be updated automatically when the
    # on_changed handler is invoked.
    iso_disk_name = constructor.construct_custom_iso_disk_name(custom.iso_volume_id.value, custom.iso_release_name.value)
    displayer.update_entry('project_page__custom_iso_disk_name_entry', iso_disk_name)

    validate_page()


def on_changed__project_page__custom_iso_disk_name_entry(widget):

    logger.log_label('Custom ISO disk name changed')

    custom.iso_disk_name.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_disk_name', custom.iso_disk_name.status)
    is_error = custom.iso_disk_name.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_disk_name_entry', is_error)
    displayer.update_label('project_page__custom_iso_disk_name_message', custom.iso_disk_name.message, is_error)

    validate_page()


def on_changed__project_page__custom_iso_release_notes_url_entry(widget):

    logger.log_label('Custom ISO release notes URL changed')

    custom.iso_release_notes_url.value = widget.get_text()

    displayer.update_status('project_page__custom_iso_release_notes_url', custom.iso_release_notes_url.status)
    is_error = custom.iso_release_notes_url.status == ERROR
    displayer.set_entry_error('project_page__custom_iso_release_notes_url_entry', is_error)
    displayer.update_label('project_page__custom_iso_release_notes_url_message', custom.iso_release_notes_url.message, is_error)

    validate_page()


def on_toggled__project_page__custom_update_os_release_check_button(widget):

    logger.log_label('Custom update OS release changed')

    # The field update_os_release is stored in "custom" IsoFields
    # instead of "options" Fields, so changes can be tracked in
    # custom_history to permit undo and redo.
    custom.update_os_release.value = widget.get_active()
    displayer.update_status('project_page__custom_update_os_release', custom.update_os_release.status)
    # is_error = custom.update_os_release.status == ERROR
    # displayer.set_check_button_error('project_page__custom_update_os_release', is_error)
    # displayer.update_label('project_page__custom_update_os_release', custom.update_os_release.message, is_error)

    validate_page()


########################################################################
# Support Functions
########################################################################

# N/A

########################################################################
# Validation Functions
########################################################################

# ----------------------------------------------------------------------
# Page Validation Functions
# ----------------------------------------------------------------------


def validate_page():
    """
    Show or hide buttons and set the original and custom sections
    sensitive or insensitive. Validate page relies on the current values
    of original fields and custom fields, and does not depend on what is
    currently displayed in the user interface.
    """

    is_page_valid = original.is_valid and custom.is_valid

    logger.log_value('Is page valid?', is_page_valid)

    # Original section.

    set_sensitive_original_section(original.is_valid)

    # Custom section.

    set_sensitive_custom_section(original.is_valid)
    validate_custom_iso_undo_button()
    validate_custom_iso_redo_button()
    validate_custom_iso_refresh_button()

    # Navigation buttons.

    # Navigation buttons are also set in the setup() function.
    if status.iso_template and       \
       status.is_success_analyze and \
       status.is_success_copy and    \
       status.is_success_extract:
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next-terminal',
            next_button_style='suggested-action',
            is_next_sensitive=is_page_valid,
            is_next_visible=True)
    else:
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=is_page_valid,
            is_next_visible=True)


# ----------------------------------------------------------------------
# Original Disk Section Validation Functions
# ----------------------------------------------------------------------


def set_sensitive_original_section(is_valid):

    displayer.set_sensitive('project_page__original_iso_file_name_entry', is_valid)
    # displayer.set_sensitive('project_page__original_iso_file_name_open_button', is_valid)
    displayer.set_sensitive('project_page__original_iso_directory_entry', is_valid)
    displayer.set_sensitive('project_page__original_iso_volume_id_entry', is_valid)
    displayer.set_sensitive('project_page__original_iso_release_name_entry', is_valid)
    displayer.set_sensitive('project_page__original_iso_disk_name_entry', is_valid)
    displayer.set_sensitive('project_page__original_iso_release_notes_url_entry', is_valid)


# ----------------------------------------------------------------------
# Custom Disk Section Validation Functions
# ----------------------------------------------------------------------


def set_editable_custom_section(is_valid):
    """
    This function is not used.
    Setting the entries not editable allows the text to be selected.
    """

    displayer.set_entry_editable('project_page__custom_iso_version_number_entry', is_valid)
    # displayer.set_sensitive('project_page__custom_iso_version_number_refresh_button', is_valid)
    displayer.set_entry_editable('project_page__custom_iso_file_name_entry', is_valid)
    # displayer.set_entry_editable('project_page__custom_iso_directory_entry', is_valid)
    displayer.set_sensitive('project_page__custom_iso_directory_open_button', is_valid)
    displayer.set_entry_editable('project_page__custom_iso_volume_id_entry', is_valid)
    displayer.set_entry_editable('project_page__custom_iso_release_name_entry', is_valid)
    displayer.set_entry_editable('project_page__custom_iso_disk_name_entry', is_valid)
    displayer.set_entry_editable('project_page__custom_iso_release_notes_url_entry', is_valid)

    # Check button widgets can not be set editable.
    # displayer.set_check_button_editable('project_page__custom_update_os_release_check_button', is_valid)


def set_sensitive_custom_section(is_valid):
    """
    Setting the entries insensitive makes the text unselectable.
    """

    displayer.set_sensitive('project_page__custom_iso_version_number_entry', is_valid)
    # displayer.set_sensitive('project_page__custom_iso_version_number_refresh_button', is_valid)
    displayer.set_sensitive('project_page__custom_iso_file_name_entry', is_valid)
    displayer.set_sensitive('project_page__custom_iso_directory_entry', is_valid)
    displayer.set_sensitive('project_page__custom_iso_directory_open_button', is_valid)
    displayer.set_sensitive('project_page__custom_iso_volume_id_entry', is_valid)
    displayer.set_sensitive('project_page__custom_iso_release_name_entry', is_valid)
    displayer.set_sensitive('project_page__custom_iso_disk_name_entry', is_valid)
    displayer.set_sensitive('project_page__custom_iso_release_notes_url_entry', is_valid)

    displayer.set_sensitive('project_page__custom_update_os_release_check_button', is_valid)
    displayer.set_sensitive('project_page__custom_update_os_release_instructions', is_valid)


def validate_custom_iso_undo_button():

    if custom_history.has_undo():

        # If there is at least one iso-fields to the "left" of the
        # currently selected iso-fields in the history, then enable the
        # undo button. This simple check is preformed first because
        # it is less expensive than comparing the currently displayed
        # iso-fields with currently selected iso-fields in the history.

        displayer.set_sensitive('project_page__undo_header_bar_button', True)

    elif custom_history.has_history() and custom != custom_history.current():

        # When history is empty, custom_history.current() is None, and
        # the comparison, custom != custom_history.current(), will be
        # True causing the undo button to be enabled. To avoid this,
        # check if history is not empty before performing the comparison.

        displayer.set_sensitive('project_page__undo_header_bar_button', True)

    else:

        displayer.set_sensitive('project_page__undo_header_bar_button', False)


def validate_custom_iso_redo_button():

    if custom_history.has_redo() and custom == custom_history.current():
        displayer.set_sensitive('project_page__redo_header_bar_button', True)
    else:
        displayer.set_sensitive('project_page__redo_header_bar_button', False)


def validate_custom_iso_refresh_button():

    if custom.is_valid:
        iso_version_number = constructor.construct_custom_iso_version_number()
        if custom.iso_version_number.value != iso_version_number:
            displayer.set_sensitive('project_page__custom_iso_version_number_refresh_button', True)
        else:
            displayer.set_sensitive('project_page__custom_iso_version_number_refresh_button', False)
    else:
        displayer.set_sensitive('project_page__custom_iso_version_number_refresh_button', False)


########################################################################
# Field Validation Functions
########################################################################

# ----------------------------------------------------------------------
# Original Field Validation Functions
# ----------------------------------------------------------------------

# To access the validator's field use:
#   • fields.{field_name}.value.
# To access other fields use:
#   • original.{other_field_name}.value
#   • custom.{other_field_name}.value
# Every validator must first check:
#   • if not fields.iso_file_name.is_valid


def validate_original_iso_version_number(fields):
    """
    This function is not used.
    """

    is_valid = True
    status = OK
    message = None
    return is_valid, status, message


def validate_original_iso_file_name(fields):
    """
    The fields.iso_file_name.value can be used to bypass validation of
    the original_iso_file_name field. After the is_valid value
    is set to False, other validators can also bypass validation by
    referencing fields.iso_file_name.is_valid.
    """

    if not fields.iso_file_name.value:
        is_valid = False
        message = None
        status = BLANK
    else:
        original_iso_file_path = os.path.join(fields.iso_directory.value, fields.iso_file_name.value)
        if not original_iso_file_path:
            is_valid = False
            message = 'Select a disk image.'
            status = ERROR
        elif iso_utilities.is_mounted(model.project.iso_mount_point, original_iso_file_path):
            # The original disk is available.
            is_valid = True
            message = None
            status = OK
        elif not model.status.is_success_analyze:
            # The original disk is required; display an error because it
            # is not available.
            is_valid = False
            # message = '<span foreground="red">Error. The original disk image is required to copy important files, but it is not available.</span>'
            message = 'Error. The original disk image is required to copy important files and extract the Linux file system, but it is not available.'
            status = ERROR
        elif not model.status.is_success_copy and not model.status.is_success_extract:
            # The original disk is required; display an error because it
            # is not available.
            is_valid = False
            # message = '<span foreground="red">Error. The original disk image is required to copy important files and extract the Linux file system, but it is not available.</span>'
            message = 'Error. The original disk image is required to copy important files and extract the Linux file system, but it is not available.'
            status = ERROR
        elif not model.status.is_success_copy:
            # The original disk is required; display an error because it
            # is not available.
            is_valid = False
            # message = '<span foreground="red">Error. The original disk image is required to copy important files, but it is not available.</span>'
            message = 'Error. The original disk image is required to copy important files, but it is not available.'
            status = ERROR
        elif not model.status.iso_template:
            # The original disk is required; display an error because it
            # is not available.
            is_valid = False
            # message = '<span foreground="red">Error. The original disk image is required to copy important files, but it is not available.</span>'
            message = 'Error. The original disk image is required to copy important files, but it is not available.'
            status = ERROR
        elif not model.status.is_success_extract:
            # The original disk is required; display an error because it
            # is not available.
            is_valid = False
            # message = '<span foreground="red">Error. The original disk image is required to extract the Linux file system, but it is not available.</span>'
            message = 'Error. The original disk image is required to extract the Linux file system, but it is not available.'
            status = ERROR
        else:
            # The original disk is optional; display a warning because it
            # is not available. Set True because this is an optional value.
            is_valid = True
            message = 'Warning. The original disk image is not available.'
            status = OPTIONAL
    return is_valid, status, message


def validate_original_iso_directory(fields):

    if not fields.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_directory.value)
        status = OK if is_valid else ERROR
        if is_valid:
            message = None
        else:
            # message = '<span foreground="red">Error. The original disk directory is required.</span>'
            message = 'Error. The original disk directory is required.'
    return is_valid, status, message


def validate_original_iso_volume_id(fields):

    if not fields.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_volume_id.value)
        status = OK if is_valid else ERROR
        if is_valid:
            # message = f'{32-len(fields.iso_volume_id.value)} of 32 characters left.'
            message = None
        else:
            # message = '<span foreground="red">Error. The original volume ID is required.</span>'
            message = 'Error. The original volume ID is required.'
    return is_valid, status, message


def validate_original_iso_release_name(fields):

    if not fields.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_release_name.value)
        status = OK if is_valid else OPTIONAL
        if is_valid:
            message = None
        else:
            message = 'The original release is not available.'
        # Set True because this is an optional field.
        is_valid = True
    return is_valid, status, message


def validate_original_iso_disk_name(fields):

    if not fields.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_disk_name.value)
        status = OK if is_valid else OPTIONAL
        if is_valid:
            message = None
        else:
            message = 'The original disk name is not available.'
        # Set True because this is an optional field.
        is_valid = True
    return is_valid, status, message


def validate_original_iso_release_notes_url(fields):

    if not fields.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_release_notes_url.value)
        status = OK if is_valid else OPTIONAL
        if is_valid:
            message = None
        else:
            message = 'The original release URL is not available.'
        # Set True because this is an optional field.
        is_valid = True
    return is_valid, status, message


def validate_original_update_os_release(fields):
    """
    This function is not used.
    """

    is_valid = True
    status = OK
    message = None
    return is_valid, status, message


# ----------------------------------------------------------------------
# Custom Field Validation Functions
# ----------------------------------------------------------------------

# To access the validator's field use:
#   • fields.{field_name}.value.
# To access other fields use:
#   • original.{other_field_name}.value
#   • custom.{other_field_name}.value
# Every validator must first check:
#   • if not original or not original.iso_file_name.is_valid


def validate_custom_iso_version_number(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_version_number.value)
        status = OK if is_valid else OPTIONAL
        if is_valid:
            message = None
        else:
            message = 'Version is optional.'
        # Set True because this is an optional field.
        is_valid = True
    return is_valid, status, message


def validate_custom_iso_file_name(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_file_name.value)
        status = OK if is_valid else ERROR
        if is_valid:
            message = None
        else:
            # message = '<span foreground="red">Error. Filename is required.</span>'
            message = 'Error. Filename is required.'
    return is_valid, status, message


def validate_custom_iso_directory(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    elif bool(fields.iso_directory.value):
        if os.path.isdir(fields.iso_directory.value):
            if file_utilities.directory_is_writable(fields.iso_directory.value):
                is_valid = True
                message = None
                status = OK
            else:
                is_valid = False
                # message = '<span foreground="red">Error. Cannot access directory.</span>'
                message = 'Error. Cannot access directory.'
                status = ERROR
        else:
            is_valid = False
            # message = '<span foreground="red">Error. Directory not found.</span>'
            message = 'Error. Directory not found.'
            status = ERROR
    else:
        is_valid = False
        status = ERROR
        # message = '<span foreground="red">Error. Directory is required.</span>'
        message = 'Error. Directory is required.'
    return is_valid, status, message


def validate_custom_iso_volume_id(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_volume_id.value)
        status = OK if is_valid else ERROR
        if is_valid:
            message = f'{32-len(fields.iso_volume_id.value)} of 32 characters left.'
        else:
            # message = '<span foreground="red">Error. Volume ID is required.</span>'
            message = 'Error. Volume ID is required.'
    return is_valid, status, message


def validate_custom_iso_release_name(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_release_name.value)
        status = OK if is_valid else OPTIONAL
        if is_valid:
            message = None
        else:
            message = 'Release is optional.'
        # Set True because this is an optional field.
        is_valid = True
    return is_valid, status, message


def validate_custom_iso_disk_name(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        is_valid = bool(fields.iso_disk_name.value)
        status = OK if is_valid else ERROR
        if is_valid:
            message = None
        else:
            # message = '<span foreground="red">Error. Disk name is required.</span>'
            message = 'Error. Disk name is required.'
    return is_valid, status, message


def validate_custom_iso_release_notes_url(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    elif bool(fields.iso_release_notes_url.value):
        is_valid = is_url(fields.iso_release_notes_url.value)
        if is_valid:
            message = None
            status = OK
        else:
            # message = '<span foreground="red">Error. Invalid URL format.</span>'
            message = 'Error. Invalid URL format.'
            status = ERROR
    else:
        # Set True because this is an optional field.
        is_valid = True
        message = 'Release URL is optional.'
        status = OPTIONAL
    return is_valid, status, message


def validate_custom_update_os_release(fields):

    if not original or not original.iso_file_name.is_valid:
        is_valid = False
        message = None
        status = BLANK
    else:
        if fields.iso_volume_id.is_valid:
            if bool(fields.update_os_release.value):
                is_valid = True
                message = None
                status = OK
            else:
                is_valid = True
                message = None
                status = OPTIONAL
        else:
            if bool(fields.update_os_release.value):
                is_valid = False
                message = None
                status = ERROR
            else:
                is_valid = True
                message = None
                status = OPTIONAL
    return is_valid, status, message


def is_url(url):
    try:
        result = urllib.parse.urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


########################################################################
# Test Functions
########################################################################


def validate_test_header_bar_button():

    # Do not show the Test button if the dummy Qemu package is
    # installed. The version of qemu-system-x86 should be >=1:4.2; the
    # dummy package version is 0.0.
    if constructor.get_package_version('qemu-system-x86') == '0.0':
        logger.log_value('Is the dummy Qemu package installed', 'Yes')
        displayer.set_sensitive('project_page__test_header_bar_button', False)
        displayer.set_visible('project_page__test_header_bar_button', False)
        logger.log_value('Enable testing?', 'No')
        return

    # Do not enable the Test button if the generated ISO file does not
    # exist.
    custom_iso_file_path = os.path.join(model.generated.iso_directory, model.generated.iso_file_name)
    if not os.path.exists(custom_iso_file_path):
        logger.log_value('Does the custom ISO file exist?', 'No')
        displayer.set_sensitive('project_page__test_header_bar_button', False)
        displayer.set_visible('project_page__test_header_bar_button', True)
        logger.log_value('Enable testing?', 'No')
        return

    # Do not enable the Test button if there is less than 1.5 GiB
    # available memory.
    is_adequate = emulator.check_available_memory()
    if not is_adequate:
        displayer.set_sensitive('project_page__test_header_bar_button', False)
        displayer.set_visible('project_page__test_header_bar_button', True)
        logger.log_value('System has adequate available memory to enable testing?', 'No')
        logger.log_value('Enable testing?', 'No')
        return

    # Enable and show the Test button.
    displayer.set_sensitive('project_page__test_header_bar_button', True)
    displayer.set_visible('project_page__test_header_bar_button', True)
    logger.log_value('The generated ISO file path is', custom_iso_file_path)
    logger.log_value('System has adequate available memory to enable testing?', 'Yes')
    logger.log_value('Enable testing?', 'Yes')


########################################################################
# Save Functions
########################################################################


def save_iso_release_notes_url():

    logger.log_label('Update the custom ISO release notes url')

    logger.log_value('The custom ISO release notes URL is', model.custom.iso_release_notes_url)

    file_path = os.path.join(model.project.custom_disk_directory, '.disk', 'release_notes_url')
    # Create the full directory path "custom-disk/.disk" because these
    # directories may not exist.
    file_utilities.write_line(model.custom.iso_release_notes_url, file_path, True, False)
