#!/usr/bin/python3

########################################################################
#                                                                      #
# extract_page.py                                                      #
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

# https://askubuntu.com/questions/1289400/remaster-installation-image-for-ubuntu-20-10
# http://manpages.ubuntu.com/manpages/groovy/man1/xorriso.1.html
# https://linux.die.net/man/8/mkisofs
# http://manpages.ubuntu.com/manpages/groovy/man1/dd.1.html
# https://stackoverflow.com/questions/65189149/best-regex-in-python-to-not-have-double-space-in-result-when-substring-is-remo/65189757#65189757
# https://manpages.ubuntu.com/manpages/noble/man1/unsquashfs.1.html

########################################################################
# Imports
########################################################################

from packaging import version

import glob
import locale
import os
import time

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import CUBIC_VERSION_2024
from cubic.constants import FINAL_PERCENT
from cubic.constants import GAP
from cubic.constants import IMAGE_FILE_NAME
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_1000_MS
from cubic.navigator import InterruptException
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities, iso_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.progressor import track_progress

########################################################################
# Global Variables & Constants
########################################################################

name = 'extract_page'

is_page_valid = False

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

    if action == 'next':

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO:
        # Remove the "if" statement in a future release but keep the
        # code inside the "if" clause. [2024-08-10]
        #
        # The code inside the "if" clause will not work for projects
        # created using Cubic version 2024.02.86, so it should only be
        # enabled for all projects after most users are no longer
        # customizing legacy projects.
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        cubic_version = constructor.get_display_version(model.project.first_version)
        if version.parse(cubic_version) >= version.parse(CUBIC_VERSION_2024):

            # Update the status in case the user modified the cubic.conf
            # project configuration file or deleted some project files.

            # Checks for legacy layouts (using ubiquity).
            is_success_analyze_1 = bool(                    \
                model.status.is_success_analyze and         \
                model.layout.casper_directory and           \
                model.layout.squashfs_directory and         \
                model.layout.squashfs_file_name)
            is_success_copy_1 = bool(                       \
                model.status.is_success_copy and            \
                model.layout.casper_directory and           \
                model.layout.squashfs_directory)
            is_success_extract_1 = bool(                    \
                model.status.is_success_extract and         \
                model.layout.squashfs_directory and         \
                model.layout.squashfs_file_name)

            # Checks for newer layouts (using subiquity).
            is_success_analyze_2 = bool(                    \
                model.status.is_success_analyze and         \
                model.layout.casper_directory and           \
                model.layout.squashfs_directory and         \
                model.layout.minimal_squashfs_file_name and \
                model.layout.standard_squashfs_file_name)
            is_success_copy_2 = bool(                       \
                model.status.is_success_copy and            \
                model.layout.casper_directory and           \
                model.layout.squashfs_directory)
            is_success_extract_2 = bool(                    \
                model.status.is_success_extract and         \
                model.layout.squashfs_directory and         \
                model.layout.minimal_squashfs_file_name and \
                model.layout.standard_squashfs_file_name)

            model.status.is_success_analyze = is_success_analyze_1 or is_success_analyze_2
            model.status.is_success_copy = is_success_copy_1 or is_success_copy_2
            model.status.is_success_extract = is_success_extract_1 or is_success_extract_2

        # --------------------------------------------------------------
        # Analyze
        # --------------------------------------------------------------

        displayer.set_visible('extract_page__analyze_original_iso_section',
                              not model.status.is_success_analyze or \
                              not model.status.iso_template)
        displayer.update_status('extract_page__analyze_original_iso', BULLET)
        displayer.update_label('extract_page__analyze_original_iso_message', '...', False)

        # --------------------------------------------------------------
        # Copy
        # --------------------------------------------------------------

        displayer.set_visible('extract_page__copy_original_iso_files_section', not model.status.is_success_copy)
        displayer.update_status('extract_page__copy_original_iso_files', BULLET)
        displayer.update_progress_bar_percent('extract_page__copy_original_iso_files_progress_bar', 0)
        # displayer.update_progress_bar_text('extract_page__copy_original_iso_files_progress_bar', None)
        displayer.update_label('extract_page__copy_original_iso_files_message', '', False)

        # --------------------------------------------------------------
        # Extract
        # --------------------------------------------------------------

        displayer.set_visible('extract_page__unsquashfs_section', not model.status.is_success_extract)
        displayer.update_status('extract_page__unsquashfs', BULLET)
        displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', 0)
        # displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar', None)
        displayer.update_label('extract_page__unsquashfs_message', '', False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Customize❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=False,
            is_next_visible=True)

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

    Specific success or error messages should be displayed in the called
    functions, but the display status should be set here because they
    depend on the outcome of multiple functions.
    """

    if action == 'next':

        # --------------------------------------------------------------
        # Analyze
        # --------------------------------------------------------------

        if not (model.status.iso_template and model.status.is_success_analyze):

            displayer.update_status('extract_page__analyze_original_iso', PROCESSING)

            time.sleep(SLEEP_1000_MS)

            if not model.status.iso_template:

                # Delete the old image files. Ignore errors.
                file_path_pattern = os.path.join(model.project.directory, IMAGE_FILE_NAME % '[1-9]')
                file_utilities.delete_files_with_pattern(file_path_pattern)

                # Identify the template for the original disk image.
                # • Set model.status.iso_template
                is_error = analyze_iso_template()

                if is_error: return  # Stay on this page.

            if not model.status.is_success_analyze:

                source_directory_path = model.project.iso_mount_point

                # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
                # TODO: Remove this section in the future. [2024-08-10]
                # Migrate a project created using Cubic version
                # 2024.02.86 to a newer version.
                # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
                if not iso_utilities.is_mounted(model.project.iso_mount_point):
                    source_directory_path = model.project.custom_disk_directory

                # Analyze the ISO layout.
                # • Set model.status.is_success_analyze
                # • Set model.layout.squashfs_directory
                # • Set model.layout.standard_squashfs_file_name
                # • Set model.layout.casper_directory
                # • Set model.layout.*
                # • Set model.status.has_minimal_install

                is_error = analyze_iso_layout(source_directory_path)

                if is_error: return  # Stay on this page.

            # Pause to allow the user to see the result.
            message = 'Success.'
            displayer.update_label('extract_page__analyze_original_iso_message', message, False)
            displayer.update_status('extract_page__analyze_original_iso', OK)
            time.sleep(SLEEP_1000_MS)

        # --------------------------------------------------------------
        # Copy
        # --------------------------------------------------------------

        if not model.status.is_success_copy:

            displayer.update_status('extract_page__copy_original_iso_files', PROCESSING)

            # Copy important files from the original disk image.
            # Set the following:
            # • Set model.status.is_success_copy
            is_error = copy_original_iso_files()

            if is_error: return  # Stay on this page.

            # Pause to allow the user to see the result.
            message = 'Success.'
            displayer.update_label('extract_page__copy_original_iso_files_message', message, False)
            displayer.update_status('extract_page__copy_original_iso_files', OK)
            time.sleep(SLEEP_1000_MS)

        # --------------------------------------------------------------
        # Extract
        # --------------------------------------------------------------

        if not model.status.is_success_extract:

            displayer.update_status('extract_page__unsquashfs', PROCESSING)

            # Clear the terminal because the history will no longer be
            # valid when the new squashfs files are extracted.
            terminal = model.builder.get_object('terminal_page__terminal')
            terminal.reset(True, True)

            # Delete the custom root directory if it exists.
            file_utilities.delete_path_as_root(model.project.custom_root_directory)

            # Identify squashfs files to extract.
            directory_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory)
#            if model.layout.squashfs_file_name:
#                file_names = [model.layout.squashfs_file_name]
#            else:
#                '''
#                file_names = [model.layout.minimal_squashfs_file_name,         \
#                              model.layout.standard_squashfs_file_name,        \
#                              model.layout.installer_squashfs_file_name,       \
#                              model.layout.installer_generic_squashfs_file_name]
#                '''
#                '''
#                file_names = [model.layout.minimal_squashfs_file_name,         \
#                              model.layout.standard_squashfs_file_name,        \
#                              model.layout.installer_squashfs_file_name,       ]
#                '''
#                file_names = [model.layout.minimal_squashfs_file_name, \
#                              model.layout.standard_squashfs_file_name]
            # muquit ---
            # identify squashfs files to extract.
            directory_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory)
            if model.layout.squashfs_file_name:
                file_names = [model.layout.squashfs_file_name]
            elif model.layout.minimal_squashfs_file_name:
                file_names = [model.layout.minimal_squashfs_file_name]
            else:
                file_names = [model.layout.standard_squashfs_file_name]
            # muquit ---

            # Exclude empty file names and links.
            file_names = [file_name for file_name in file_names \
                          if file_name and not os.path.islink(os.path.join(directory_path, file_name))]

            # Extract each squashfs file in sequence.
            # • Set model.status.is_success_extract
            total_files = len(file_names)
            for file_number, file_name in enumerate(file_names):
                is_error = extract_squashfs(file_name, file_number, total_files)
                if is_error: return  # Stay on this page.

            # Pause to allow the user to see the result.
            message = 'Success.'
            displayer.update_label('extract_page__unsquashfs_message', message, False)
            displayer.update_status('extract_page__unsquashfs', OK)
            time.sleep(SLEEP_1000_MS)

        return 'next'

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

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'quit':

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

# N/A

########################################################################
# Support Functions
########################################################################

# ----------------------------------------------------------------------
# Analyze Original Disk Functions
# ----------------------------------------------------------------------


def analyze_iso_template():

    logger.log_label('Generate the ISO template')

    iso_report = iso_utilities.get_iso_report()
    template = iso_utilities.generate_iso_template(iso_report)
    if template:
        model.status.iso_template = constructor.encode(template)
    else:
        model.status.iso_template = None

    if not model.status.iso_template:
        logger.log_value('Error', 'Unable to identify information about this disk')
        # message = '<span foreground="red">Error. Unable to identify information about this disk.</span>'
        message = 'Error. Unable to identify information about this disk'
        displayer.update_label('extract_page__analyze_original_iso_message', message, True)
        displayer.update_status('extract_page__analyze_original_iso', ERROR)
        return True
    else:
        return False


def identify_directories_and_files(source_directory_path, directory_attribute, file_attribute):
    """
    Identify a directory by searching for files within the directory.
    """

    directory_patterns = model.layout.values(directory_attribute)
    for directory_pattern in directory_patterns:
        directory_path_pattern = os.path.join(source_directory_path, directory_pattern)
        directory_paths = glob.glob(directory_path_pattern)
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                file_name_patterns = model.layout.values(file_attribute)
                for file_name_pattern in file_name_patterns:
                    file_path_pattern = os.path.join(directory_path, file_name_pattern)
                    file_paths = glob.glob(file_path_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            # Set the directory.
                            directory = os.path.relpath(directory_path, source_directory_path)
                            model.layout.set(directory_attribute, directory, True)
                            # Set the file name.
                            file_name = os.path.relpath(file_path, directory_path)
                            model.layout.set(file_attribute, file_name, True)


def identify_directories(source_directory_path, directory_attribute, file_attribute):
    """
    Identify a directory by searching for files within the directory.
    """

    directory_patterns = model.layout.values(directory_attribute)
    for directory_pattern in directory_patterns:
        directory_path_pattern = os.path.join(source_directory_path, directory_pattern)
        directory_paths = glob.glob(directory_path_pattern)
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                file_name_patterns = model.layout.values(file_attribute)
                for file_name_pattern in file_name_patterns:
                    file_path_pattern = os.path.join(directory_path, file_name_pattern)
                    file_paths = glob.glob(file_path_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            # Set the directory.
                            directory = os.path.relpath(directory_path, source_directory_path)
                            model.layout.set(directory_attribute, directory, True)
                            # Set the file name.
                            # file_name = os.path.relpath(file_path, directory_path)
                            # model.layout.set(file_attribute, file_name, True)


def identify_files(source_directory_path, directory_attribute, file_attribute):
    """
    Identify files within the directory.
    """

    directory_patterns = model.layout.values(directory_attribute)
    for directory_pattern in directory_patterns:
        directory_path_pattern = os.path.join(source_directory_path, directory_pattern)
        directory_paths = glob.glob(directory_path_pattern)
        for directory_path in directory_paths:
            if os.path.exists(directory_path):
                file_name_patterns = model.layout.values(file_attribute)
                for file_name_pattern in file_name_patterns:
                    file_path_pattern = os.path.join(directory_path, file_name_pattern)
                    file_paths = glob.glob(file_path_pattern)
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            # Set the directory.
                            # directory = os.path.relpath(directory_path, source_directory_path)
                            # model.layout.set(directory_attribute, directory, True)
                            # Set the file name.
                            file_name = os.path.relpath(file_path, directory_path)
                            model.layout.set(file_attribute, file_name, True)


def analyze_iso_layout(source_directory_path):
    """
    Set valid possible values for each attribute as True.
    Set invalid possible values for each attribute as False.
    (See the Structures class).

    Args:
        source_directory_path (str): The source directory path

    Returns:
        None: N/A
    """

    logger.log_label('Analyze the ISO layout')

    logger.log_value('Analyze', source_directory_path)

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

    # Initialize the layout.
    # Although layout is reset on the Start page and the Delete page,
    # if the user clicks cancel, returns to the project page, and
    # selects a different original ISO, the layout values should be
    # reset, so the values from the previous ISO are not preserved.
    model.layout.reset()

    # Casper Section (Directories)
    # Identify the casper_directory using:
    # • initrd_file_name
    # • vmlinuz_file_name
    identify_directories(source_directory_path, 'casper_directory', 'initrd_file_name')
    identify_directories(source_directory_path, 'casper_directory', 'vmlinuz_file_name')

    # Casper Section (Files)
    identify_files(source_directory_path, 'casper_directory', 'initrd_file_name')
    identify_files(source_directory_path, 'casper_directory', 'vmlinuz_file_name')

    # General Section (Directories)
    # Identify the squashfs_directory using:
    # • squashfs_file_name
    # • minimal_squashfs_file_name
    # • standard_squashfs_file_name
    identify_directories(source_directory_path, 'squashfs_directory', 'squashfs_file_name')
    identify_directories(source_directory_path, 'squashfs_directory', 'minimal_squashfs_file_name')
    identify_directories(source_directory_path, 'squashfs_directory', 'standard_squashfs_file_name')

    # General Section (Files)
    identify_files(source_directory_path, 'squashfs_directory', 'squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_remove_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'standard_remove_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'size_file_name')

    # Minimal Section
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'minimal_size_file_name')

    # Standard Section
    identify_files(source_directory_path, 'squashfs_directory', 'standard_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'standard_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'standard_size_file_name')

    # Installer / Live Section
    identify_files(source_directory_path, 'squashfs_directory', 'installer_sources_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'installer_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'installer_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'installer_size_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'installer_generic_squashfs_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'installer_generic_manifest_file_name')
    identify_files(source_directory_path, 'squashfs_directory', 'installer_generic_size_file_name')

    # print('-' * 80)
    # model.layout.print()
    # print('-' * 80)

    # Set important files that may not exist on the original ISO.
    if not model.layout.size_file_name:
        model.layout.size_file_name = 'filesystem.size', True
    if not model.layout.manifest_file_name:
        model.layout.manifest_file_name = 'filesystem.manifest', True

    # Identify if the ISO has a legacy minimal install option.
    model.options.has_minimal_install = bool(model.layout.minimal_remove_file_name)

    # Check if the analysis succeeded.
    is_success_analyze_1 = bool(                    \
        model.layout.casper_directory and           \
        model.layout.squashfs_directory and         \
        model.layout.squashfs_file_name)
#    is_success_analyze_2 = bool(                    \
#        model.layout.casper_directory and           \
#        model.layout.squashfs_directory and         \
#        model.layout.minimal_squashfs_file_name and \
#        model.layout.standard_squashfs_file_name)
# muquit
    is_success_analyze_2 = bool(                    \
        model.layout.casper_directory and           \
        model.layout.squashfs_directory and         \
        (model.layout.minimal_squashfs_file_name or \
        model.layout.standard_squashfs_file_name))
    model.status.is_success_analyze = is_success_analyze_1 or is_success_analyze_2

    is_error = not model.status.is_success_analyze

    # muquit ---
    logger.log_value('casper_directory', model.layout.casper_directory)
    logger.log_value('squashfs_directory', model.layout.squashfs_directory)
    logger.log_value('minimal_squashfs_file_name', model.layout.minimal_squashfs_file_name)
    logger.log_value('standard_squashfs_file_name', model.layout.standard_squashfs_file_name)
    logger.log_value('is_success_analyze_1', is_success_analyze_1)
    logger.log_value('is_success_analyze_2', is_success_analyze_2)
    # muquit ---

    return is_error


# ----------------------------------------------------------------------
# Copy Original Disk Files Functions
# ----------------------------------------------------------------------
"""
Here is an example of the files that are copied (and not copied) for
ubuntu-24.04-desktop. Note that "??" represents languages, including
"no-languages".

~ ~ ~  copy: filesystem.manifest
~ ~ ~  copy: filesystem.size
~ ~ ~  copy: install-sources.yaml
do not copy: minimal.manifest
do not copy: minimal.size
do not copy: minimal.squashfs
do not copy: minimal.squashfs.gpg

do not copy: minimal.??.manifest
do not copy: minimal.??.size
do not copy: minimal.??.squashfs
do not copy: minimal.??.squashfs.gpg

do not copy: minimal.standard.manifest
do not copy: minimal.standard.size
do not copy: minimal.standard.squashfs
do not copy: minimal.standard.squashfs.gpg

~ ~ ~  copy: minimal.standard.live.manifest
~ ~ ~  copy: minimal.standard.live.size
~ ~ ~  copy: minimal.standard.live.squashfs
do not copy: minimal.standard.live.squashfs.gpg

do not copy: minimal.standard.??.manifest
do not copy: minimal.standard.??.size
do not copy: minimal.standard.??.squashfs
do not copy: minimal.standard.??.squashfs.gpg

do not copy: minimal.enhanced-secureboot.manifest
do not copy: minimal.enhanced-secureboot.size
do not copy: minimal.enhanced-secureboot.squashfs
do not copy: minimal.enhanced-secureboot.squashfs.gpg

do not copy: minimal.enhanced-secureboot.??.manifest
do not copy: minimal.enhanced-secureboot.??.size
do not copy: minimal.enhanced-secureboot.??.squashfs
do not copy: minimal.enhanced-secureboot.??.squashfs.gpg

do not copy: minimal.standard.enhanced-secureboot.manifest
do not copy: minimal.standard.enhanced-secureboot.size
do not copy: minimal.standard.enhanced-secureboot.squashfs
do not copy: minimal.standard.enhanced-secureboot.squashfs.gpg

do not copy: minimal.standard.enhanced-secureboot.??.manifest
do not copy: minimal.standard.enhanced-secureboot.??.size
do not copy: minimal.standard.enhanced-secureboot.??.squashfs
do not copy: minimal.standard.enhanced-secureboot.??.squashfs.gpg

~ ~ ~  copy: initrd
~ ~ ~  copy: vmlinuz
"""


def copy_original_iso_files():
    """
    Excludes all files in the casper and squashfs directories, but
    copies specified files.

    Exclude or copy the following files:

    do not copy: md5sum.txt
    do not copy: MD5SUMS
    do not copy: .disk/release notes url

    # Casper Section
    ~ ~ ~  copy: initrd file name
    ~ ~ ~  copy: vmlinuz file name

    # General Section
    do not copy: squashfs file name
    do not copy: manifest file name
    ~ ~ ~  copy: minimal remove file name
    ~ ~ ~  copy: standard remove file name
    do not copy: size file name

    # Minimal Section
    do not copy: minimal squashfs file name
    do not copy: minimal manifest file name
    do not copy: minimal size file name

    # Standard Section
    do not copy: standard squashfs file name
    do not copy: standard manifest file name
    do not copy: standard size file name

    # Installer / Live Section
    ~ ~ ~  copy: installer sources file name
    ~ ~ ~  copy: installer squashfs file name
    ~ ~ ~  copy: installer manifest file name
    ~ ~ ~  copy: installer size file name
    ~ ~ ~  copy: installer generic squashfs file name
    ~ ~ ~  copy: installer generic manifest file name
    ~ ~ ~  copy: installer generic size file name
    """

    logger.log_label('Copy important files from the original disk image')

    # Add a "/" at the end of the path so rsync copies the contents
    # of the source directory to the target directory.
    source_file_path = os.path.join(model.project.iso_mount_point, '')
    logger.log_value('The source file path is', source_file_path)

    # Add a "/" at the end of the path so rsync copies files into
    # the target directory. This is not required, but is consistent
    # with the source directory path above.
    target_file_path = os.path.join(model.project.custom_disk_directory, '')
    logger.log_value('The target file path is', target_file_path)

    # Copy files from the original iso.

    # Some important rsync options:
    #
    #   -rlptgoD
    #
    #     -r --recursive
    #     -l --links
    #     -p --perms (do not use)
    #     -t --times
    #     -g --group
    #     -O --owner
    #     -D --devices --specials

    # Use info=progress2 to get the total progress, instead of the
    # progress for individual files.
    # Add read and write permissions for the user.
    # Set read and write permissions for group and other.

    # Includes: Casper Section
    include_11 = constructor.construct_rsync_includes(model.layout.casper_directory_as_list, model.layout.initrd_file_name_as_list)
    include_12 = constructor.construct_rsync_includes(model.layout.casper_directory_as_list, model.layout.vmlinuz_file_name_as_list)

    # Includes: General Section
    include_21 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.minimal_remove_file_name_as_list)
    include_22 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.standard_remove_file_name_as_list)

    # Includes: Installer / Live Section
    include_31 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_sources_file_name_as_list)
    include_32 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_squashfs_file_name_as_list)
    include_33 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_manifest_file_name_as_list)
    include_34 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_size_file_name_as_list)
    include_35 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_generic_squashfs_file_name_as_list)
    include_36 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_generic_manifest_file_name_as_list)
    include_37 = constructor.construct_rsync_includes(model.layout.squashfs_directory_as_list, model.layout.installer_generic_size_file_name_as_list)

    # Excludes: Casper Section
    # The * is used to exclude all files in the casper directory.
    # However, the preceding includes supersede all excludes, so
    # specified files in the casper directory will still be copied.
    exclude_11 = constructor.construct_rsync_excludes(model.layout.casper_directory_as_list, ['*'])

    # Excludes: General Section
    # The * is used to exclude all files in the squashfs directory.
    # However, the preceding includes supersede all excludes, so
    # specified files in the squashfs directory will still be copied.
    exclude_21 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, ['*'])

    # Do not include a leading "/" in front of the relative file paths,
    # in the include and exclude arguments. Includes must precede
    # excludes.
    command = (
        'rsync'
        f' --info=progress2 "{source_file_path}" "{target_file_path}"'
        ' --delete'
        # ' --archive'
        ' --recursive'
        ' --links'
        ' --chmod=u+rwX,g=rX,o=rX'
        # Casper Section
        f' {include_11}'  # initrd_file_name
        f' {include_12}'  # vmlinuz_file_name
        # General Section
        f' {include_21}'  # minimal_remove_file_name
        f' {include_22}'  # standard_remove_file_name
        # Installer / Live Section
        f' {include_31}'  # installer_sources_file_name
        f' {include_32}'  # installer_squashfs_file_name
        f' {include_33}'  # installer_manifest_file_name
        f' {include_34}'  # installer_size_file_name
        f' {include_35}'  # installer_generic_squashfs_file
        f' {include_36}'  # installer_generic_manifest_file_name
        f' {include_37}'  # installer_generic_size_file_name
        # Casper Section
        f' {exclude_11}'  # casper_directory
        # General Section
        f' {exclude_21}'  # squashfs_directory
        # Additional Excludes
        ' --exclude="md5sum.txt"'
        ' --exclude="MD5SUMS"'
        ' --exclude=".disk/release_notes_url"')

    # The progress callback function.
    def progress_callback(percent):
        displayer.update_progress_bar_percent('extract_page__copy_original_iso_files_progress_bar', percent)
        if percent % 10 == 0:
            logger.log_value('Completed', f'{percent:n}%')

    try:
        track_progress(command, progress_callback)
    except InterruptException as exception:
        model.status.is_success_copy = False
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to copy files from the original disk image.</span>'
            message = 'Error. Unable to copy files from the original disk image.'
        displayer.update_label('extract_page__copy_original_iso_files_message', message, True)
        displayer.update_status('extract_page__copy_original_iso_files', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        model.status.is_success_copy = False
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to copy files from the original disk image.</span>'
            message = 'Error. Unable to copy files from the original disk image.'
        displayer.update_label('extract_page__copy_original_iso_files_message', message, True)
        displayer.update_status('extract_page__copy_original_iso_files', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    model.status.is_success_copy = True

    return False  # (No Error)


def copy_original_iso_files_ALTERNATIVE():
    """
    Copies all files in the casper and squashfs directories, but
    excludes specified files.

    Exclude or copy the following files:

    do not copy: md5sum.txt
    do not copy: MD5SUMS
    do not copy: .disk/release notes url

    # Casper Section
    ~ ~ ~  copy: initrd file name
    ~ ~ ~  copy: vmlinuz file name

    # General Section
    do not copy: squashfs file name
    do not copy: manifest file name
    ~ ~ ~  copy: minimal remove file name
    ~ ~ ~  copy: standard remove file name
    do not copy: size file name

    # Minimal Section
    do not copy: minimal squashfs file name
    do not copy: minimal manifest file name
    do not copy: minimal size file name

    # Standard Section
    do not copy: standard squashfs file name
    do not copy: standard manifest file name
    do not copy: standard size file name

    # Installer / Live Section
    ~ ~ ~  copy: installer sources file name
    ~ ~ ~  copy: installer squashfs file name
    ~ ~ ~  copy: installer manifest file name
    ~ ~ ~  copy: installer size file name
    ~ ~ ~  copy: installer generic squashfs file name
    ~ ~ ~  copy: installer generic manifest file name
    ~ ~ ~  copy: installer generic size file name

    do not copy: squashfs directory/*.gpg
    """

    logger.log_label('Copy important files from the original disk image')

    # Add a "/" at the end of the path so rsync copies the contents
    # of the source directory to the target directory.
    source_file_path = os.path.join(model.project.iso_mount_point, '')
    logger.log_value('The source file path is', source_file_path)

    # Add a "/" at the end of the path so rsync copies files into
    # the target directory. This is not required, but is consistent
    # with the source directory path above.
    target_file_path = os.path.join(model.project.custom_disk_directory, '')
    logger.log_value('The target file path is', target_file_path)

    # Copy files from the original iso.

    # Some important rsync options:
    #
    #   -rlptgoD
    #
    #     -r --recursive
    #     -l --links
    #     -p --perms (do not use)
    #     -t --times
    #     -g --group
    #     -O --owner
    #     -D --devices --specials

    # Use info=progress2 to get the total progress, instead of the
    # progress for individual files.
    # Add read and write permissions for the user.
    # Set read and write permissions for group and other.

    # General Section
    exclude_11 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.squashfs_file_name_as_list)
    exclude_12 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.manifest_file_name_as_list)
    exclude_13 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.size_file_name_as_list)

    # Minimal Section
    exclude_21 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.minimal_squashfs_file_name_as_list)
    exclude_22 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.minimal_manifest_file_name_as_list)
    exclude_23 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.minimal_size_file_name_as_list)

    # Standard Section
    exclude_31 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.standard_squashfs_file_name_as_list)
    exclude_32 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.standard_manifest_file_name_as_list)
    exclude_33 = constructor.construct_rsync_excludes(model.layout.squashfs_directory_as_list, model.layout.standard_size_file_name_as_list)

    # Do not include a leading "/" in front of the relative file paths
    # in the include and exclude arguments.
    command = (
        'rsync'
        f' --info=progress2 "{source_file_path}" "{target_file_path}"'
        ' --delete'
        # ' --archive'
        ' --recursive'
        ' --links'
        ' --chmod=u+rwX,g=rX,o=rX'
        # Squashfs Section
        f' {exclude_11}'  # squashfs_file_name
        f' {exclude_12}'  # manifest_file_name
        f' {exclude_13}'  # size_file_name
        # Minimal Section
        f' {exclude_21}'  # minimal_squashfs_file_name
        f' {exclude_22}'  # minimal_manifest_file_name
        f' {exclude_23}'  # minimal_size_file_name
        # Standard Section
        f' {exclude_31}'  # standard_squashfs_file_name
        f' {exclude_32}'  # standard_manifest_file_name
        f' {exclude_33}'  # standard_size_file_name
        f' --exclude="{model.layout.squashfs_directory}/*.gpg"'
        ' --exclude="md5sum.txt"'
        ' --exclude="MD5SUMS"'
        ' --exclude=".disk/release_notes_url"')

    # The progress callback function.
    def progress_callback(percent):
        displayer.update_progress_bar_percent('extract_page__copy_original_iso_files_progress_bar', percent)
        if percent % 10 == 0:
            logger.log_value('Completed', f'{percent:n}%')

    try:
        track_progress(command, progress_callback)
    except InterruptException as exception:
        model.status.is_success_copy = False
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to copy files from the original disk image.</span>'
            message = 'Error. Unable to copy files from the original disk image.'
        displayer.update_label('extract_page__copy_original_iso_files_message', message, True)
        displayer.update_status('extract_page__copy_original_iso_files', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        model.status.is_success_copy = False
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to copy files from the original disk image.</span>'
            message = 'Error. Unable to copy files from the original disk image.'
        displayer.update_label('extract_page__copy_original_iso_files_message', message, True)
        displayer.update_status('extract_page__copy_original_iso_files', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    model.status.is_success_copy = True

    return False  # (No Error)


# ----------------------------------------------------------------------
# Extract Linux File System Functions
# ----------------------------------------------------------------------


def extract_squashfs(file_name, file_number, total_files):

    logger.log_label('Extract the compressed Linux file system')
    # muquit -starts -
    target_file_path = model.project.custom_root_directory
    source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
    logger.log_value('Starting extraction of', file_name)
    logger.log_value('Target path', target_file_path)
    logger.log_value('Source path', source_file_path)
    logger.log_value('file_name', file_name)
    logger.log_value('file_number', file_number)
    logger.log_value('total_files', total_files)
    logger.log_value('target_file_path', model.project.custom_root_directory)
    logger.log_value('source_file_path', os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name))
    # muquit -ends -
    target_file_path = model.project.custom_root_directory
    logger.log_value('The target file path is', target_file_path)

    source_file_path = os.path.join(model.project.iso_mount_point, model.layout.squashfs_directory, file_name)
    logger.log_value('The source file path is', source_file_path)

    if total_files > 1:
        file_number_text = constructor.number_as_text(file_number + 1)
        total_files_text = constructor.number_as_text(total_files)
        message = f'Extracting Linux file system {file_number_text} of {total_files_text}.'
    else:
        message = 'Extracting the Linux file system.'
    displayer.update_label('extract_page__unsquashfs_message', message, False)

    # https://manpages.ubuntu.com/manpages/noble/man1/unsquashfs.1.html
    # EXIT STATUS
    # 0 The filesystem listed or extracted OK.
    # 1 FATAL errors occurred, e.g. filesystem corruption, I/O errors.
    #   Unsquashfs did not continue and aborted.
    # 2 Non-fatal errors occurred, e.g. no support for XATTRs, Symbolic
    #   links in output filesystem or couldn't write permissions to
    #   output filesystem. Unsquashfs continued and did not abort.
    # See -ignore-errors, -strict-errors and -no-exit-code options for
    # how they affect the exit status.
    program = os.path.join(model.application.directory, 'commands', 'extract-root')
    command = ['pkexec', program, target_file_path, source_file_path]

    # The progress callback function.
    def progress_callback(percent):
        total_percent = (FINAL_PERCENT * file_number + percent) / total_files
        # displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
        displayer.update_progress_bar_text('extract_page__unsquashfs_progress_bar', f'{locale.format_string("%.1f", total_percent, True)}{GAP}%')
        displayer.update_progress_bar_percent('extract_page__unsquashfs_progress_bar', total_percent)
        if total_percent % 10 == 0:
            logger.log_value('Completed', f'{total_percent:n}%')

    try:
        # muquit --
        logger.log_value('Running command', ' '.join(command))
        track_progress(command, progress_callback)
        # muquit
        logger.log_value('Extraction completed for', file_name)
    except InterruptException as exception:
        model.status.is_success_extract = False
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to extract the compressed Linux file system.</span>'
            message = 'Error. Unable to extract the compressed Linux file system.'
        displayer.update_label('extract_page__unsquashfs_message', message, True)
        displayer.update_status('extract_page__unsquashfs', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        # muquit
        logger.log_value('Exception during extraction', str(exception))
        raise
        # muquit
        model.status.is_success_extract = False
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to extract the compressed Linux file system.</span>'
            message = 'Error. Unable to extract the compressed Linux file system.'
        displayer.update_label('extract_page__unsquashfs_message', message, True)
        displayer.update_status('extract_page__unsquashfs', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    model.status.is_success_extract = True
    return False  # (No error)
