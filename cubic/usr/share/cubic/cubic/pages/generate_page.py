#!/usr/bin/python3

########################################################################
#                                                                      #
# generate_page.py                                                     #
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

# http://manpages.ubuntu.com/manpages/groovy/man1/xorrisofs.1.html
# https://linux.die.net/man/8/mkisofs

########################################################################
# Imports
########################################################################

import getpass
import locale
import os
import re
import sys
import time

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import FINAL_PERCENT
from cubic.constants import GAP
from cubic.constants import MIB, GIB, MAXIMUM_DISK_SIZE_BYTES, MAXIMUM_DISK_SIZE_GIB
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_0500_MS
from cubic.constants import TIME_STAMP_FORMAT_YYYYMMDD
from cubic.navigator import InterruptException
from cubic.pages import options_page
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.processor import execute_synchronous
from cubic.utilities.progressor import track_progress

########################################################################
# Global Variables & Constants
########################################################################

name = 'generate_page'

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

    if action == 'generate':

        displayer.update_status('generate_page__copy_boot_files', BULLET)
        displayer.update_progress_bar_percent('generate_page__copy_boot_files_progress_bar', 0)
        # displayer.update_progress_bar_text('generate_page__copy_boot_files_progress_bar', ' ')
        displayer.update_label('generate_page__copy_boot_files_message', '...', False)

        displayer.update_status('generate_page__create_squashfs', BULLET)
        displayer.update_progress_bar_percent('generate_page__create_squashfs_progress_bar', 0)
        displayer.update_progress_bar_text('generate_page__create_squashfs_progress_bar', ' ')
        displayer.update_label('generate_page__create_squashfs_message', '...', False)

        displayer.update_status('generate_page__update_file_system_size', BULLET)
        displayer.update_label('generate_page__update_file_system_size_message', '...', False)

        displayer.update_status('generate_page__update_disk_and_installer_info', BULLET)
        displayer.update_label('generate_page__update_disk_and_installer_info_message', '...', False)

        displayer.update_status('generate_page__update_checksums', BULLET)
        displayer.update_progress_bar_percent('generate_page__update_checksums_progress_bar', 0)
        displayer.update_progress_bar_text('generate_page__update_checksums_progress_bar', ' ')
        displayer.update_label('generate_page__update_checksums_message', '...', False)

        displayer.update_status('generate_page__check_custom_disk_size', BULLET)
        displayer.update_label('generate_page__check_custom_disk_size_message', '...', False)

        displayer.update_status('generate_page__create_iso_image', BULLET)
        displayer.update_progress_bar_percent('generate_page__create_iso_image_progress_bar', 0)
        displayer.update_progress_bar_text('generate_page__create_iso_image_progress_bar', ' ')
        displayer.update_label('generate_page__create_iso_image_message', '...', False)

        displayer.update_status('generate_page__calculate_iso_image_checksum', BULLET)
        displayer.update_label('generate_page__calculate_iso_image_checksum_message', '...', False)

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Finish❭',
            next_action='finish',
            next_button_style=None,
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
    """

    if action == 'generate':

        # --------------------------------------------------------------
        # Copy boot files.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__copy_boot_files', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = copy_kernel_files()
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Create squashfs.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__create_squashfs', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = create_squashfs()
        sys.stdout.flush()  # Flush the output before proceeding.
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Update file system size.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__update_file_system_size', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = update_file_system_size()
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Update disk and installer information.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__update_disk_and_installer_info', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = update_disk_and_installer_info()
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Update MD5 checksums.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__update_checksums', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = update_checksums()
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Check disk size.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__check_custom_disk_size', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = check_custom_disk_directory_size()
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Create links for attributes.
        # --------------------------------------------------------------

        # This should be fast, so no need to display progress.

        create_links_for_attributes()

        # --------------------------------------------------------------
        # Create disk image.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__create_iso_image', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = create_iso_image()
        sys.stdout.flush()  # Flush the output before proceeding.
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Calculate disk image checksum.
        # --------------------------------------------------------------

        displayer.update_status('generate_page__calculate_iso_image_checksum', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = calculate_checksum_for_iso()
        if is_error: return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # Success. Pause to allow the user to see the page.
        time.sleep(SLEEP_0500_MS)

        return 'finish'

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

    elif action == 'error':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'finish':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        options_page.preseed_tab.remove_tree()
        options_page.boot_tab.remove_tree()

        # Save the model values.
        # model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'

    return


########################################################################
# Handler Functions
########################################################################

# N/A

########################################################################
# Support Functions
########################################################################

# ----------------------------------------------------------------------
# Copy Disk Kernel Files Functions
# ----------------------------------------------------------------------


def copy_kernel_files():
    """
    Copies vmlinuz & initrd files to the custom disk.
    """

    # ------------------------------------------------------------------
    # Vmlinuz & Initrd
    # ------------------------------------------------------------------

    time.sleep(SLEEP_0500_MS)

    logger.log_label('Identify the selected kernel')

    # Get the selected kernel.

    # 0: version_name
    # 1: vmlinuz_file_name
    # 2: new_vmlinuz_file_name
    # 3: initrd_file_name
    # 4: new_initrd_file_name
    # 5: directory
    # 6: note
    # 7: is_selected

    list_store = model.builder.get_object('kernel_tab__list_store')
    for selected_index, kernel_details in enumerate(list_store):
        if kernel_details[7]:
            break
    else:
        selected_index = 0
    logger.log_value('The selected kernel is index number', selected_index)

    # Get the selected directory.
    source_directory = list_store[selected_index][5]

    # Get the target directory.
    target_directory = os.path.join(model.project.custom_disk_directory, model.layout.casper_directory)

    # displayer.update_progress_bar_percent('generate_page__copy_boot_files_progress_bar', 0)

    # ------------------------------------------------------------------
    # Vmlinuz
    # ------------------------------------------------------------------

    logger.log_label('Update the vmlinuz boot file')

    source_file_name = list_store[selected_index][1]
    source_file_path = os.path.join(source_directory, source_file_name)
    target_file_name = list_store[selected_index][2]
    target_file_path = os.path.join(target_directory, target_file_name)
    user = getpass.getuser()

    # Delete existing vmlinuz* files in the target directory. Do not
    # remove a file if it matches the target file name, because it will
    # be efficiently updated by rsync.
    file_path_pattern = os.path.join(target_directory, 'vmlinuz*')
    file_utilities.delete_files_with_pattern(file_path_pattern, [target_file_path])

    # Copy the new vmlinuz file.
    try:
        _copy_kernel_file(source_file_path, target_file_path, user, file_number=0, total_files=2)
    except InterruptException as exception:
        # message = '<span foreground="red">Error. Unable to update the vmlinuz boot file.</span>'
        message = 'Error. Unable to update the vmlinuz boot file.'
        displayer.update_label('generate_page__copy_boot_files_message', message, True)
        displayer.update_status('generate_page__copy_boot_files', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        # message = '<span foreground="red">Error. Unable to update the vmlinuz boot file.</span>'
        message = 'Error. Unable to update the vmlinuz boot file.'
        displayer.update_label('generate_page__copy_boot_files_message', message, True)
        displayer.update_status('generate_page__copy_boot_files', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    # Workaround for Pop!_OS.
    # Create a symlink from vmlinuz.efi to vmlinuz.
    # Workaround for Bug #1900917, "Kernel Panic on Boot After
    # Installation (No initrd in grub.cfg)."
    # Reference Bug #1898749, "Pop!_OS expects vmlinuz on the ISO to
    # have the *.efi extension."
    # Reference Bug #1895770, "Pop!_OS expects the initramfs bootstrap
    # file to be explicitly named "initrd.gz"
    is_pop_os_based = constructor.os_is_distribution('pop', model.project.custom_root_directory)
    if is_pop_os_based:
        directory_path = target_directory
        file_name = target_file_name
        link_name = 'vmlinuz.efi'
        logger.log_value('For Pop!_OS, create link', f'from {link_name} to {file_name} in {directory_path}')
        file_utilities.create_link(directory_path, file_name, link_name)

    # ------------------------------------------------------------------
    # Initrd
    # ------------------------------------------------------------------

    logger.log_label('Update the initrd boot file')

    source_file_name = list_store[selected_index][3]
    source_file_path = os.path.join(source_directory, source_file_name)
    target_file_name = list_store[selected_index][4]
    target_file_path = os.path.join(target_directory, target_file_name)
    user = getpass.getuser()

    # Delete existing initrd* files in the target directory. Do not
    # remove a file if it matches the target file name, because it will
    # be efficiently updated by rsync.
    file_path_pattern = os.path.join(target_directory, 'initrd*')
    file_utilities.delete_files_with_pattern(file_path_pattern, [target_file_path])

    # Copy the new initrd file.
    try:
        _copy_kernel_file(source_file_path, target_file_path, user, file_number=1, total_files=2)
    except InterruptException as exception:
        # displayer.update_label('generate_page__copy_boot_files_message', '<span foreground="red">Error. Unable to update the initrd boot file.</span>')
        message = 'Error. Unable to update the initrd boot file.'
        displayer.update_label('generate_page__copy_boot_files_message', message, True)
        displayer.update_status('generate_page__copy_boot_files', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        # displayer.update_label('generate_page__copy_boot_files_message', '<span foreground="red">Error. Unable to update the initrd boot file.</span>')
        message = 'Error. Unable to update the initrd boot file.'
        displayer.update_label('generate_page__copy_boot_files_message', message, True)
        displayer.update_status('generate_page__copy_boot_files', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)
    '''
    # Workaround for Ubuntu 23.04+ (Lunar).
    # Tested 7/12/2024, and this workaround was not required.
    # Create a symlink from initrd to initrd.*.
    directory_path = target_directory
    file_name = target_file_name
    link_name = 'initrd'
    logger.log_value('For Ubuntu 23.04+, create link', f'from {link_name} to {file_name} in {directory_path}')
    file_utilities.create_link(directory_path, file_name, link_name)
    '''

    # Workaround for Pop!_OS.
    # Create a symlink from initrd.gz to initrd.*.
    # Workaround for Bug #1900917, "Kernel Panic on Boot After
    # Installation (No initrd in grub.cfg)."
    # Reference Bug #1898749, "Pop!_OS expects vmlinuz on the ISO to
    # have the *.efi extension."
    # Reference Bug #1895770, "Pop!_OS expects the initramfs bootstrap
    # file to be explicitly named "initrd.gz"
    is_pop_os_based = constructor.os_is_distribution('pop', model.project.custom_root_directory)
    if is_pop_os_based:
        directory_path = target_directory
        file_name = target_file_name
        link_name = 'initrd.gz'
        logger.log_value('For Pop!_OS, create link', f'from {link_name} to {file_name} in {directory_path}')
        file_utilities.create_link(directory_path, file_name, link_name)

    message = 'Success.'
    displayer.update_label('generate_page__copy_boot_files_message', message, False)
    displayer.update_status('generate_page__copy_boot_files', OK)
    return False  # (No error)


def _copy_kernel_file(source_file_path, target_file_path, user, file_number, total_files):
    """
    Raises exception.
    """

    # TODO: Can this function be consolidated outside this module?

    logger.log_label(f'Copy file number {file_number+1} of {total_files}')

    logger.log_value('The source file path is', source_file_path)
    logger.log_value('The target file path is', target_file_path)

    program = os.path.join(model.application.directory, 'commands', 'copy-path')
    command = ['pkexec', program, source_file_path, target_file_path, user]

    # The progress callback function.
    def progress_callback(percent):
        total_percent = (FINAL_PERCENT * file_number + percent) / total_files
        displayer.update_progress_bar_percent('generate_page__copy_boot_files_progress_bar', total_percent)
        if total_percent % 10 == 0:
            logger.log_value('Completed', f'{total_percent:n}%')

    track_progress(command, progress_callback)


# ----------------------------------------------------------------------
# Create Squashfs Functions
# ----------------------------------------------------------------------


def create_squashfs():

    logger.log_label('Compress the Linux file system')

    directory = model.layout.squashfs_directory

    if model.layout.minimal_squashfs_file_name:
        file_name = model.layout.minimal_squashfs_file_name
    else:
        file_name = model.layout.squashfs_file_name

    source_file_path = model.project.custom_root_directory
    logger.log_value('The source file path is', source_file_path)

    target_file_path = os.path.join(model.project.custom_disk_directory, directory, file_name)
    logger.log_value('The target file path is', target_file_path)

    message = f'Using {model.options.compression} compression.'
    displayer.update_label('generate_page__create_squashfs_message', message, False)

    # Create the standard squashfs file, such as:
    # • filesystem.squashfs
    # • minimal.standard.squashfs
    # • ubuntu-server-minimal.ubuntu-server.squashfs
    # • etc.

    # Pkexec is required.
    program = os.path.join(model.application.directory, 'commands', 'compress-root')
    command = ['pkexec', program, source_file_path, target_file_path, model.options.compression]

    # Show % in progress by setting text to None.
    # displayer.update_progress_bar_text('generate_page__create_squashfs_progress_bar', None)
    displayer.update_progress_bar_text('generate_page__create_squashfs_progress_bar', f'0.0{GAP}%')

    # The progress callback function.
    def progress_callback(percent):
        displayer.update_progress_bar_text('generate_page__create_squashfs_progress_bar', f'{locale.format_string("%.1f", percent, True)}{GAP}%')
        displayer.update_progress_bar_percent('generate_page__create_squashfs_progress_bar', percent)
        if percent % 10 == 0:
            logger.log_value('Completed', f'{percent:n}%')

    try:
        track_progress(command, progress_callback)
    except InterruptException as exception:
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to create the compressed Linux file system.</span>'
            message = 'Error. Unable to create the compressed Linux file system.'
        displayer.update_label('generate_page__create_squashfs_message', message, True)
        displayer.update_status('generate_page__create_squashfs', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        if 'No space left on device' in str(exception):
            # message = '<span foreground="red">Error. Not enough space on the disk.</span>'
            message = 'Error. Not enough space on the disk.'
        else:
            # message = '<span foreground="red">Error. Unable to create the compressed Linux file system.</span>'
            message = 'Error. Unable to create the compressed Linux file system.'
        displayer.update_label('generate_page__create_squashfs_message', message, True)
        displayer.update_status('generate_page__create_squashfs', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # TODO:
    # Remove this *comment* in the future. [2024-08-10]
    #
    # In Cubic version 2024.02.86, minimal squashfs is generated, and
    # standard squashfs is copied from the original ISO.
    # In Cubic version 2024.08.87, minimal squashfs is generated, and
    # standard squashfs must be a link to this file.
    # Therefore, delete standard squashfs, if it exists, and create the
    # link.
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

    # Create a link to minimal_squashfs_file_name from standard_squashfs_file_name.
    if model.layout.minimal_squashfs_file_name:
        directory_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory)
        file_name = model.layout.minimal_squashfs_file_name
        link_name = model.layout.standard_squashfs_file_name
        _, _, signal_status = file_utilities.create_link(directory_path, file_name, link_name)
        if signal_status:
            # logger.log_value('Error. Unable to create link', f'{link_name} to {file_name}')
            message = 'Error. Unable to link to the standard Linux file system.'
            displayer.update_label('generate_page__create_squashfs_message', message, True)
            displayer.update_status('generate_page__create_squashfs', ERROR)
            return True  # (Error)
    '''
    ### TODO: TESTING
    # Create a link to minimal_squashfs_file_name from installer_squashfs_file_name.
    if model.layout.minimal_squashfs_file_name:
        directory_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory)
        file_name = model.layout.minimal_squashfs_file_name
        link_name = model.layout.installer_squashfs_file_name
        _, _, signal_status = file_utilities.create_link(directory_path, file_name, link_name)
        if signal_status:
            # logger.log_value('Error. Unable to create link', f'{link_name} to {file_name}')
            message = 'Error. Unable to link to the standard Linux file system.'
            displayer.update_label('generate_page__create_squashfs_message', message, True)
            displayer.update_status('generate_page__create_squashfs', ERROR)
            return True  # (Error)
    '''
    '''
    ### TODO: TESTING
    # Create a link to minimal_squashfs_file_name from installer_generic_squashfs_file_name.
    if model.layout.minimal_squashfs_file_name:
        directory_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory)
        file_name = model.layout.minimal_squashfs_file_name
        link_name = model.layout.installer_generic_squashfs_file_name
        _, _, signal_status = file_utilities.create_link(directory_path, file_name, link_name)
        if signal_status:
            # logger.log_value('Error. Unable to create link', f'{link_name} to {file_name}')
            message = 'Error. Unable to link to the standard Linux file system.'
            displayer.update_label('generate_page__create_squashfs_message', message, True)
            displayer.update_status('generate_page__create_squashfs', ERROR)
            return True  # (Error)
    '''

    message = 'Success.'
    displayer.update_label('generate_page__create_squashfs_message', message, False)
    displayer.update_status('generate_page__create_squashfs', OK)
    return False  # (No error)


def create_squashfs_TESTING_1():
    """
    This function does nothing.
    """

    logger.log_label('Create squashfs (Testing)')

    directory = model.layout.squashfs_directory

    if model.layout.minimal_squashfs_file_name:
        file_name = model.layout.minimal_squashfs_file_name
    else:
        file_name = model.layout.squashfs_file_name

    source_file_path = model.project.custom_root_directory
    logger.log_value('The source file path is', source_file_path)

    target_file_path = os.path.join(model.project.custom_disk_directory, directory, file_name)
    logger.log_value('The target file path is', target_file_path)

    message = 'Testing.'
    displayer.update_label('generate_page__create_squashfs_message', message, False)
    displayer.update_status('generate_page__create_squashfs', OK)
    return False  # (No error)


def create_squashfs_TESTING_2():
    """
    This function simply copies the original filesystem.squashfs file or
    the ubuntu-server-minimal.ubuntu-server.squashfs file.
    """

    logger.log_label('Create squashfs (Testing)')

    directory = model.layout.squashfs_directory

    if model.layout.minimal_squashfs_file_name:
        file_name = model.layout.minimal_squashfs_file_name
    else:
        file_name = model.layout.squashfs_file_name

    source_file_path = model.project.custom_root_directory
    logger.log_value('The source file path is', source_file_path)

    target_file_path = os.path.join(model.project.custom_disk_directory, directory, file_name)
    logger.log_value('The target file path is', target_file_path)

    # Copy the original filesystem.squashfs or
    # ubuntu-server-minimal.ubuntu-server.squashfs.
    file_utilities.copy_file(source_file_path, target_file_path)

    if not os.path.exists(target_file_path):
        message = f'Testing. Error. {file_name} already exists.'
        displayer.update_label('generate_page__create_squashfs_message', message, True)
        displayer.update_status('generate_page__create_squashfs', ERROR)
        return True  # (Error)

    message = 'Testing.'
    displayer.update_label('generate_page__create_squashfs_message', message, False)
    displayer.update_status('generate_page__create_squashfs', OK)
    return False  # (No error)


def create_squashfs_TESTING_3():
    """
    This function displays a progress from 0 to 1,000.
    """

    logger.log_label('Create squashfs (Testing)')

    total_files = 1000
    for file_number in range(0, 1000):
        percent = 100 * file_number / total_files
        displayer.update_progress_bar_percent('generate_page__create_squashfs_progress_bar', percent)
        displayer.update_progress_bar_text('generate_page__create_squashfs_progress_bar', f'Processing {file_number:n} of {total_files:n}')
        time.sleep(SLEEP_0500_MS)

    displayer.update_status('generate_page__create_squashfs', OK)
    return False  # (No error)


# ----------------------------------------------------------------------
# Update File System Size Functions
# ----------------------------------------------------------------------


def update_file_system_size():

    logger.log_label('Update the file system size')

    # The file system size files appear on various ISOs as follows:
    # • standard_size_file_name............ Desktop, Server
    # • minimal_size_file_name............. Desktop, Server
    # • installer_size_file_name........... Desktop, Server
    # • installer_generic_size_file_name... Server only
    # • size_file_name..................... Desktop, Server

    size_1_in_bytes = 0  # Customized file system size
    size_2_in_bytes = 0  # Installer file system size
    size_3_in_bytes = 0  # Generic installer file system size
    size_4_in_bytes = 0  # File system size

    # Calculate the customized file system size.
    try:
        # Pkexec is required.
        program = os.path.join(model.application.directory, 'commands', 'file-size')
        command = ['pkexec', program, model.project.custom_root_directory]
        result, exit_status, signal_status = execute_synchronous(command)
        size_1_information = re.search(r'^([0-9]+)\s', result)
        size_1_in_bytes = int(size_1_information.group(1))
        size_1_in_mib = size_1_in_bytes / MIB
        size_1_in_gib = size_1_in_bytes / GIB
        logger.log_value('The customized Linux file system size is', f'{locale.format_string("%.2f", size_1_in_gib, True)} GiB ({size_1_in_bytes:n} bytes)')
    except InterruptException as exception:
        logger.log_value('Unable to get the customized file system size for', model.project.custom_root_directory)
        logger.log_value('The exception is', exception)
        message = 'Error. Unable to get the customized file system size.'
        displayer.update_label('generate_page__update_file_system_size_message', message, True)
        displayer.update_status('generate_page__update_file_system_size', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Unable to get the customized file system size for', model.project.custom_root_directory)
        logger.log_value('The exception is', exception)
        message = 'Error. Unable to get the customized file system size.'
        displayer.update_label('generate_page__update_file_system_size_message', message, True)
        displayer.update_status('generate_page__update_file_system_size', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    # Calculate the installer file system size.
    if model.layout.installer_size_file_name:
        file_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory, model.layout.installer_size_file_name)
        size_2_in_bytes = int(file_utilities.read_file(file_path))
        size_2_in_mib = size_2_in_bytes / MIB
        size_2_in_gib = size_2_in_bytes / GIB
        logger.log_value('The installer Linux file system size is', f'{locale.format_string("%.2f", size_2_in_gib, True)} GiB ({size_2_in_bytes:n} bytes)')

    # Calculate the generic installer file system size.
    if model.layout.installer_generic_size_file_name:
        file_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory, model.layout.installer_generic_size_file_name)
        size_3_in_bytes = int(file_utilities.read_file(file_path))
        size_3_in_mib = size_3_in_bytes / MIB
        size_3_in_gib = size_3_in_bytes / GIB
        logger.log_value(
            'The generic installer Linux file system size is',
            f'{locale.format_string("%.2f", size_3_in_gib, True)} GiB ({size_3_in_bytes:n} bytes)')

    # Calculate the file system size.
    size_4_in_bytes = size_1_in_bytes + \
                      size_2_in_bytes + \
                      size_3_in_bytes
    size_4_in_mib = size_4_in_bytes / MIB
    size_4_in_gib = size_4_in_bytes / GIB
    model.file_system_size = size_4_in_bytes
    logger.log_value('The Linux file system size is', f'{locale.format_string("%.2f", size_4_in_gib, True)} GiB ({size_4_in_bytes:n} bytes)')
    if size_4_in_bytes > GIB:
        message = f' The Linux file system size is {locale.format_string("%.2f", size_4_in_gib, True)} GiB ({size_4_in_bytes:n} bytes).'
    else:
        message = f' The Linux file system size is {locale.format_string("%.2f", size_4_in_mib, True)} MiB ({size_4_in_bytes:n} bytes).'

    # Write the minimal file system size.
    if model.layout.minimal_size_file_name:
        try:
            file_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory, model.layout.minimal_size_file_name)
            file_utilities.write_line(str(size_1_in_bytes), file_path)
        except InterruptException as exception:
            logger.log_value('Unable to write the minimal file system size in', file_path)
            logger.log_value('The exception is', exception)
            message = 'Error. Unable to save the minimal file system size.'
            displayer.update_label('generate_page__update_file_system_size_message', message, True)
            displayer.update_status('generate_page__update_file_system_size', ERROR)
            logger.log_value('Do not propagate exception', exception)
            raise exception
        except Exception as exception:
            logger.log_value('Unable to write the minimal file system size in', file_path)
            logger.log_value('The exception is', exception)
            message = 'Error. Unable to save the minimal file system size.'
            displayer.update_label('generate_page__update_file_system_size_message', message, True)
            displayer.update_status('generate_page__update_file_system_size', ERROR)
            logger.log_value('Do not propagate exception', exception)
            return True  # (Error)

    # Write the standard file system size.
    if model.layout.standard_size_file_name:

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # TODO:
        # Remove this *comment* in the future. [2024-08-10]
        #
        # In Cubic version 2024.02.86, minimal size is generated, and
        # standard size is copied from the original ISO.
        # In Cubic version 2024.08.87, minimal size is generated, and
        # standard size must be a link to this file.
        # Therefore, delete standard size, if it exists, and create the
        # link.
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

        # Create a link from standard_size_file_name to minimal_size_file_name.
        # Assume minimal_size_file_name exists.
        directory_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory)
        file_name = model.layout.minimal_size_file_name
        link_name = model.layout.standard_size_file_name
        _, _, signal_status = file_utilities.create_link(directory_path, file_name, link_name)
        if signal_status:
            # logger.log_value('Error. Unable to create link', f'{link_name} to {file_name}')
            message = 'Error. Unable to link to the minimal file system size.'
            displayer.update_label('generate_page__update_file_system_size_message', message, True)
            displayer.update_status('generate_page__update_file_system_size', ERROR)
            return True  # (Error)

    # Write the file system size.
    if model.layout.size_file_name:
        try:
            file_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory, model.layout.size_file_name)
            file_utilities.write_line(str(size_4_in_bytes), file_path)
        except InterruptException as exception:
            logger.log_value('Unable to write file system size in', file_path)
            logger.log_value('The exception is', exception)
            message = 'Error. Unable to save file system size.'
            displayer.update_label('generate_page__update_file_system_size_message', message, True)
            displayer.update_status('generate_page__update_file_system_size', ERROR)
            logger.log_value('Propagate exception', exception)
            raise exception
        except Exception as exception:
            logger.log_value('Unable to write file system size in', file_path)
            logger.log_value('The exception is', exception)
            message = 'Error. Unable to save file system size.'
            displayer.update_label('generate_page__update_file_system_size_message', message, True)
            displayer.update_status('generate_page__update_file_system_size', ERROR)
            logger.log_value('Do not propagate exception', exception)
            return True  # (Error)

    displayer.update_label('generate_page__update_file_system_size_message', message, False)
    displayer.update_status('generate_page__update_file_system_size', OK)
    return False  # (No error)


# ----------------------------------------------------------------------
# Update Disk and Installer Information Functions
# ----------------------------------------------------------------------


def update_disk_and_installer_info():

    # Update the disk name.

    try:
        _update_disk_name()
    except InterruptException as exception:
        logger.log_value('Unable to update the disk name to', model.custom.iso_disk_name)
        message = 'Error. Unable to update the disk name.'
        displayer.update_label('generate_page__update_disk_and_installer_info_message', message, True)
        displayer.update_status('generate_page__update_disk_and_installer_info', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Unable to update the disk name to', model.custom.iso_disk_name)
        message = 'Error. Unable to update the disk name.'
        displayer.update_label('generate_page__update_disk_and_installer_info_message', message, True)
        displayer.update_status('generate_page__update_disk_and_installer_info', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    # Update the disk information.

    try:
        _update_disk_info()
    except InterruptException as exception:
        logger.log_value('Unable to update the disk name to', model.custom.iso_disk_name)
        message = 'Error. Unable to update the disk name.'
        displayer.update_label('generate_page__update_disk_and_installer_info_message', message, True)
        displayer.update_status('generate_page__update_disk_and_installer_info', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Unable to update the disk name to', model.custom.iso_disk_name)
        message = 'Error. Unable to update the disk name.'
        displayer.update_label('generate_page__update_disk_and_installer_info_message', message, True)
        displayer.update_status('generate_page__update_disk_and_installer_info', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    # Update the installer sources file.

    try:
        _update_installer_sources_file()
    except InterruptException as exception:
        logger.log_value('Unable to update the installer sources in', model.layout.installer_sources_file_name)
        message = 'Error. Unable to update the installer sources.'
        displayer.update_label('generate_page__update_disk_and_installer_info_message', message, True)
        displayer.update_status('generate_page__update_disk_and_installer_info', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Unable to update the installer sources to', model.layout.installer_sources_file_name)
        message = 'Error. Unable to update the installer sources.'
        displayer.update_label('generate_page__update_disk_and_installer_info_message', message, True)
        displayer.update_status('generate_page__update_disk_and_installer_info', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    message = 'Success.'
    displayer.update_label('generate_page__update_disk_and_installer_info_message', message, False)
    displayer.update_status('generate_page__update_disk_and_installer_info', OK)
    return False  # (No error)


def _update_disk_name():
    """
    Raises exception.
    """

    logger.log_label('Update the disk name')

    file_path = os.path.join(model.project.custom_disk_directory, 'README.diskdefines')

    # Read the original file if it exists.
    lines = []
    if os.path.isfile(file_path):
        logger.log_value('The existing file will be updated', file_path)
        lines = file_utilities.read_lines(file_path)
    else:
        logger.log_value('A new file will be created', file_path)

    # Create the new lines.
    new_lines = []
    # Append the new disk name line.
    line = f'#define DISKNAME  {model.custom.iso_disk_name}'
    new_lines.append(line)
    logger.log_value('Update disk name', line)
    # Append the new disk note line.
    display_version = constructor.get_display_version(model.application.cubic_version)
    # Use the modify date from the model.
    line = f'#define DISKNOTE  Generated using Cubic version {display_version} on {model.project.modify_date} based on {model.original.iso_file_name}'
    new_lines.append(line)
    logger.log_value('Update disk note', line)
    # Append only existing lines that should be retained.
    for line in lines:
        if 'DISKNAME' in line:
            # Exclude old disk name line.
            pass
        elif 'DISKNOTE' in line:
            # Exclude old disk note line.
            pass
        elif 'CUBIC_INFO' in line:
            # TODO: Remove this block in a future release (2012-12-11).
            pass
        else:
            # Retain existing line.
            new_lines.append(line.strip())

    # Create a new README.diskdefines file.
    file_utilities.write_lines(new_lines, file_path)


def _update_disk_info():
    """
    Raises exception.
    """

    logger.log_label('Update the disk information')

    # Use the modify date from the model.
    time_stamp = constructor.reformat_time_stamp(model.project.modify_date, TIME_STAMP_FORMAT_YYYYMMDD)
    line = f'{model.custom.iso_disk_name} ({time_stamp})'
    logger.log_value('The custom disk image name and release date are', line)
    file_path = os.path.join(model.project.custom_disk_directory, '.disk', 'info')
    file_utilities.write_line(line, file_path)


def _update_installer_sources_file():
    """
    Update the installer sources yaml file. Set the minimal install as
    default.

    Returns:
    : None

    Raises:
    : Exception
        The exception that occurred.
    """

    if model.layout.installer_sources_file_name:

        logger.log_label('Update the installer sources configuration')

        file_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory, model.layout.installer_sources_file_name)
        logger.log_value('File path', file_path)

        yaml_list = file_utilities.read_yaml_file(file_path)
        logger.log_value('Current configuration', yaml_list)

        # Make the minimal squashfs file default. Do not use the
        # standard squashfs file because it does not work for the
        # installer.
        yaml_list = _update_installer_sources_yaml(yaml_list, model.layout.minimal_squashfs_file_name)
        logger.log_value('Updated configuration', yaml_list)

        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
        # Note: Remember to exclude the backup file from md5sum.txt in
        #       the update_checksums() function.
        # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

        # Backup the original file.
        if not os.path.exists(f'{file_path}.original'):
            file_utilities.copy_file(file_path, f'{file_path}.original')

        # Save the file.
        file_utilities.save_yaml_file(yaml_list, file_path)


def _update_installer_sources_yaml(yaml_list, path):
    """
    Create a new yaml configuration using information from the supplied
    configuration and using values from this project.
    
    Update the following values:
    • default - Set to true
    • description - Use the custom ISO release name
    • locale support - Change to none
    • name - Use the custom ISO volume ID
    • size - Use the calculated file system size

    Here is an example configuration:
      - default: true
        description:
          en: Custom Noble Numbat
        id: ubuntu-server-minimal
        locale_support: none
        name:
          en: Ubuntu-Server 24.04.0 2024.08.09
        path: ubuntu-server-minimal.squashfs
        size: 2430492672
        type: fsimage
        variant: server

    Arguments:
    yaml_list : list of dict
        The supplied configuration.
    path : str
        Used to select the section from the supplied yaml configuration
        that will be used as the basis of the new configuration.

    Returns:
    new_yaml_list: list of dict
        The updated yam configuration.

    Raises:
    : Exception
        The exception that occurred.
    """

    new_yaml_list = []
    new_yaml_dict = {}
    for yaml_dict in yaml_list:
        if yaml_dict['path'] == path:
            new_yaml_dict['default'] = True
            # new_yaml_dict['description'] = yaml_dict['description']
            new_yaml_dict['description'] = {'en': model.custom.iso_release_name}
            new_yaml_dict['id'] = yaml_dict['id']
            # new_yaml_dict['locale_support'] = yaml_dict['locale_support']
            new_yaml_dict['locale_support'] = 'none'  # 'locale-only'
            # new_yaml_dict['name'] = yaml_dict['name']
            new_yaml_dict['name'] = {'en': model.custom.iso_volume_id}
            new_yaml_dict['path'] = yaml_dict['path']
            # new_yaml_dict['size'] = yaml_dict['size']
            new_yaml_dict['size'] = model.file_system_size
            new_yaml_dict['type'] = yaml_dict['type']
            new_yaml_dict['variant'] = yaml_dict['variant']
            new_yaml_list.append(new_yaml_dict)

    return new_yaml_list


# ----------------------------------------------------------------------
# Update Checksums Functions
# ----------------------------------------------------------------------


# TODO: This doesn't use a pexpect process.
#       How do we kill/stop this when back, or quit are clicked?
#       Do we use a flag and/or break in all loops?
def update_checksums():

    # TODO: Should os.path.realpath should be used for?...
    #       1. checksums_file_path
    #       2. exclude_paths

    logger.log_label('Update checksums')

    # Show % in progress by setting text to None.
    displayer.update_progress_bar_text('generate_page__update_checksums_progress_bar', None)

    checksums_file_path = os.path.join(model.project.custom_disk_directory, 'md5sum.txt')
    start_path = model.project.custom_disk_directory

    #
    # Identify file paths to exclude from the checksums.
    #

    exclude_paths = []

    # Exclude the checksums file.
    exclude_paths.append(checksums_file_path)

    # Exclude the eltorito boot image and the boot catalog.

    template = constructor.decode(model.status.iso_template)

    # Exclude the eltorito boot image file path (if it exists).
    result = re.search(r"-b '(.*?)'", template)
    if result:
        file_path = result.group(1).strip(os.path.sep)
        file_path = os.path.join(model.project.custom_disk_directory, file_path)
        exclude_paths.append(file_path)

    # Exclude the boot catalog file path (if it exists).
    result = re.search(r"-c '(.*?)'", template)
    if result:
        file_path = result.group(1).strip(os.path.sep)
        file_path = os.path.join(model.project.custom_disk_directory, file_path)
        exclude_paths.append(file_path)

    # Exclude the minimal remove file if the minimal install option was
    # not selected.
    # Exclude file paths must be full file paths.
    if model.layout.minimal_remove_file_name and not model.options.has_minimal_install:
        # Exclude the filesystem.manifest-minimal-remove.
        file_path = os.path.join(                \
            model.project.custom_disk_directory, \
            model.layout.squashfs_directory,     \
            model.layout.minimal_remove_file_name)
        exclude_paths.append(file_path)

    # Exclude the installer sources backup file if present.
    if model.layout.installer_sources_file_name:
        file_path = os.path.join(                                 \
            model.project.custom_disk_directory,                  \
            model.layout.squashfs_directory,                      \
            f'{model.layout.installer_sources_file_name}.original')
        exclude_paths.append(file_path)

    logger.log_value('Exclude files from the checksum', exclude_paths)

    #
    # Get file paths to include in the checksums.
    #

    file_paths = file_utilities.get_relative_file_paths(start_path, exclude_paths)
    file_paths.sort(key=lambda file_path: file_path.lower())

    total_files = len(file_paths)
    if total_files == 0:
        logger.log_value('Unable to update checksums. No files found in', checksums_file_path)
        message = 'Error. Unable to calculate checksums.'
        displayer.update_label('generate_page__update_checksums_message', message, True)
        displayer.update_status('generate_page__update_checksums', ERROR)
        return True  # (Error)

    #
    # Update checksums and display progress.
    #

    # https://docs.python.org/3/library/functions.html#open
    #
    # r   Open text file for reading. The stream is positioned at the
    #     beginning of the file.
    #
    # r+  Open for reading and writing. The stream is positioned at the
    #     beginning of the file.
    #
    # w   Truncate file to zero length or create text file for writing.
    #     The stream is positioned at the beginning of the file.
    #
    # w+  Open for reading and writing. The file is created if it does
    #     not exist, otherwise it is truncated. The stream is positioned
    #     at the beginning of the file.
    #
    # a   Open for writing. The file is created if it does not exist.
    #     The stream is positioned at the end of the file.  Subsequent
    #     writes to the file will always end up at the then current end
    #     of file, irrespective of any intervening fseek(3) or similar.
    #
    # a+  Open for reading and writing. The file is created if it does
    #     not exist. The stream is positioned at the end of the file.
    #     Subsequent writes to the file will always end up at the then
    #     current end of file, irrespective of any intervening fseek(3)
    #     or similar.

    try:
        logger.log_value('Write to file', checksums_file_path)
        line_separator = ''
        with open(checksums_file_path, 'w') as file:
            for file_number, file_path in enumerate(file_paths, start=1):
                displayer.update_progress_bar_text(
                    'generate_page__update_checksums_progress_bar',
                    f'Calculating checksum for file {file_number:n} of {total_files:n}')
                try:
                    checksum, file_path = file_utilities.calculate_md5_hash(file_path, start_path)
                    if checksum:
                        file.write(f'{line_separator}{checksum}  ./{file_path}')
                        line_separator = os.linesep
                except FileNotFoundError as exception:
                    logger.log_value('Skipping file', file_path)
                percent = 100 * file_number / total_files
                displayer.update_progress_bar_percent('generate_page__update_checksums_progress_bar', percent)
    except InterruptException as exception:
        logger.log_value('Error', 'Unable to update checksums')
        logger.log_value('The exception is', exception)
        if 'No space left on device' in str(exception):
            message = 'Error. Not enough space on the disk.'
        else:
            message = 'Error. Unable to calculate checksums.'
        displayer.update_label('generate_page__update_checksums_message', message, True)
        displayer.update_status('generate_page__update_checksums', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Error', 'Unable to update checksums')
        logger.log_value('The exception is', exception)
        if 'No space left on device' in str(exception):
            message = 'Error. Not enough space on the disk.'
        else:
            message = 'Error. Unable to calculate checksums.'
        displayer.update_label('generate_page__update_checksums_message', message, True)
        displayer.update_status('generate_page__update_checksums', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    logger.log_value('Calculated checksums for', f'{total_files} files')
    displayer.update_progress_bar_text('generate_page__update_checksums_progress_bar', '100%')
    message = f'Calculated checksums for {total_files} files.'
    displayer.update_label('generate_page__update_checksums_message', message, False)
    displayer.update_status('generate_page__update_checksums', OK)
    return False  # (No error)


# ----------------------------------------------------------------------
# Check Disk Size Functions
# ----------------------------------------------------------------------


def check_custom_disk_directory_size():

    logger.log_label('Get the custom disk size')

    try:
        # Pkexec is not required.
        program = os.path.join(model.application.directory, 'commands', 'file-size')
        command = ['pkexec', program, model.project.custom_disk_directory]
        result, exit_status, signal_status = execute_synchronous(command)
        size_information = re.search(r'^([0-9]+)\s', result)
        size_in_bytes = int(size_information.group(1))
        size_in_mib = size_in_bytes / MIB
        size_in_gib = size_in_bytes / GIB
    except InterruptException as exception:
        logger.log_value('Unable to get the total size', model.project.custom_disk_directory)
        logger.log_value('The exception is', exception)
        message = 'Error. Unable to get the total size.'
        displayer.update_label('generate_page__check_custom_disk_size_message', message, True)
        displayer.update_status('generate_page__check_custom_disk_size', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Unable to get the total size', model.project.custom_disk_directory)
        logger.log_value('The exception is', exception)
        message = 'Error. Unable to get the total size.'
        displayer.update_label('generate_page__check_custom_disk_size_message', message, True)
        displayer.update_status('generate_page__check_custom_disk_size', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    logger.log_value('The total size is', f'{locale.format_string("%.2f", size_in_gib, True)} GiB ({size_in_bytes:n} bytes)')

    logger.log_value('The maximum size limit for all files on the disk is', f'{MAXIMUM_DISK_SIZE_GIB:.2f} GiB ({MAXIMUM_DISK_SIZE_BYTES:n} bytes)')
    if size_in_bytes > MAXIMUM_DISK_SIZE_BYTES:
        logger.log_value('Error', 'The total size exceeds the maximum size')
        message = (
            f'The the custom disk directory size is {locale.format_string("%.2f", size_in_gib, True)} GiB ({size_in_bytes:n} bytes).{os.linesep}'
            f'This is larger than the {MAXIMUM_DISK_SIZE_GIB:.2f} GiB ({MAXIMUM_DISK_SIZE_BYTES:n} bytes) limit.{os.linesep}'
            f'Click the Back button, and reduce the size of the Linux file system.')
        displayer.update_label('generate_page__check_custom_disk_size_message', message, True)
        displayer.update_status('generate_page__check_custom_disk_size', ERROR)
        return True  # (Error)

    if size_in_bytes > GIB:
        message = f'The total size of all files is {locale.format_string("%.2f", size_in_gib, True)} GiB ({size_in_bytes:n} bytes).'
    else:
        message = f'The total size of all files is {locale.format_string("%.2f", size_in_mib, True)} MiB ({size_in_bytes:n} bytes).'
    displayer.update_label('generate_page__check_custom_disk_size_message', message, False)
    displayer.update_status('generate_page__check_custom_disk_size', OK)
    return False  # (No error)


# ----------------------------------------------------------------------
# Create Disk Image Functions
# ----------------------------------------------------------------------
'''
https://askubuntu.com/questions/1289400/remaster-installation-image-for-ubuntu-20-10
https://unix.stackexchange.com/users/135084/thomas-schmitt
https://stackoverflow.com/questions/60731231/xorriso-boot-catalog-and-eltorito-catalog-not-working
https://askubuntu.com/questions/457528/how-do-i-create-an-efi-bootable-iso-of-a-customized-version-of-ubuntu

1. Exclude every folder under boot/grub
2. Exclude the entire EFI folder
3. Exclude the file boot.catalog
'''


def create_iso_image():

    #
    # Create disk image.
    #

    logger.log_label('Create disk image')

    # Get the correct xorriso command.
    command = _get_xorriso_command()

    # Show % in progress by setting text to None.
    # displayer.update_progress_bar_text('generate_page__create_iso_image_progress_bar', None)
    displayer.update_progress_bar_text('generate_page__create_iso_image_progress_bar', f'0.0{GAP}%')

    # The progress callback function.
    def progress_callback(percent):
        displayer.update_progress_bar_percent('generate_page__create_iso_image_progress_bar', percent)
        displayer.update_progress_bar_text('generate_page__create_iso_image_progress_bar', f'{locale.format_string("%.1f", percent, True)}{GAP}%')
        if percent % 10 == 0:
            logger.log_value('Completed', f'{percent:n}%')

    try:
        track_progress(command, progress_callback, working_directory=model.project.custom_disk_directory)
    except InterruptException as exception:
        if 'exceeds free space on media' in str(exception):
            message = 'Error. Not enough space on the disk.'
        else:
            message = 'Error. Unable to create the customized disk image.'
        displayer.update_label('generate_page__create_iso_image_message', message, True)
        displayer.update_status('generate_page__create_iso_image', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        if 'exceeds free space on media' in str(exception):
            message = 'Error. Not enough space on the disk.'
        else:
            message = 'Error. Unable to create the customized disk image.'
        displayer.update_label('generate_page__create_iso_image_message', message, True)
        displayer.update_status('generate_page__create_iso_image', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    #
    # Get the size.
    #

    logger.log_label('Get the custom disk size')

    iso_file_path = os.path.join(model.custom.iso_directory, model.custom.iso_file_name)
    try:
        # Pkexec is not required.
        program = os.path.join(model.application.directory, 'commands', 'file-size')
        command = ['pkexec', program, iso_file_path]
        result, exit_status, signal_status = execute_synchronous(command)
        size_information = re.search(r'^([0-9]+)\s', result)
        size_in_bytes = int(size_information.group(1))
        size_in_mib = size_in_bytes / MIB
        size_in_gib = size_in_bytes / GIB
        model.iso_file_size = size_in_bytes
    except InterruptException as exception:
        logger.log_value('Unable to get the size of the custom disk', iso_file_path)
        logger.log_value('The exception is', exception)
        message = 'Error. Unable to get the size of the custom disk.'
        displayer.update_label('generate_page__create_iso_image_message', message, True)
        displayer.update_status('generate_page__create_iso_image', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        logger.log_value('Unable to get the size of the custom disk', iso_file_path)
        logger.log_value('The exception is', exception)
        message = 'Error. Unable to get the size of the custom disk.'
        displayer.update_label('generate_page__create_iso_image_message', message, True)
        displayer.update_status('generate_page__create_iso_image', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    if size_in_bytes > GIB:
        logger.log_value('The size of the custom disk is', f'{locale.format_string("%.2f", size_in_gib, True)} GiB ({size_in_bytes:n} bytes)')
        message = f'Generated {model.custom.iso_file_name}. The disk image size is {locale.format_string("%.2f", size_in_gib, True)} GiB.'
        displayer.update_label('generate_page__create_iso_image_message', message, False)
    else:
        logger.log_value('The size of the custom disk is', f'{locale.format_string("%.2f", size_in_mib, True)} MiB ({size_in_bytes:n} bytes)')
        message = f'Generated {model.custom.iso_file_name}. The disk image size is {locale.format_string("%.2f", size_in_mib, True)} MiB.'
        displayer.update_label('generate_page__create_iso_image_message', message, False)

    displayer.update_status('generate_page__create_iso_image', OK)
    return False  # (No error)


# ----------------------------------------------------------------------
# Get Xorriso Command Functions
# ----------------------------------------------------------------------


def _get_xorriso_command():

    template = constructor.decode(model.status.iso_template)

    # In the xorriso command, the volume_id and boot_image_directory
    # must be single quoted bash strings. Because these values may
    # internally contain single quote characters, escape each single
    # quote character (') by replacing it with the sequence '"'"'.
    # This sequence is defied as:
    #   ' = terminate the original single quoted bash string
    #   " = start a new double quoted bash string
    #   ' = apply the single quite character
    #   " = terminate the new double quoted bash string
    #   ' = restart the original single quoted bash string
    # Note, the triple quotes below delineate the python string.
    volume_id = model.custom.iso_volume_id.replace("'", """'"'"'""")
    boot_image_directory = model.project.directory.replace("'", """'"'"'""")

    complete_template = template.format(volume_id=volume_id, boot_image_directory=boot_image_directory)
    iso_file_path = os.path.join(model.custom.iso_directory, model.custom.iso_file_name)

    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # Note: Remember to exclude these files from md5sum.txt in the
    #       update_checksums() function.
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

    # Exclude the minimal remove file if the minimal install option was
    # not selected.
    if model.layout.minimal_remove_file_name and not model.options.has_minimal_install:
        file_path = os.path.join(                \
            model.layout.squashfs_directory,     \
            model.layout.minimal_remove_file_name)
        exclude_1 = f'-m "{file_path}"'
    else:
        exclude_1 = ''

    # Exclude the installer sources backup file if present.
    if model.layout.installer_sources_file_name:
        file_path = os.path.join(                                 \
            model.project.custom_disk_directory,                  \
            model.layout.squashfs_directory,                      \
            f'{model.layout.installer_sources_file_name}.original')
        exclude_2 = f'-m "{file_path}"'
    else:
        exclude_2 = ''

    command = ('xorriso'                 \
               ' -as mkisofs'            \
               ' -r'                     \
               ' -J'                     \
               ' -joliet-long'           \
               ' -l'                     \
               ' -iso-level 3'           \
               f' {exclude_1}'           \
               f' {exclude_2}'           \
               f' {complete_template}'   \
               f' -o "{iso_file_path}" .')

    return command


# ----------------------------------------------------------------------
# Create Links for Attributes Functions
# ----------------------------------------------------------------------


def create_links_for_attributes():
    """
    If an attribute has more than one valid value, the last file name is
    considered to be the actual file, and prior values should be links
    to this file.
    """

    logger.log_label('Create links for attributes')

    def create_links(attribute, directory_path):
        """
        If an attribute has more than one valid value, the last file
        name is considered to be the actual file, and prior values
        should be links to this file.
        """
        file_names = model.layout.values(attribute, True)
        if len(file_names) > 1:
            file_name = file_names[-1]
            link_names = file_names[:-1]
            for link_name in link_names:
                file_utilities.create_link(directory_path, file_name, link_name)

    # Casper Section
    create_links('casper_directory', model.project.custom_disk_directory)
    directory_path = os.path.join(model.project.custom_disk_directory, model.layout.casper_directory)
    # The initrd file name is never set, so do not create links.
    # create_links('initrd_file_name', directory_path)
    # The vmlinuz file name is never set, so do not create links.
    # create_links('vmlinuz_file_name', directory_path)

    # General Section
    create_links('squashfs_directory', model.project.custom_disk_directory)
    directory_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory)
    create_links('squashfs_file_name', directory_path)
    create_links('manifest_file_name', directory_path)
    create_links('minimal_remove_file_name', directory_path)
    create_links('standard_remove_file_name', directory_path)
    create_links('size_file_name', directory_path)

    # Minimal Section
    create_links('minimal_squashfs_file_name', directory_path)
    create_links('minimal_manifest_file_name', directory_path)
    create_links('minimal_size_file_name', directory_path)

    # Standard Section
    create_links('standard_squashfs_file_name', directory_path)
    create_links('standard_manifest_file_name', directory_path)
    create_links('standard_size_file_name', directory_path)

    # Installer / Live Section
    create_links('installer_sources_file_name', directory_path)
    create_links('installer_squashfs_file_name', directory_path)
    create_links('installer_manifest_file_name', directory_path)
    create_links('installer_size_file_name', directory_path)
    create_links('installer_generic_squashfs_file_name', directory_path)
    create_links('installer_generic_manifest_file_name', directory_path)
    create_links('installer_generic_size_file_name', directory_path)


# ----------------------------------------------------------------------
# Calculate Disk Image Checksum Functions
# ----------------------------------------------------------------------


def calculate_checksum_for_iso():

    logger.log_label('Calculate checksum for ISO')

    model.status.iso_checksum, _ = file_utilities.calculate_md5_hash(model.custom.iso_file_name, model.custom.iso_directory)
    message = f'The checksum is {model.status.iso_checksum}.'
    displayer.update_label('generate_page__calculate_iso_image_checksum_message', message, False)
    time.sleep(SLEEP_0500_MS)

    model.status.iso_checksum_file_name = constructor.construct_custom_iso_checksum_file_name(model.custom.iso_file_name)
    try:
        file_path = os.path.join(model.custom.iso_directory, model.status.iso_checksum_file_name)
        file_utilities.write_line(f'{model.status.iso_checksum}  {model.custom.iso_file_name}', file_path)
    except InterruptException as exception:
        message = f'Unable to save the checksum file {model.status.iso_checksum}.{os.linesep}The checksum file is {model.status.iso_checksum_file_name}.'
        displayer.update_label('generate_page__calculate_iso_image_checksum_message', message, True)
        displayer.update_status('generate_page__calculate_iso_image_checksum', ERROR)
        logger.log_value('Propagate exception', exception)
        raise exception
    except Exception as exception:
        message = f'Unable to save the checksum file {model.status.iso_checksum}.{os.linesep}The checksum file is {model.status.iso_checksum_file_name}.'
        displayer.update_label('generate_page__calculate_iso_image_checksum_message', message, True)
        displayer.update_status('generate_page__calculate_iso_image_checksum', ERROR)
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)

    message = f'The checksum is {model.status.iso_checksum}.{os.linesep}The checksum file is {model.status.iso_checksum_file_name}.'
    displayer.update_label('generate_page__calculate_iso_image_checksum_message', message, False)
    displayer.update_status('generate_page__calculate_iso_image_checksum', OK)
    return False  # (No error)
