#!/usr/bin/python3

########################################################################
#                                                                      #
# start_page.py                                                        #
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

from packaging import version

from cubic.choosers import directory_chooser
from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import CUBIC_VERSION_2024
from cubic.constants import OK, ERROR, EXCLUDED_FILE_SYSTEM_TYPES, FILE_SYSTEM_TYPES
from cubic.utilities import configuration
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'start_page'

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

    if action == 'open':

        # Initialize button labels, actions, and styles.
        display_version = constructor.get_display_version(model.application.cubic_version)
        about_dialog = model.builder.get_object('about_dialog')
        about_dialog.set_version(f'<small>{display_version}</small>')
        message = f'Version {display_version}'
        displayer.update_label('start_page__version_label', message)
        message = 'Select a project directory.'
        displayer.update_label('start_page__project_directory_message', message, False)

        # Create the application configuration.
        file_path = constructor.construct_application_configuration_file_path(model.application.user_home)
        model.application.configuration = configuration.Application(file_path)

        # Load the model from the application configuration.
        # • model.application.cubic_version
        #   - The previous Cubic version is not loaded into the model;
        #     it is set to the current Cubic version in cubic_wizard
        # • model.application.visited_sites
        #   - The previous visited sites
        # • model.application.projects
        #   - The previous projects
        # • model.application.iso_directory
        #   - The previous ISO directory
        model.application.configuration.load()

        # Initialize the list of previous projects.
        displayer.remove_all_combo_box_text('start_page__project_directory_combo_box_text')
        for directory in model.application.projects:
            displayer.append_combo_box_text('start_page__project_directory_combo_box_text', directory)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        return

    elif action == 'back':

        # Do not change button labels, actions, and styles.
        # The validate_page() function in the enter action will assign
        # the correct button labels, actions, and styles.

        # Initialize the list of previous projects.
        displayer.remove_all_combo_box_text('start_page__project_directory_combo_box_text')
        for directory in model.application.projects:
            displayer.append_combo_box_text('start_page__project_directory_combo_box_text', directory)

        displayer.reset_buttons(
            back_button_label=None,
            back_action=None,
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=None,
            next_button_label=None,
            next_action=None,
            next_button_style=None,
            is_next_sensitive=None,
            is_next_visible=None)

        return

    elif action == 'cancel':

        # Do not change button labels, actions, and styles.

        displayer.reset_buttons(
            back_button_label=None,
            back_action=None,
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=None,
            next_button_label=None,
            next_action=None,
            next_button_style=None,
            is_next_sensitive=None,
            is_next_visible=None)

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

    if action == 'open':

        if model.arguments.directory:
            selected_project_directory(model.arguments.directory)

        return

    elif action == 'back':

        validate_page()

        return

    elif action == 'cancel':

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

    if action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # The following fields must be set before leaving this page:
        #
        # 1. model.project.cubic_version
        #    - Set to the running Cubic version in cubic_wizard
        # 2. model.project.create_date
        #    - Loaded from an existing configuration, or set to current
        #      date in the initialize_model() function
        # 3. model.project.directory
        #    - Set by the selected_project_directory() function
        # 4. model.project.configuration
        #    - Set in the validate_page() function
        # 5. model.project.iso_mount_point
        #    - Set in the initialize_model() function
        # 6. model.project.custom_root_directory
        #    - Set in the initialize_model() function
        # 7. model.project.custom_disk_directory
        #    - Set in the initialize_model() function

        # Prepend the selected project directory to the list of previous
        # project directories, ensuring there are no duplicates.
        # Truncate the list to five items.
        model.application.projects = list(dict.fromkeys([model.project.directory] + model.application.projects))[0:5]

        return

    elif action == 'alert':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # The following fields must be set before leaving this page:
        #
        # 1. model.project.cubic_version
        #    - Set to the running Cubic version in cubic_wizard
        # 2. model.project.create_date
        #    - Loaded from an existing configuration, or set to current
        #      date in the initialize_model() function
        # 3. model.project.directory
        #    - Set by the selected_project_directory() function
        # 4. model.project.configuration
        #    - Set in the validate_page() function
        # 5. model.project.iso_mount_point
        #    - Set in the initialize_model() function
        # 6. model.project.custom_root_directory
        #    - Set in the initialize_model() function
        # 7. model.project.custom_disk_directory
        #    - Set in the initialize_model() function

        # Prepend the selected project directory to the list of previous
        # project directories, ensuring there are no duplicates. Truncate
        # the list to five items.
        model.application.projects = list(dict.fromkeys([model.project.directory] + model.application.projects))[0:5]

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_clicked__start_page__project_directory_open_button(widget):

    logger.log_label('Clicked start page project directory open button')

    directory_chooser.open(selected_project_directory, model.project.directory)


def on_changed__start_page__project_directory_entry(widget):

    logger.log_label('Project directory changed')

    model.project.directory = widget.get_text()

    validate_page()


########################################################################
# Support Functions
########################################################################


def selected_project_directory(directory):

    # logger.log_value('The selected directory is', original_iso_file_path)

    displayer.update_entry('start_page__project_directory_entry', directory)


########################################################################
# Validation Functions
########################################################################


def validate_page():

    # ------------------------------------------------------------------
    # No directory was selected.
    # ------------------------------------------------------------------

    if not model.project.directory:

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        message = 'Select a project directory.'
        displayer.update_label('start_page__project_directory_message', message, False)
        displayer.set_entry_error('start_page__project_directory_entry', OK)

        return  # Done

    # ------------------------------------------------------------------
    # The selected path is not a directory.
    # ------------------------------------------------------------------

    if not os.path.isdir(model.project.directory):

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        # Remove the invalid directory from list of previous projects.
        if model.project.directory in model.application.projects:
            logger.log_value('Remove inaccessible directory from projects list', model.project.directory)
            model.application.projects.remove(model.project.directory)

        # message = '<span foreground="red">Error. Select a valid directory.</span>'
        message = 'Error. Select a valid directory.'
        displayer.update_label('start_page__project_directory_message', message, True)
        displayer.set_entry_error('start_page__project_directory_entry', ERROR)

        return  # Done

    # ------------------------------------------------------------------
    # The selected directory is not writable.
    # ------------------------------------------------------------------

    if not file_utilities.directory_is_writable(model.project.directory):

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        # Remove the invalid directory from list of previous projects.
        if model.project.directory in model.application.projects:
            logger.log_value('Remove inaccessible directory from projects list', model.project.directory)
            model.application.projects.remove(model.project.directory)

        # message = '<span foreground="red">Error. Cannot access directory.</span>'
        message = 'Error. Cannot access directory.'
        displayer.update_label('start_page__project_directory_message', message, True)
        displayer.set_entry_error('start_page__project_directory_entry', ERROR)

        return  # Done

    # ------------------------------------------------------------------
    # An excluded file system was selected.
    # ------------------------------------------------------------------

    file_system_type = file_utilities.get_file_system_type(model.project.directory)
    if file_system_type in EXCLUDED_FILE_SYSTEM_TYPES:

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

        # Remove the invalid directory from list of previous projects.
        if model.project.directory in model.application.projects:
            logger.log_value('Remove excluded directory from projects list', model.project.directory)
            model.application.projects.remove(model.project.directory)

        # message = f'<span foreground="red">Error. Cannot customize Linux using the {FILE_SYSTEM_TYPES[file_system_type]} file system.</span>'
        message = f'Error. Cannot customize Linux using the {FILE_SYSTEM_TYPES[file_system_type]} file system.'
        displayer.update_label('start_page__project_directory_message', message, True)
        displayer.set_entry_error('start_page__project_directory_entry', ERROR)

        return  # Done

    # ------------------------------------------------------------------
    # Create a project log file, initialize the model, and create the
    # project configuration.
    # ------------------------------------------------------------------

    # Create a project log file.
    if logger.log:
        # Create a new log file. Prior checks above ensure the directory
        # is valid.
        logger.log_file = constructor.construct_log_file_path(model.project.directory)
        # Temporarily disable verbose mode, if it is on.
        verbose, logger.verbose = logger.verbose, False
        # Write the application title to the log file (only).
        logger.log_title('Cubic - Custom Ubuntu ISO Creator')
        # Reset verbose mode to previous value.
        logger.verbose = verbose
        logger.log_value('The log file is', logger.log_file)

    # Log the application information again because the log file does
    # not exist until a valid project directory is selected.
    logger.log_value('The application directory is', model.application.directory)
    logger.log_value('The application user home is', model.application.user_home)
    logger.log_value('The application kernel version is', model.application.kernel_version)
    logger.log_value('The application configuration is', model.application.configuration)
    logger.log_value('The application cubic version is', model.application.cubic_version)
    logger.log_value('The application visited sites are', model.application.visited_sites)
    logger.log_value('The application projects are', model.application.projects)
    logger.log_value('The application iso file path is', model.application.iso_file_path)

    # There is no need to log the following values because they are set
    # as indicated.
    # 1. model.project.cubic_version
    #    - Set in the validate_page() function
    # 2. model.project.create_date
    #    - Loaded from an existing configuration, or set to current date
    #      in the initialize_model() function
    # 3. model.project.modify_date
    #    - Set on the Project page
    # 4. model.project.directory
    #    - Set above
    # 5. model.project.configuration
    #    - Set in the validate_page() function
    # 6. model.project.iso_mount_point
    #    - Set in the validate_page() function
    # 7. model.project.custom_root_directory
    #    - Set in the validate_page() function
    # 8. model.project.custom_disk_directory
    #    - Set in the validate_page() function
    #
    # logger.log_value('The project cubic version is', model.project.cubic_version)
    # logger.log_value('The project create date is', model.project.create_date)
    # logger.log_value('The project modify date is', model.project.modify_date)
    # logger.log_value('The project directory is', model.project.directory)
    # logger.log_value('The project configuration is', model.project.configuration)
    # logger.log_value('The project iso mount point is', model.project.iso_mount_point)
    # logger.log_value('The project custom root directory is', model.project.custom_root_directory)
    # logger.log_value('The project custom disk directory is', model.project.custom_disk_directory)

    # Create the project configuration.
    file_path = constructor.construct_project_configuration_file_path(model.project.directory)
    model.project.configuration = configuration.Project(file_path)

    # Initialize the model.
    initialize_model()

    # ------------------------------------------------------------------
    # This is a new project.
    # ------------------------------------------------------------------

    if not os.path.isfile(file_path):

        # Set the Cubic version.
        model.project.cubic_version = model.application.cubic_version
        model.project.first_version = model.application.cubic_version

        # Set the create date.
        model.project.create_date = constructor.get_current_time_stamp()

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        message = 'A new Cubic project will be created using this directory.'
        displayer.update_label('start_page__project_directory_message', message, False)
        displayer.set_entry_error('start_page__project_directory_entry', OK)

        return  # Done

    # ------------------------------------------------------------------
    # This is an existing project.
    # ------------------------------------------------------------------

    model.project.configuration.load()

    # ------------------------------------------------------------------
    # Migrate existing project.
    # ------------------------------------------------------------------

    cubic_version = constructor.get_display_version(model.project.first_version)
    if version.parse(cubic_version) < version.parse(CUBIC_VERSION_2024):

        # Set the Cubic version.
        model.project.cubic_version = model.application.cubic_version
        # model.project.first_version = model.application.cubic_version

        # Already loaded the create date from the configuration.
        # model.project.create_date = constructor.get_current_time_stamp()

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=False,
            is_back_visible=False,
            next_button_label='Alert❭',
            next_action='alert',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        message = 'This directory contains a legacy Cubic project.'
        displayer.update_label('start_page__project_directory_message', message, False)
        displayer.set_entry_error('start_page__project_directory_entry', OK)

        return  # Done

    # ------------------------------------------------------------------
    # Existing project with ISO template.
    # ------------------------------------------------------------------

    # Set the Cubic version.
    model.project.cubic_version = model.application.cubic_version
    # model.project.first_version = model.application.cubic_version

    # Already loaded the create date from the configuration.
    # model.project.create_date = constructor.get_current_time_stamp()

    displayer.reset_buttons(
        back_button_label='❬Back',
        back_action='back',
        back_button_style=None,
        is_back_sensitive=False,
        is_back_visible=False,
        next_button_label='Next❭',
        next_action='next',
        next_button_style='suggested-action',
        is_next_sensitive=True,
        is_next_visible=True)

    message = 'This directory contains an existing Cubic project.'
    displayer.update_label('start_page__project_directory_message', message, False)
    displayer.set_entry_error('start_page__project_directory_entry', OK)

    return  # Done


def initialize_model():

    logger.log_label('Initialize')

    # model.project.cubic_version = model.application.cubic_version
    # model.project.first_version = model.application.first_version
    # model.project.create_date = constructor.get_current_time_stamp()
    model.project.modify_date = None
    # model.project.directory = None
    # model.project.configuration = None
    model.project.iso_mount_point = constructor.construct_original_iso_mount_point(model.project.directory)
    model.project.custom_root_directory = constructor.construct_custom_root_directory(model.project.directory)
    model.project.custom_disk_directory = constructor.construct_custom_disk_directory(model.project.directory)

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

    model.status.is_success_analyze = None
    model.status.is_success_copy = None
    model.status.is_success_extract = None
    model.status.iso_template = None
    model.status.iso_checksum = None
    model.status.iso_checksum_file_name = None

    model.options.update_os_release = None
    model.options.has_minimal_install = None
    model.options.boot_configurations = None
    model.options.compression = None
