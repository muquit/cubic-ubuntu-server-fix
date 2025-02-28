#!/usr/bin/python3

########################################################################
#                                                                      #
# prepare_page.py                                                      #
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

# https://apt-team.pages.debian.net/python-apt/library/index.html

########################################################################
# Imports
########################################################################

# import apt
import collections
import glob
import os
import platform
import re
import string
import time

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
from cubic.constants import SLEEP_0125_MS, SLEEP_0250_MS, SLEEP_0500_MS, SLEEP_1000_MS
from cubic.utilities import constructor
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.processor import execute_synchronous, execute_asynchronous

########################################################################
# Global Variables & Constants
########################################################################

name = 'prepare_page'

INITRAMFS_VERSION_PATTERN = re.compile(r'lib/modules/(\d[\d\.-]*\d)')

# Valid initramfs compression formats are gzip, bzip2, lz4, lzma, lzop,
# or xz, ignoring case. (See /etc/initramfs-tools/initramfs.conf).
INITRAMFS_COMPRESSION_PATTERN = re.compile(r'(?i).*(gzip|bzip2|lz4|lzma|lzop|xz).*')
COMPRESSION_EXTENSIONS = {'gzip': 'gz', 'bzip2': 'bz', 'lz4': 'lz', 'lzma': 'lz', 'lzop': 'lz', 'xz': 'xz'}

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

        # --------------------------------------------------------------
        # Identify disk boot kernels.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__boot_kernels', BULLET)
        displayer.empty_box('prepare_page__boot_kernels_box')

        # --------------------------------------------------------------
        # Identify installed packages.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__installed_packages', BULLET)
        displayer.update_label('prepare_page__installed_packages_message', '...', False)

        # --------------------------------------------------------------
        # Create the removable packages list for a standard install.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__package_manifest_1', BULLET)
        displayer.update_label('prepare_page__package_manifest_1_message', '...', False)

        # --------------------------------------------------------------
        # Create the removable packages list for a minimal install.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__package_manifest_2', BULLET)
        displayer.update_label('prepare_page__package_manifest_2_message', '...', False)

        # --------------------------------------------------------------
        # Save the package manifest.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__save_package_manifest', BULLET)
        displayer.update_label('prepare_page__save_package_manifest_message', '...', False)

        # --------------------------------------------------------------
        # Determine if the Packages page should be skipped.
        # --------------------------------------------------------------

        # The validate function sets the next action.
        validate_page()

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

    if action == 'next':

        # --------------------------------------------------------------
        # Identify disk boot kernels.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__boot_kernels', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        model.kernel_details_list = create_boot_kernel_details_list()
        if model.kernel_details_list:
            displayer.update_status('prepare_page__boot_kernels', OK)
            count = len(model.kernel_details_list)
            logger.log_value('Number of valid disk boot kernels found', count)
            number_text = constructor.number_as_text(count)
            plural_text = constructor.get_plural('kernel', 'kernels', count)
            add_message_to_boot_kernels_box(f'{os.linesep}Found {number_text} valid disk boot {plural_text}.')
        else:
            displayer.update_status('prepare_page__boot_kernels', ERROR)
            logger.log_value('Error. Number of valid disk boot kernels found', 0)
            add_message_to_boot_kernels_box(f'{os.linesep}Error. No valid disk boot kernels were found.')
            add_message_to_boot_kernels_box(
                'To correct this issue, click the Back button and install missing Linux kernel packages on the Terminal page, or select the original disk image on the Project page.'
            )
            return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Identify installed packages.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__installed_packages', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        model.package_details_list = create_package_details_list(model.project.custom_root_directory)
        if model.package_details_list:
            count = len(model.package_details_list)
            logger.log_value('Number of installed packages found', count)
            number_text = constructor.number_as_text(count)
            plural_text = constructor.get_plural('package', 'packages', count)
            message = f'Found {number_text} installed {plural_text}.'
            displayer.update_label('prepare_page__installed_packages_message', message, False)
            displayer.update_status('prepare_page__installed_packages', OK)
        else:
            logger.log_value('Error. Number of installed packages found', 0)
            message = 'Error. No installed packages found.'
            displayer.update_label('prepare_page__installed_packages_message', message, True)
            displayer.update_status('prepare_page__installed_packages', ERROR)
            return  # Stay on this page.
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Create the removable packages list for a standard install.
        # --------------------------------------------------------------

        logger.log_label('Create the removable packages list for a standard install')
        displayer.update_status('prepare_page__package_manifest_1', PROCESSING)
        time.sleep(SLEEP_0500_MS)

        if model.layout.standard_remove_file_name:
            # If the file path does not exist, the packages list will be
            # empty.
            file_path = os.path.join(model.project.custom_disk_directory, \
                                    model.layout.squashfs_directory, \
                                    model.layout.standard_remove_file_name)
            removable_packages_list = file_utilities.read_lines(file_path)
        else:
            removable_packages_list = []
        count = populate_package_details_list_for_standard_install(model.package_details_list, removable_packages_list)
        logger.log_value('Number of installed packages matching standard install list', count)
        number_text = constructor.number_as_text(count)
        plural_text = constructor.get_plural('package', 'packages', count)
        message = f'Identified {number_text} {plural_text} for removal during a standard install.'
        status = OK if model.layout.standard_remove_file_name else OPTIONAL
        displayer.update_label('prepare_page__package_manifest_1_message', message, False)
        displayer.update_status('prepare_page__package_manifest_1', status)
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Create the removable packages list for a minimal install.
        # --------------------------------------------------------------

        logger.log_label('Create the removable packages list for a minimal install')
        displayer.update_status('prepare_page__package_manifest_2', PROCESSING)
        time.sleep(SLEEP_0500_MS)

        if model.layout.minimal_remove_file_name:
            # If the file path does not exist, the packages list will be empty.
            file_path = os.path.join(model.project.custom_disk_directory, \
                                    model.layout.squashfs_directory, \
                                    model.layout.minimal_remove_file_name)
            removable_packages_list = file_utilities.read_lines(file_path)
        else:
            removable_packages_list = []
        count = populate_package_details_list_for_minimal_install(model.package_details_list, removable_packages_list)
        logger.log_value('Number of installed packages matching minimal install list', count)
        number_text = constructor.number_as_text(count)
        plural_text = constructor.get_plural('package', 'packages', count)
        message = f'Identified {number_text} {plural_text} for removal during a minimal install.'
        status = OK if model.options.has_minimal_install else OPTIONAL
        displayer.update_label('prepare_page__package_manifest_2_message', message, False)
        displayer.update_status('prepare_page__package_manifest_2', status)
        time.sleep(SLEEP_0500_MS)

        # --------------------------------------------------------------
        # Save the package manifest.
        # --------------------------------------------------------------

        displayer.update_status('prepare_page__save_package_manifest', PROCESSING)
        time.sleep(SLEEP_0500_MS)
        is_error = save_file_system_manifest_file(model.package_details_list)
        if is_error:
            displayer.update_status('prepare_page__save_package_manifest', ERROR)
            message = 'Unable to save the package manifest file.'
            displayer.update_label('prepare_page__save_package_manifest_message', message, True)
            return  # Stay on this page.
        else:
            displayer.update_status('prepare_page__save_package_manifest', OK)
            message = 'Saved the package manifest file.'
            displayer.update_label('prepare_page__save_package_manifest_message', message, False)
        time.sleep(SLEEP_1000_MS)

        # --------------------------------------------------------------
        # Determine if the Packages page should be skipped.
        # --------------------------------------------------------------

        if model.layout.standard_remove_file_name:
            # Show the Packages page.
            logger.log_value('Show the Packages page?', 'Yes')
            return 'next'
        else:
            # Do not show the Packages page.
            logger.log_value('Show the Packages page?', 'No')
            # Set the minimal install option to False.
            # The Packages page, which sets the minimal install option,
            # will be skipped, so the the minimal install option must be
            # set here.
            model.options.has_minimal_install = False
            return 'next-options'

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

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'next-options':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        # model.project.configuration.save()

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return

    else:

        logger.log_value('Error', f'{BOLD_RED}Unknown action for leave{NORMAL}')

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        iso_utilities.unmount_iso_and_delete_mount_point(model.project.iso_mount_point)

        return 'unknown'


########################################################################
# Handler Functions
########################################################################


def on_size_allocate__prepare_page__boot_kernels_view_port(widget, event, data=None):

    displayer.scroll_view_port_to_bottom('prepare_page__boot_kernels_view_port')


########################################################################
# Support Functions
########################################################################


def add_message_to_boot_kernels_box(message):
    displayer.insert_box_label('prepare_page__boot_kernels_box', message, 0.50)
    time.sleep(SLEEP_0125_MS)


########################################################################
# Linux Kernel Functions
########################################################################

# ----------------------------------------------------------------------
# Kernel Versions
# ----------------------------------------------------------------------

# TODO: Consider using a sorted set so the list doesn't need to be sorted later.


def create_boot_kernel_details_list():
    """
    Get the list of linux kernels from the following directories:
      1. custom-root/boot/vmlinuz-*; initrd.img-*
      2. source-disk/casper/vmlinuz.efi; initrd.lz
    """

    directory_1 = os.path.join(model.project.custom_root_directory, 'boot')
    directory_2 = os.path.join(model.project.iso_mount_point, model.layout.casper_directory)
    kernel_details_list = create_kernel_details_list(directory_1, directory_2)

    return kernel_details_list


def create_kernel_details_list(*directories):

    logger.log_label('Create kernel details list')

    #
    # Vmlinuz
    #

    # Create a consolidated vmlinuz details list.
    vmlinuz_details_list = []
    for directory in directories:
        # Real path is necessary here.
        directory = os.path.realpath(directory)
        update_vmlinuz_details_list(directory, vmlinuz_details_list)

    # For debugging.
    # print_details_list(vmlinuz_details_list)

    # Count vmlinuz directories.
    vmlinuz_directory_counter = collections.Counter()
    vmlinuz_directory_counter.update([vmlinuz_details['directory'] for vmlinuz_details in vmlinuz_details_list])
    directories_with_one_vmlinuz = [directory for directory, count in vmlinuz_directory_counter.items() if count == 1]

    #
    # Initrd
    #

    # Create a consolidated initrd details list.
    initrd_details_list = []
    initrd_directory_counter = collections.Counter()
    for directory in directories:
        # Real path is necessary here.
        directory = os.path.realpath(directory)
        update_initrd_details_list(directory, initrd_details_list)

    # Delete temporary files.
    file_path_pattern = os.path.os.path.join(os.path.sep, 'var', 'tmp', 'unmkinitramfs_*')
    file_utilities.delete_files_with_pattern(file_path_pattern)

    # For debugging.
    # print_details_list(initrd_details_list)

    # Count initrd directories.
    initrd_directory_counter = collections.Counter()
    initrd_directory_counter.update([initrd_details['directory'] for initrd_details in initrd_details_list])
    directories_with_one_initrd = [directory for directory, count in initrd_directory_counter.items() if count == 1]

    #
    # Kernels (vmlinuz and initrd)
    #

    add_message_to_boot_kernels_box('Consolidated kernel files')

    # Create a list of directories that only contain one vmlinuz file
    # and one initrd file.
    directories_with_one_vmlinuz_and_initrd = list(set(directories_with_one_vmlinuz) & set(directories_with_one_initrd))

    # Create a consolidated kernel details list.
    kernel_details_list = []
    _create_kernel_details_list(kernel_details_list, vmlinuz_details_list, initrd_details_list, directories_with_one_vmlinuz_and_initrd)

    # Sort, select kernel, add notes, and remove the 1st column.
    if kernel_details_list:
        _update_kernel_details_list(kernel_details_list)

    # For debugging.
    # print_details_list(kernel_details_list, {'note': 10})

    return kernel_details_list


def _create_kernel_details_list(kernel_details_list, vmlinuz_details_list, initrd_details_list, directories_with_one_vmlinuz_and_initrd):
    """
    Add kernel details to the kernel details list.
    """

    logger.log_label('Collate kernel versions')

    note = ''
    is_selected = False

    for vmlinuz_details in vmlinuz_details_list:

        vmlinuz_version_integers = vmlinuz_details['version_integers']
        vmlinuz_version_name = vmlinuz_details['version_name']
        vmlinuz_file_name = vmlinuz_details['file_name']
        new_vmlinuz_file_name = vmlinuz_details['new_file_name']
        vmlinuz_directory = vmlinuz_details['directory']

        for initrd_details in initrd_details_list:

            initrd_version_integers = initrd_details['version_integers']
            initrd_version_name = initrd_details['version_name']
            initrd_file_name = initrd_details['file_name']
            new_initrd_file_name = initrd_details['new_file_name']
            initrd_directory = initrd_details['directory']

            # The kernel_details dictionary keys:
            # 0: version_integers
            # 1: version_name
            # 2: vmlinuz_file_name
            # 3: new_vmlinuz_file_name
            # 4: initrd_file_name
            # 5: new_initrd_file_name
            # 6: directory
            # 7: note
            # 8: is_selected

            if vmlinuz_directory == initrd_directory:
                if vmlinuz_version_name and initrd_version_name:
                    if vmlinuz_version_integers == initrd_version_integers:
                        logger.log_value('Directory', vmlinuz_directory)
                        logger.log_value('Matching vmlinuz and initrd versions', vmlinuz_version_name)
                        kernel_details = {
                            'version_integers': vmlinuz_version_integers,
                            'version_name': vmlinuz_version_name,
                            'vmlinuz_file_name': vmlinuz_file_name,
                            'new_vmlinuz_file_name': new_vmlinuz_file_name,
                            'initrd_file_name': initrd_file_name,
                            'new_initrd_file_name': new_initrd_file_name,
                            'directory': vmlinuz_directory,
                            'note': note,
                            'is_selected': is_selected
                        }
                        kernel_details_list.append(kernel_details)
                elif vmlinuz_directory in directories_with_one_vmlinuz_and_initrd:
                    if vmlinuz_version_name and not initrd_version_name:
                        logger.log_value('Directory', vmlinuz_directory)
                        logger.log_value('The vmlinuz version is', vmlinuz_version_name)
                        logger.log_value(
                            'The initrd version is',
                            f'{initrd_version_name}; assume the version is {vmlinuz_version_name} because this directory has one set of kernel files')
                        kernel_details = {
                            'version_integers': vmlinuz_version_integers,
                            'version_name': vmlinuz_version_name,
                            'vmlinuz_file_name': vmlinuz_file_name,
                            'new_vmlinuz_file_name': new_vmlinuz_file_name,
                            'initrd_file_name': initrd_file_name,
                            'new_initrd_file_name': new_initrd_file_name,
                            'directory': vmlinuz_directory,
                            'note': note,
                            'is_selected': is_selected
                        }
                        kernel_details_list.append(kernel_details)
                    elif not vmlinuz_version_name and initrd_version_name:
                        logger.log_value('Directory', vmlinuz_directory)
                        logger.log_value(
                            'The vmlinuz version is',
                            f'{vmlinuz_version_name}; assume the version is {initrd_version_name} because this directory has one set of kernel files')
                        kernel_details = {
                            'version_integers': initrd_version_integers,
                            'version_name': initrd_version_name,
                            'vmlinuz_file_name': vmlinuz_file_name,
                            'new_vmlinuz_file_name': new_vmlinuz_file_name,
                            'initrd_file_name': initrd_file_name,
                            'new_initrd_file_name': new_initrd_file_name,
                            'directory': vmlinuz_directory,
                            'note': note,
                            'is_selected': is_selected
                        }
                        kernel_details_list.append(kernel_details)
                    else:
                        logger.log_value('Directory', vmlinuz_directory)
                        logger.log_value('The vmlinuz version is', f'{vmlinuz_version_name}; assume the version is 0.0.0-0')
                        logger.log_value('The initrd version is', f'{initrd_version_name}; assume the version is  0.0.0-0')
                        kernel_details = {
                            'version_integers': (0,
                                                 0,
                                                 0,
                                                 0),
                            # 'version_name': '0.0.0-0',
                            'version_name': None,
                            'vmlinuz_file_name': vmlinuz_file_name,
                            'new_vmlinuz_file_name': new_vmlinuz_file_name,
                            'initrd_file_name': initrd_file_name,
                            'new_initrd_file_name': new_initrd_file_name,
                            'directory': vmlinuz_directory,
                            'note': note,
                            'is_selected': is_selected
                        }
                        kernel_details_list.append(kernel_details)
                else:
                    logger.log_value('Directory', vmlinuz_directory)
                    logger.log_value('The vmlinuz version is', vmlinuz_version_name)
                    logger.log_value('The initrd version is', initrd_version_name)
                    logger.log_value('Warning', 'The versions do not match. Skipping')


def _update_kernel_details_list(kernel_details_list):
    """
    Sort, select kernel, add notes, and remove the 1st column.
    """

    logger.log_label('List the kernel details')

    # Reverse sort the kernel details list by kernel version number (1st
    # column).
    #
    # List sort can use a list as the sorting key, and the column values
    # may be tuples, strings, etc. However, list sort can only
    # compare tuples with tuples and stings with strings, and these
    # values may not be None. Since each row of details in
    # kernel_details_list is a dict, this approach uses list compression
    # to create a new list which may be used as the sorting key. The
    # list compression applies a value of (0,0,0,0) if the 1st colum is
    # None, because this column should contain a tuple. It also applies
    # a value of '' for the other columns, if they are None, because the
    # other columns should contain strings. Otherwise, the list
    # compression just uses the column's existing value from the dict
    # when creating the new list for the row.
    kernel_details_list.sort(
        key=lambda details: [(0,
                              0,
                              0,
                              0) if k == 'version_integers' and v is None else '' if v is None else v for k,
                             v in details.items()],
        reverse=True)

    # Set the selected index as the index of the most recent kernel.
    selected_index = 0

    # Set the notes, and update the selected index if necessary.
    # current_kernel_release_name = get_current_kernel_release_name()
    current_kernel_version_name = get_current_kernel_version_name()
    original_iso_image_directory = os.path.join(model.project.iso_mount_point, model.layout.casper_directory)
    for index, kernel_details in enumerate(kernel_details_list):
        note = ''
        version_name = kernel_details['version_name']
        if current_kernel_version_name == version_name:
            if note: note += ' '  # os.linesep
            note += f'You are currently running kernel version {current_kernel_version_name}.'
        # if index == 0:
        #     if note: note += ' '  # os.linesep
        #     note += 'This is the newest kernel version available to bootstrap the customized disk.'
        directory = kernel_details['directory']
        if directory == original_iso_image_directory:
            if note: note += ' '  # os.linesep
            note += 'This kernel is used to bootstrap the original disk.'
            if len(kernel_details_list) > 1:
                if note: note += ' '  # os.linesep
                note += 'Select this kernel if you are unable to boot the disk using other kernel versions.'
            if model.layout.installer_sources_file_name:
                # If Subiquity is used, select the original kernel.
                # Added for Cubic 2023.03.78 to support Ubuntu 23.04.
                if note: note += ' '  # os.linesep
                note += 'Use this kernel to bootstrap Ubuntu Server 21.10+ or Desktop 23.04+.'
                # Set the selected index for the the original disk kernel.
                selected_index = index
            # if is_server_image()
            #     # if note: note += ' ' # os.linesep
            #     # note += 'Since you are customizing a server image, select this option if you encounter issues using other kernel versions.'
            #     # Set the selected index for the the original disk kernel.
            #     selected_index = index
        else:
            if note: note += ' '  # os.linesep
            note += 'This kernel is installed in the <span font_family="monospace">/boot</span> directory of the Linux file system and can be used to bootstrap the customized disk.'
        new_vmlinuz_file_name = kernel_details['new_vmlinuz_file_name']
        new_initrd_file_name = kernel_details['new_initrd_file_name']
        if note: note += ' '  # os.linesep
        note += f'Reference these files as <span font_family="monospace">{new_vmlinuz_file_name}</span> and <span font_family="monospace">{new_initrd_file_name}</span> in the disk boot configurations.'
        kernel_details['note'] = note

    # Set the selected kernel based on the selected index.
    kernel_details_list[selected_index]['is_selected'] = True

    # For debugging.
    # print_details_list(kernel_details_list, {'note': 10})

    # Remove the 1st column because it is a tuple and cannot be rendered.
    # The resulting kernel_details is:
    #
    # 0: version_name
    # 1: vmlinuz_file_name
    # 2: new_vmlinuz_file_name
    # 3: initrd_file_name
    # 4: new_initrd_file_name
    # 5: directory
    # 6: note
    # 7: is_selected
    #
    # It is not necessary to remove the 1st column because because items
    # are selectively added to the list_store in the
    # displayer.update_list_store() function.
    #
    # (list_store_name, data_list)
    # [
    #     kernel_details.pop('version_integers')
    #     for kernel_details in kernel_details_list
    # ]

    # For debugging.
    # print_details_list(kernel_details_list, {'note': 10})

    # Log the resulting list of kernel versions.
    total = len(kernel_details_list)
    for index, kernel_details in enumerate(kernel_details_list):
        logger.log_value('Version', kernel_details['version_name'])
        logger.log_value('▹ Index', f'{index + 1} of {total}')
        logger.log_value('▹ Vmlinuz file name', kernel_details['vmlinuz_file_name'])
        logger.log_value('▹ New vmlinuz file name', kernel_details['new_vmlinuz_file_name'])
        logger.log_value('▹ Initrd file name', kernel_details['initrd_file_name'])
        logger.log_value('▹ New initrd file name', kernel_details['new_initrd_file_name'])
        logger.log_value('▹ Directory', kernel_details['directory'])
        logger.log_value('▹ Note', kernel_details['note'])
        logger.log_value('▹ Is selected', kernel_details['is_selected'])


def get_current_kernel_version_name():

    version_name = None
    try:
        version_information = (r'(\d+\.\d+\.\d+(?:-\d+)*)', platform.release())
        version_name = version_information.group(1)
    except AttributeError as exception:
        pass

    return version_name


def get_current_kernel_release_name():

    return platform.release()


def is_server_image():

    # Guess if we are customizing a server image by checking the file
    # name, volume id, or disk name. For example:
    # - original.iso_file_name = ubuntu-18.04-live-server-amd64.iso
    # - original.iso_volume_id = Ubuntu-Server 18.04 LTS amd64
    # - original.iso_disk_name = Ubuntu-Server 18.04 LTS "Bionic Beaver" - Release amd64

    if re.search('server', model.original.iso_file_name, re.IGNORECASE):
        return True
    if re.search('server', model.original.iso_volume_id, re.IGNORECASE):
        return True
    if re.search('server', model.original.iso_disk_name, re.IGNORECASE):
        return True

    return False


# ----------------------------------------------------------------------
# Vmlinuz
# ----------------------------------------------------------------------


def update_vmlinuz_details_list(directory, details_list):

    logger.log_label('Create vmlinuz details list')
    logger.log_value('▹ Search directory', directory)

    relative_directory = os.path.relpath(directory, model.project.directory)
    add_message_to_boot_kernels_box(f'Search for vmlinuz files in {relative_directory}')

    file_paths = []

    # Replace simlinks with the actual file_path.
    directory = os.path.realpath(directory)
    file_path_pattern = os.path.join(directory, 'vmlinuz*')
    for file_path in glob.glob(file_path_pattern):
        # Replace simlinks with the actual file_path.
        real_path = os.path.realpath(file_path)
        if not os.path.exists(real_path):
            # The real path may not exist because it may be relative to
            # the root directory of the virtual environment. If this is
            # the case, the link will appear broken outside of the
            # virtual environment, because it will seem to point to the
            # root of the host system.

            # The following remedies this situation by appending the
            # virtual environment's root directory to the real path.
            # However, if another file with the same path actually
            # exists on the host system, real path will point to that
            # file instead, and this 'if not' block will not be
            # executed. This is considered a negligible risk.

            # It is necessary to strip the leading '/' from the real
            # path, otherwise os.path.join() considers the real path
            # to be an absolute path and discards the custom root
            # directory prefix: "If a component is an absolute path, all
            # previous components are thrown away and os.path.joining
            # continues from the absolute path component."
            # (See https://docs.python.org/3/library/os.path.html).
            file_path = os.path.abspath(os.path.join(model.project.custom_root_directory, real_path.strip(os.path.sep)))

            # Replace simlinks with the actual file_path.
            real_path = os.path.realpath(file_path)

        if os.path.exists(real_path):
            file_paths.append(real_path)

    file_paths = list(set(file_paths))

    count = len(file_paths)
    logger.log_value('▹ Number of vmlinuz files found', count)
    number_text = constructor.number_as_text(count)
    plural_text = constructor.get_plural('file', 'files', count)
    add_message_to_boot_kernels_box(f'Found {number_text} vmlinuz {plural_text}')
    time.sleep(SLEEP_0250_MS)

    for index, file_path in enumerate(file_paths):
        file_name = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        version_name = get_vmlinuz_version_name(file_path)
        # if not version_name: version_name = '0.0.0-0'
        logger.log_value('▹ The vmlinuz version is', version_name)
        if version_name:
            version_integers = tuple(map(int, re.split('[.-]', version_name)))
        else:
            version_integers = tuple(map(int, re.split('[.-]', '0.0.0-0')))
        new_file_name = calculate_vmlinuz_file_name(file_path)

        details = {
            'version_integers': version_integers,
            'version_name': version_name,
            'file_name': file_name,
            'new_file_name': new_file_name,
            'directory': directory
        }
        details_list.append(details)
        time.sleep(SLEEP_0250_MS)


def calculate_vmlinuz_file_name(file_path):

    # Just use vmlinuz (instead of vmlinuz or vmlinuz.efi).
    file_name = 'vmlinuz'

    return file_name


def get_vmlinuz_version_name(file_path):

    # logger.log_value('Get vmlinuz version', file_path)
    # relative_file_path = os.path.relpath(file_path, model.project.directory)
    file_name = os.path.basename(file_path)
    add_message_to_boot_kernels_box(f'Identify version for {file_name}')

    version_name = (
        _get_vmlinuz_version_name_from_file_name(file_path) or _get_vmlinuz_version_name_from_file_type(file_path)
        or _get_vmlinuz_version_name_from_file_contents(file_path))

    # add_message_to_boot_kernels_box(f'The version is {version_name}')
    return version_name


def _get_vmlinuz_version_name_from_file_name(file_path):
    """
    Get the vmlinuz version name from the name of the file.

    Arguments:
    file_path : str
        The full path of the vmlinuz file. This must be a real path
        (symbolic links must be dereferenced, or followed).

    Returns:
    version_name : str
        The version name.
    """

    logger.log_value('Get vmlinuz version name from file name', file_path)
    file_name = os.path.basename(file_path)
    version_name = re.search(r'\d[\d\.-]*\d', file_name)
    version_name = version_name.group(0) if version_name else None
    logger.log_value('▹ The version name is', version_name)

    return version_name


def _get_vmlinuz_version_name_from_file_type(file_path):
    """
    Get the vmlinuz version name from using the file command.

    Arguments:
    file_path : str
        The full path of the vmlinuz file. This must be a real path
        (symbolic links must be dereferenced, or followed).

    Returns:
    version_name : str
        The version name.
    """

    logger.log_value('Get vmlinuz version name from file type', file_path)
    directory, file_name = os.path.split(file_path)
    command = f'file "{file_name}"'
    result, exit_status, signal_status = execute_synchronous(command, directory)
    version_name = None
    if not exit_status and not signal_status:
        version_information = re.search(r'(\d+\.\d+\.\d+(?:-\d+)*)', str(result))
        if version_information:
            version_name = version_information.group(1)
    logger.log_value('▹ The version name is', version_name)

    return version_name


def _get_vmlinuz_version_name_from_file_contents(file_path):
    """
    Get the vmlinuz version name by reading the fine contents.

    Arguments:
    file_path : str
        The full path of the vmlinuz file. This must be a real path
        (symbolic links must be dereferenced, or followed).

    Returns:
    version_name : str
        The version name.
    """

    logger.log_value('Get vmlinuz version name from file contents', file_path)
    version_name = None
    file_contents = file_utilities.read_file(file_path, errors='ignore')
    candidate = ''
    for character in file_contents:
        # Keep adding characters to candidate, until a non-printable
        # character is encountered.
        if character in string.printable:
            candidate += character
        elif len(candidate) > 4:
            # Attempt to get the version name if there is a sequence of
            # five or more printable characters. The smallest possible
            # version number is five characters (ex. 0.0.0).
            try:
                version_information = re.search(r'(\d+\.\d+\.\d+(?:-\d+)*)', str(candidate))
                version_name = version_information.group(1)
                # The version name has been found.
                break
            except (AttributeError, IndexError):
                # The version name was not found; reset candidate.
                candidate = ''
            # TODO: Is the following code more consistent with other
            # functions in this module?
            r'''
            version_information = re.search(r'(\d+\.\d+\.\d+(?:-\d+)*)', str(candidate))
            if version_information:
                version_name = version_information.group(1)
                break
            else:
                candidate = ''
            '''
        else:
            # Reset candidate if the character is non-printable.
            candidate = ''
    logger.log_value('▹ The version name is', version_name)

    return version_name


# ----------------------------------------------------------------------
# Initrd
# ----------------------------------------------------------------------


def update_initrd_details_list(directory, details_list):

    logger.log_label('Create initrd details list')
    logger.log_value('▹ Search directory', directory)

    relative_directory = os.path.relpath(directory, model.project.directory)
    add_message_to_boot_kernels_box(f'Search for initrd files in {relative_directory}')

    file_paths = []

    # Replace simlinks with the actual file_path.
    directory = os.path.realpath(directory)
    file_path_pattern = os.path.join(directory, 'initrd*')
    for file_path in glob.glob(file_path_pattern):
        # Replace simlinks with the actual file_path.
        real_path = os.path.realpath(file_path)
        if not os.path.exists(real_path):
            # The real path may not exist because it may be relative to
            # the root directory of the virtual environment. If this is
            # the case, the link will appear broken outside of the
            # virtual environment, because it will seem to point to the
            # root of the host system.

            # The following remedies this situation by prepending the
            # virtual environment's root directory to the real path.
            # However, if another file with the same path actually
            # exists on the host system, real path will point to that
            # file instead, and this 'if not' block will not be
            # executed. This is considered a negligible risk.

            # It is necessary to strip the leading '/' from the real
            # path, otherwise os.path.join() considers the real path
            # to be an absolute path and discards the custom root
            # directory prefix: "If a component is an absolute path, all
            # previous components are thrown away and os.path.joining
            # continues from the absolute path component."
            # (See https://docs.python.org/3/library/os.path.html).
            file_path = os.path.abspath(os.path.join(model.project.custom_root_directory, real_path.strip(os.path.sep)))

            # Replace symbolic links with the actual file path.
            real_path = os.path.realpath(file_path)

        if os.path.exists(real_path):
            file_paths.append(real_path)

    file_paths = list(set(file_paths))

    count = len(file_paths)
    logger.log_value('▹ Number of initrd files found', count)
    number_text = constructor.number_as_text(count)
    plural_text = constructor.get_plural('file', 'files', count)
    add_message_to_boot_kernels_box(f'Found {number_text} initrd {plural_text}')
    time.sleep(SLEEP_0250_MS)

    for index, file_path in enumerate(file_paths):
        file_name = os.path.basename(file_path)
        directory = os.path.dirname(file_path)
        version_name = get_initrd_version_name(file_path)
        # if not version_name: version_name = '0.0.0-0'
        logger.log_value('▹ The initrd version is', version_name)
        if version_name:
            version_integers = tuple(map(int, re.split('[.-]', version_name)))
        else:
            version_integers = tuple(map(int, re.split('[.-]', '0.0.0-0')))
        new_file_name = calculate_initrd_file_name(file_path)

        details = {
            'version_integers': version_integers,
            'version_name': version_name,
            'file_name': file_name,
            'new_file_name': new_file_name,
            'directory': directory
        }
        details_list.append(details)
        time.sleep(SLEEP_0250_MS)


def calculate_initrd_file_name(file_path):

    # logger.log_value('Calculate initrd file name', file_path)

    compression_format = get_initrd_compression_format(file_path)
    compression_extension = COMPRESSION_EXTENSIONS.get(compression_format)
    if compression_extension:
        file_name = f'initrd.{compression_extension}'
    else:
        file_name = 'initrd'

    return file_name


def get_initrd_compression_format(file_path):

    # logger.log_value('Get initrd compression format', file_path)

    file_name = os.path.basename(file_path)
    add_message_to_boot_kernels_box(f'Identify correct compression format for {file_name}')

    compression_format = (_get_initrd_compression_format_from_file_type(file_path) or _get_initrd_compression_format_from_file_contents(file_path))

    logger.log_value('The compression format is', compression_format)

    return compression_format


def _get_initrd_compression_format_from_file_type(file_path):
    """
    Get the compression format in lower case.
    Valid compression formats are 'gzip', 'bzip2', 'lz4', 'lzma', 'lzop', and 'xz'.
    """

    logger.log_value('Get initrd compression format from file type', file_path)

    command = f'file "{file_path}"'
    result, exit_status, signal_status = execute_synchronous(command)
    logger.log_value('The initrd file type information is', result)

    compression_format = None
    match = re.search(r':\s(.*)\scompressed data', result)
    if match:
        compression_format = match.group(1).lower()
        logger.log_value('Initrd compression format found?', 'Yes')
    else:
        logger.log_value('Initrd compression format found?', 'No')

    return compression_format


def _get_initrd_compression_format_from_file_contents(file_path):
    """
    Get the compression format in lower case.
    Valid compression formats are 'gzip', 'bzip2', 'lz4', 'lzma', 'lzop', and 'xz'.
    """

    logger.log_value('Get initrd compression format from file contents', file_path)
    compression_format = None
    try:
        # Only show results that match "compressed data"
        command = f'binwalk --include="compressed data" "{file_path}"'
        process = execute_asynchronous(command)

        # Assume the first occurrence "compressed data" contains the
        # compression format used. This immediately follows the line:
        # ASCII cpio archive (SVR4 with no CRC), file name: "TRAILER!!!"
        process.expect(INITRAMFS_COMPRESSION_PATTERN)
        # Close the process to obtain the exit status, if needed.
        process.close()
        logger.log_value('The initrd file contents information is', process.match.group(0))
        compression_format = process.match.group(1).lower()
        logger.log_value('Initrd compression format found?', 'Yes')
    except IndexError as exception:
        process.close()
        logger.log_value('Initrd compression format found?', 'No')
    except Exception as exception:
        # Exceptions include TIMEOUT, EOF, ExceptionPexpect, or IndexError.
        # Close the process to obtain the exit status, if needed.
        process.close()
        logger.log_value('Initrd compression format found?', 'No')
        logger.log_value('Encountered an exception while getting initrd compression format from file contents', exception)

    return compression_format


'''
# The binwalk.scan() function does not terminate immediately, so the
# former _get_initrd_compression_format_from_file_contents() function is
# preferred over this alternative function. To use this function:
# 1. import binwalk
# 2. Add the following to the debian control file:
#    # Required for binwalk; included with binwalk
#      python3-binwalk (>=2.1.1),
def _get_initrd_compression_format_from_file_contents_ALTERNATIVE(file_path):
    """
    Get the compression format in lower case.
    Valid compression formats are 'gzip', 'bzip2', 'lz4', 'lzma', 'lzop', and 'xz'.
    """

    logger.log_value('Get initrd compression format from file contents', file_path)
    compression_format = None

    for module in binwalk.scan(file_path, signature=True, quiet=True, include='compressed data'):
        for result in module.results:
            logger.log_value('The initrd file contents information is', result.description)
            match = INITRAMFS_COMPRESSION_PATTERN.match(result.description)
            if match:
                compression_format = match.group(1).lower()
                logger.log_value('Initrd compression format found?', 'Yes')
                break
            else:
                logger.log_value('Initrd compression format found?', 'No')

    return compression_format
'''


def get_vmlinuz_version_from_kernel_details_list(kernel_details_list, directory):

    # The kernel_details dictionary keys:
    # 0: version_integers
    # 1: version_name
    # 2: vmlinuz_file_name
    # 3: new_vmlinuz_file_name
    # 4: initrd_file_name
    # 5: new_initrd_file_name
    # 6: directory
    # 7: note
    # 8: is_selected

    version_name = '0.0.0-0'
    for kernel_details in kernel_details_list:
        if directory == kernel_details[6]:
            version_name = kernel_details[1]
            break
    return version_name


def get_initrd_version_name(file_path):

    # logger.log_value('Get initrd version', file_path)
    # TODO: Investigate if relative file path should have been used below.
    # relative_file_path = os.path.relpath(file_path, model.project.directory)
    # add_message_to_boot_kernels_box(f'▹ Processing .../{relative_file_path}')
    file_name = os.path.basename(file_path)
    add_message_to_boot_kernels_box(f'Identify version for {file_name}')

    version_name = (
        _get_initrd_version_name_from_file_name(file_path) or _get_initrd_version_name_from_file_contents(file_path)
        or _get_initrd_version_name_from_file_type(file_path))

    # add_message_to_boot_kernels_box(f'The version is {version_name}')
    return version_name


def _get_initrd_version_name_from_file_name(file_path):
    """
    Get the initrd version name from the name of the file.

    Arguments:
    file_path : str
        The full path of the initrd file. This must be a real path
        (symbolic links must be dereferenced, or followed).

    Returns:
    version_name : str
        The version name.
    """

    logger.log_value('Get initrd version name from file name', file_path)
    file_name = os.path.basename(file_path)
    version_name = re.search(r'\d[\d\.-]*\d', file_name)
    version_name = version_name.group(0) if version_name else None
    logger.log_value('▹ The version name is', version_name)

    return version_name


def _get_initrd_version_name_from_file_type(file_path):
    """
    Get the initrd version name from using the file command.

    Arguments:
    file_path : str
        The full path of the initrd file. This must be a real path
        (symbolic links must be dereferenced, or followed).

    Returns:
    version_name : str
        The version name.
    """

    logger.log_value('Get initrd version name from file type', file_path)
    directory, file_name = os.path.split(file_path)
    command = f'file "{file_name}"'
    result, exit_status, signal_status = execute_synchronous(command, directory)
    version_name = None
    if not exit_status and not signal_status:
        version_information = re.search(r'(\d+\.\d+\.\d+(?:-\d+)*)', str(result))
        if version_information:
            version_name = version_information.group(1)
    logger.log_value('▹ The version name is', version_name)

    return version_name


def _get_initrd_version_name_from_file_contents(file_path):
    """
    Get the initrd version name from using the lsinitramfs command.

    Arguments:
    file_path : str
        The full path of the initrd file. This must be a real path
        (symbolic links must be dereferenced, or followed).

    Returns:
    version_name : str
        The version name.
    """

    logger.log_value('Get initrd version name from file contents', file_path)
    version_name = None
    try:
        command = f'lsinitramfs "{file_path}"'
        process = execute_asynchronous(command)
        process.expect(INITRAMFS_VERSION_PATTERN)
        # Close the process to obtain the exit status, if needed.
        process.close()
        version_name = process.match.group(1)
    except Exception as exception:
        # Exceptions include TIMEOUT, EOF, ExceptionPexpect, or IndexError.
        # Close the process to obtain the exit status, if needed.
        process.close()
        logger.log_value('Encountered an exception while getting initrd version name from file contents', exception)

    logger.log_value('▹ The version name is', version_name)

    return version_name


# ----------------------------------------------------------------------
# Print
# ----------------------------------------------------------------------


# For debugging only.
def get_widths(details_list, default_widths):
    """
    details_list   - a list of lists or dicts
    default_widths - dictionary of str:int
    """
    widths = {}
    for details in details_list:
        if not isinstance(details, dict):
            # Assume details is a list; convert into a dictionary.
            details = {index: details[index] for index in range(0, len(details))}
        for key, value in details.items():
            if key in default_widths:
                widths[key] = default_widths[key]
            else:
                value_width = 0 if value is None else len(str(value))
                saved_width = 0 if key not in widths else widths[key]
                widths[key] = max(saved_width, value_width)
    return widths


# For debugging only.
def print_details_list(details_list, default_widths={}):
    """
    details_list   - a list of lists or dicts
    default_widths - dictionary of str:int
    """
    total = len(details_list)
    widths = get_widths(details_list, default_widths)
    index_width = len(str(total))
    for index, details in enumerate(details_list):
        print(('| {:%i}' % index_width).format(index + 1), end='')
        print((' of {:%i}' % index_width).format(total), end='')
        if not isinstance(details, dict):
            # Assume details is a list; convert into a dictionary.
            details = {index: details[index] for index in range(0, len(details))}
        for key in widths.keys():
            width = widths[key]
            if width:
                value = str(details[key])
                print((' | {:%s.%s}' % (width, width)).format(value), end='')
        print(' |')


########################################################################
# Filesystem Manifest Functions
########################################################################


def create_package_details_list(root_directory):
    """
    Create a list of installed package details. Each package detail is a
    list containing the following elements. Only package name and
    package version are populated. All other elements are set to False.
        0: is standard selected?
        1: is minimal selected?
        2: is minimal selected initial?
        3: is minimal active?
        4: package name
        5: package version

    Also see constructor.get_installed_packages_list().

    Arguments:
    root_directory : str
        The root directory of "var/lib/dpkg" (the dpkg database).

    Returns:
    package_details_list : list
        A list of package details.
    """

    logger.log_label('Create list of installed packages')

    package_details_list = []

    # The --root option was added to dpkg-query in Ubuntu 22.04 (dpkg
    # package 1.21.1ubuntu2.1 and higher). Older versions of dpkg-query
    # only support the --admindir option (dpkg package 1.20.9ubuntu2.2
    # and lower).
    admin_directory = os.path.join(root_directory, 'var/lib/dpkg')
    command = 'dpkg-query --admindir="%s" --show' % (admin_directory)
    result, exit_status, signal_status = execute_synchronous(command)

    if result:
        packages = result.splitlines()
        for package in packages:
            package_name, package_version = package.split()

            # Create a new package details for the current package.
            # 0: is standard selected?
            # 1: is minimal selected?
            # 2: is minimal selected initial?
            # 3: is minimal active?
            # 4: package name
            # 5: package version
            package_details = [False, False, False, False, package_name, package_version]
            package_details_list.append(package_details)

    # package_count = len(package_details_list)
    # logger.log_value('Total number of installed packages', len(package_details_list))

    return package_details_list


'''
def create_package_details_list_01(root_directory):
    """
    Create a list of installed package details. Each package detail is a
    list containing the following elements. Only package name and
    package version are populated. All other elements are set to False.
        0: is standard selected?
        1: is minimal selected?
        2: is minimal selected initial?
        3: is minimal active?
        4: package name
        5: package version

    Also see constructor.get_installed_packages_list().

    Arguments:
    root_directory : str
        The root directory of "var/lib/dpkg" (the dpkg database).

    Returns:
    package_details_list : list
        A list of package details.
    """

    logger.log_label('Create list of installed packages')

    package_details_list = []

    apt_cache = apt.Cache(rootdir=root_directory)
    for package in apt_cache:

        if apt_cache[package.name].is_installed:

            # Create a new package details for the current package.
            # 0: is standard selected?
            # 1: is minimal selected?
            # 2: is minimal selected initial?
            # 3: is minimal active?
            # 4: package name
            # 5: package version
            package_details = [False, False, False, False, package.name, package.installed.version]
            package_details_list.append(package_details)

    # package_count = len(package_details_list)
    # logger.log_value('Total number of installed packages', len(package_details_list))

    return package_details_list


def create_package_details_list_02(root_directory):
    """
    Create a list of installed package details. Each package detail is a
    list containing the following elements. Only package name and
    package version are populated. All other elements are set to False.
        0: is standard selected?
        1: is minimal selected?
        2: is minimal selected initial?
        3: is minimal active?
        4: package name
        5: package version

    Also see constructor.get_installed_packages_list().

    Arguments:
    root_directory : str
        The root directory of "var/lib/dpkg" (the dpkg database).

    Returns:
    package_details_list : list
        A list of package details.
    """

    logger.log_label('Create list of installed packages')

    package_details_list = []

    # The --root option was added to dpkg-query in Ubuntu 22.04 (dpkg
    # package 1.21.1ubuntu2.1 and higher). Older versions of dpkg-query
    # only support the --admindir option (dpkg package 1.20.9ubuntu2.2
    # and lower).
    command = 'dpkg-query --root="%s" --show' % (root_directory)
    result, exit_status, signal_status = execute_synchronous(command)

    if result:
        packages = result.splitlines()
        for package in packages:
            package_name, package_version = package.split()

            # Create a new package details for the current package.
            # 0: is standard selected?
            # 1: is minimal selected?
            # 2: is minimal selected initial?
            # 3: is minimal active?
            # 4: package name
            # 5: package version
            package_details = [False, False, False, False, package_name, package_version]
            package_details_list.append(package_details)

    # package_count = len(package_details_list)
    # logger.log_value('Total number of installed packages', len(package_details_list))

    return package_details_list
'''


def populate_package_details_list_for_standard_install(package_details_list, removable_packages_list):

    # logger.log_label('Identify removable packages for a standard install')

    number_of_packages_total = len(package_details_list)
    number_of_packages_to_remove = 0
    number_of_packages_to_retain = 0

    for package_details in package_details_list:

        # Check the package name with or without the architecture suffix.
        # Some package names include the architecture as a suffix, using
        # ":" as a delimiter (ex. gir1.2-rb-3.0:amd64).
        # • filesystem.manifest may list packages with the
        #   architecture suffix.
        # • filesystem.manifest-remove lists packages with the
        #   architecture suffix.
        # • filesystem.manifest-minimal-remove lists packages without
        #   the architecture suffix.
        package_name = package_details[4]
        package_name_without_architecture = package_name.rpartition(':')[0]
        is_remove_standard = (package_name in removable_packages_list) or (package_name_without_architecture in removable_packages_list)

        # 0: is standard selected?
        # 1: is minimal selected?
        # 2: is minimal selected initial?
        # 3: is minimal active?
        # 4: package name
        # 5: package version

        # Set is standard selected or unselected?
        package_details[0] = is_remove_standard

        number_of_packages_to_remove += is_remove_standard

    number_of_packages_to_retain = number_of_packages_total - number_of_packages_to_remove

    logger.log_value('Total number of installed packages', number_of_packages_total)
    logger.log_value('Number of packages to be removed for a standard install', number_of_packages_to_remove)
    logger.log_value('Number of packages to be retained for a standard install', number_of_packages_to_retain)

    return number_of_packages_to_remove


def populate_package_details_list_for_minimal_install(package_details_list, removable_packages_list):

    # logger.log_label('Identify removable packages for a minimal install')

    number_of_packages_total = len(package_details_list)
    number_of_packages_to_remove = 0
    number_of_packages_to_retain = 0

    for package_details in package_details_list:

        # Check the package name with or without the architecture suffix.
        # Some package names include the architecture as a suffix, using
        # ":" as a delimiter (ex. gir1.2-rb-3.0:amd64).
        # • filesystem.manifest may list packages with the
        #   architecture suffix.
        # • filesystem.manifest-remove lists packages with the
        #   architecture suffix.
        # • filesystem.manifest-minimal-remove lists packages without
        #   the architecture suffix.
        package_name = package_details[4]
        package_name_without_architecture = package_name.rpartition(':')[0]
        is_remove_minimal = (package_name in removable_packages_list) or (package_name_without_architecture in removable_packages_list)

        # 0: is standard selected?
        # 1: is minimal selected?
        # 2: is minimal selected initial?
        # 3: is minimal active?
        # 4: package name
        # 5: package version

        # Get is standard selected or unselected?
        is_remove_standard = package_details[0]

        # Set is minimal selected or unselected?
        package_details[1] = is_remove_minimal or is_remove_standard

        # Backup original minimal check button value. If the standard
        # check button is unselected, then set the minimal check button
        # with this backup value.
        package_details[2] = is_remove_minimal

        # Set minimal check button active or inactive. If the standard
        # check button is active, then the minimal check button must not
        # be active.
        package_details[3] = not is_remove_standard

        number_of_packages_to_remove += (is_remove_minimal or is_remove_standard)

    number_of_packages_to_retain = number_of_packages_total - number_of_packages_to_remove

    logger.log_value('Total number of installed packages', number_of_packages_total)
    logger.log_value('Number of packages to be removed for a minimal install', number_of_packages_to_remove)
    logger.log_value('Number of packages to be retained for a minimal install', number_of_packages_to_retain)

    return number_of_packages_to_remove


def save_file_system_manifest_file(package_details_list):

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

    logger.log_label('Create new file system manifest file')

    try:
        if model.layout.minimal_squashfs_file_name:
            file_name = model.layout.minimal_manifest_file_name
        else:
            file_name = model.layout.manifest_file_name
        file_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory, file_name)

        logger.log_value('Write file system manifest to', file_path)
        with open(file_path, 'w') as file:
            for package_details in package_details_list[:-1]:
                # 0: is standard selected?
                # 1: is minimal selected?
                # 2: is minimal selected initial?
                # 3: is minimal active?
                # 4: package name
                # 5: package version
                package_name = package_details[4]
                package_version = package_details[5]
                file.write(f'{package_name}\t{package_version}\n')
            if package_details:
                package_details = package_details_list[-1]
                file.write(f'{package_name}\t{package_version}')
    except Exception as exception:
        logger.log_value('Do not propagate exception', exception)
        return True  # (Error)
    if not os.path.exists(file_path):
        return True  # (Error)

    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
    # TODO:
    # Remove this *comment* in the future. [2024-08-10]
    #
    # In Cubic version 2024.02.86, minimal manifest is generated, and
    # file system manifest is copied from the original ISO.
    # In Cubic version 2024.08.87, minimal manifest is generated, and
    # file system manifest must be a link to this file.
    # Therefore, delete file system manifest, if it exists, and create
    # the link.
    # ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

    # Create a link to minimal_manifest_file_name from manifest_file_name.
    if model.layout.minimal_squashfs_file_name:
        directory_path = os.path.join(model.project.custom_disk_directory, model.layout.squashfs_directory)
        file_name = model.layout.minimal_manifest_file_name
        link_name = model.layout.manifest_file_name
        _, _, signal_status = file_utilities.create_link(directory_path, file_name, link_name)
        if signal_status:
            return True  # (Error)

    return False  # (No Error)


########################################################################
# Validation Functions
########################################################################


def validate_page():
    """
    Determine if the Packages page should be skipped.
    """

    # Show the Packages page if the installer requires it.
    if model.layout.standard_remove_file_name:
        # Show the Packages page.
        logger.log_value('Show the Packages page?', 'Yes')
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style=None,
            is_next_sensitive=False,
            is_next_visible=True)

    else:
        # Do not show the Packages page.
        logger.log_value('Show the Packages page?', 'No')
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next-options',
            next_button_style=None,
            is_next_sensitive=False,
            is_next_visible=True)
