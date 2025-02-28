#!/usr/bin/python3

########################################################################
#                                                                      #
# boot_tab.py                                                          #
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
import re

from cubic.utilities.files_tab import FilesTab
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Boot Tab Class
########################################################################


class BootTab(FilesTab):

    def __init__(self):
        """
        Create a new BootTab.
        This method must be invoked using GLib.idle_add().
        """

        logger.log_label('Initialize Boot Tab')

        self.COPY_ACTION = 'copy-boot'

        # Widget names.

        self.COPY_FILES_HEADER_BAR_BUTTON = 'boot_tab__copy_files_header_bar_button'
        self.CREATE_DIRECTORY_BUTTON = 'boot_tab__create_directory_button'
        self.CREATE_DIRECTORY_FILE_NAME_ENTRY = 'boot_tab__create_directory_file_name_entry'
        self.CREATE_DIRECTORY_FILE_PATH_LABEL = 'boot_tab__create_directory_file_path_label'
        self.CREATE_DIRECTORY_HEADER_BAR_BUTTON = 'boot_tab__create_directory_header_bar_button'
        self.CREATE_DIRECTORY_MESSAGE_LABEL = 'boot_tab__create_directory_message_label'
        self.CREATE_DIRECTORY_VIEW_PORT = 'boot_tab__create_directory_view_port'
        self.CREATE_FILE_BUTTON = 'boot_tab__create_file_button'
        self.CREATE_FILE_FILE_NAME_ENTRY = 'boot_tab__create_file_file_name_entry'
        self.CREATE_FILE_FILE_PATH_LABEL = 'boot_tab__create_file_file_path_label'
        self.CREATE_FILE_HEADER_BAR_BUTTON = 'boot_tab__create_file_header_bar_button'
        self.CREATE_FILE_MESSAGE_LABEL = 'boot_tab__create_file_message_label'
        self.CREATE_FILE_VIEW_PORT = 'boot_tab__create_file_view_port'
        self.DELETE_DIRECTORY_BUTTON = 'boot_tab__delete_directory_button'
        self.DELETE_DIRECTORY_FILE_NAME_ENTRY = 'boot_tab__delete_directory_file_name_entry'
        self.DELETE_DIRECTORY_FILE_PATH_LABEL = 'boot_tab__delete_directory_file_path_label'
        self.DELETE_DIRECTORY_HEADER_BAR_BUTTON = 'boot_tab__delete_directory_header_bar_button'
        self.DELETE_DIRECTORY_MESSAGE_LABEL = 'boot_tab__delete_directory_message_label'
        self.DELETE_DIRECTORY_VIEW_PORT = 'boot_tab__delete_directory_view_port'
        self.DELETE_FILE_BUTTON = 'boot_tab__delete_file_button'
        self.DELETE_FILE_FILE_NAME_ENTRY = 'boot_tab__delete_file_file_name_entry'
        self.DELETE_FILE_FILE_PATH_LABEL = 'boot_tab__delete_file_file_path_label'
        self.DELETE_FILE_HEADER_BAR_BUTTON = 'boot_tab__delete_file_header_bar_button'
        self.DELETE_FILE_MESSAGE_LABEL = 'boot_tab__delete_file_message_label'
        self.DELETE_FILE_VIEW_PORT = 'boot_tab__delete_file_view_port'
        self.DIRECTORY_HEADER_BOX = 'boot_tab__directory_header_bar_box'
        self.FILE_HEADER_BOX = 'boot_tab__file_header_bar_box'
        self.FILE_PATH_LABEL = 'boot_tab__file_path_label'
        self.FOLDER_NAME = 'boot_tab__folder_name'
        self.FOLDER_VIEW_PORT = 'boot_tab__folder_view_port'
        self.PICTURE_IMAGE = 'boot_tab__picture_image'
        self.PICTURE_VIEW_PORT = 'boot_tab__picture_view_port'
        self.RENAME_DIRECTORY_BUTTON = 'boot_tab__rename_directory_button'
        self.RENAME_DIRECTORY_FILE_PATH_LABEL = 'boot_tab__rename_directory_file_path_label'
        self.RENAME_DIRECTORY_HEADER_BAR_BUTTON = 'boot_tab__rename_directory_header_bar_button'
        self.RENAME_DIRECTORY_MESSAGE_LABEL = 'boot_tab__rename_directory_message_label'
        self.RENAME_DIRECTORY_SOURCE_FILE_NAME_ENTRY = 'boot_tab__rename_directory_source_file_name_entry'
        self.RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY = 'boot_tab__rename_directory_target_file_name_entry'
        self.RENAME_DIRECTORY_VIEW_PORT = 'boot_tab__rename_directory_view_port'
        self.RENAME_FILE_BUTTON = 'boot_tab__rename_file_button'
        self.RENAME_FILE_FILE_PATH_LABEL = 'boot_tab__rename_file_file_path_label'
        self.RENAME_FILE_HEADER_BAR_BUTTON = 'boot_tab__rename_file_header_bar_button'
        self.RENAME_FILE_MESSAGE_LABEL = 'boot_tab__rename_file_message_label'
        self.RENAME_FILE_SOURCE_FILE_NAME_ENTRY = 'boot_tab__rename_file_source_file_name_entry'
        self.RENAME_FILE_TARGET_FILE_NAME_ENTRY = 'boot_tab__rename_file_target_file_name_entry'
        self.RENAME_FILE_VIEW_PORT = 'boot_tab__rename_file_view_port'
        self.SCROLLED_WINDOW_1 = 'boot_tab__scrolled_window_1'
        self.SCROLLED_WINDOW_2 = 'boot_tab__scrolled_window_2'
        self.SHOW_ALL_FILES_HEADER_BAR_BUTTON = 'boot_tab__show_all_files_header_bar_button'
        self.UNKNOWN_FILE_NAME = 'boot_tab__unknown_file_file_name'
        self.UNKNOWN_VIEW_PORT = 'boot_tab__unknown_file_view_port'

        # Signal handler names.

        self.ON_CHANGED_CREATE_DIRECTORY_FILE_NAME_ENTRY = 'on_changed__boot_tab__create_directory_file_name_entry'
        self.ON_CHANGED_CREATE_FILE_FILE_NAME_ENTRY = 'on_changed__boot_tab__create_file_file_name_entry'
        self.ON_CHANGED_RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY = 'on_changed__boot_tab__rename_directory_target_file_name_entry'
        self.ON_CHANGED_RENAME_FILE_TARGET_FILE_NAME_ENTRY = 'on_changed__boot_tab__rename_file_target_file_name_entry'
        self.ON_CLICKED_CREATE_DIRECTORY_BUTTON = 'on_clicked__boot_tab__create_directory_button'
        self.ON_CLICKED_CREATE_FILE_BUTTON = 'on_clicked__boot_tab__create_file_button'
        self.ON_CLICKED_DELETE_DIRECTORY_BUTTON = 'on_clicked__boot_tab__delete_directory_button'
        self.ON_CLICKED_DELETE_FILE_BUTTON = 'on_clicked__boot_tab__delete_file_button'
        self.ON_CLICKED_RENAME_DIRECTORY_BUTTON = 'on_clicked__boot_tab__rename_directory_button'
        self.ON_CLICKED_RENAME_FILE_BUTTON = 'on_clicked__boot_tab__rename_file_button'
        self.ON_CLICKED_COPY_FILES_HEADER_BAR_BUTTON = 'on_clicked__boot_tab__copy_files_header_bar_button'
        self.ON_TOGGLED_CREATE_DIRECTORY_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__create_directory_header_bar_button'
        self.ON_TOGGLED_CREATE_FILE_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__create_file_header_bar_button'
        self.ON_TOGGLED_DELETE_DIRECTORY_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__delete_directory_header_bar_button'
        self.ON_TOGGLED_DELETE_FILE_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__delete_file_header_bar_button'
        self.ON_TOGGLED_RENAME_DIRECTORY_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__rename_directory_header_bar_button'
        self.ON_TOGGLED_RENAME_FILE_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__rename_file_header_bar_button'
        self.ON_TOGGLED_SHOW_ALL_FILES_HEADER_BAR_BUTTON = 'on_toggled__boot_tab__show_all_files_header_bar_button'

        file_path = os.path.join(model.application.directory, 'cubic', 'pages', 'boot_tab.ui')
        super().__init__(file_path)

    def update_boot_configurations(self, relative_file_paths):
        """
        Update the boot configuration files. Replace references to
        vmlinuz and initrd with the correct file names based on the
        currently selected kernel. Replace "boot=<casper>" with the
        correct casper directory.

        The contents of the boot configuration files are updated in:
        • options_page.on_unmap__options_page__kernel_tab()
        • setup_boot_tab()

        (The files_tree must exist, and the files_tab.update_file()
        method performs this check).

        This method must be invoked using GLib.idle_add().

        relative_file_paths : list of str
            A list of file paths relative to the root of the files tree.
        edit_source_view : function
            A function used by files_tree to make changes to the source
            view. This function may add, delete, update, or highlight
            text in the source view.
        """

        logger.log_label('Update boot configurations')

        for relative_file in relative_file_paths:
            self.update_file(relative_file, self.edit_source_view)

    def edit_source_view(self, source_view):
        """
        Search and replace text in the source view associated with a
        file displayed on the boot tab. The source view is updated
        first, and then changes are saved to the file. This function may
        add, delete, update, or highlight text in the source view and is
        a required argument for the files_tab.update_file() function.

        Arguments:
        self : BootTab
            A derived class of FilesTab.
        source_view : GtkSource.View
            The source view to updated.

        Returns:
        update_count : int
            The number of updates (deletions, additions) made.
        """

        logger.log_value('Search and replace in source view', source_view.file_path)

        # Get new values.

        # Workaround for Grml.
        # Only use the first directory from the squashfs directory path.
        # This is to support Grml which uses "live" instead of
        # "live/grml64-full" as the boot directory. Grml is currently
        # the only distro that uses a path for the squashfs file system.
        # squashfs_directory = model.layout.squashfs_directory
        squashfs_directory = model.layout.squashfs_directory.split(os.path.sep)[0]
        casper_directory = model.layout.casper_directory
        has_subiquity = bool(model.layout.installer_sources_file_name)
        new_vmlinuz_file_name = model.kernel_details_list[model.selected_kernel_index]['new_vmlinuz_file_name']
        new_initrd_file_name = model.kernel_details_list[model.selected_kernel_index]['new_initrd_file_name']

        # Process each line of the source buffer.
        source_buffer = source_view.get_buffer()
        number_of_lines = source_buffer.get_line_count()
        update_count = 0
        for line_number in range(number_of_lines):

            # Get the current line.
            line = self.get_line_text(source_buffer, line_number)

            #
            # append
            #
            if re.search(r'^\s*(?i:APPEND)\s+', line):

                # initrd
                match = re.search(r'(?i:INITRD)=(\S+(?i:INITRD)\S*)', line)
                if match:
                    self.delete_text(source_buffer, line_number, match.start(1), match.end(1))
                    update_count += 1
                    logger.log_value('%d. Removed the initrd path on line' % update_count, line_number)
                    text = f'{os.path.sep}{casper_directory}{os.path.sep}{new_initrd_file_name}'
                    text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, match.start(1))
                    source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                    update_count += 1
                    logger.log_value('%d. Updated the initrd path on line' % update_count, line_number)
                    # Get the current line because it has changed.
                    line = self.get_line_text(source_buffer, line_number)

                    # boot
                    match = re.search(r'(?i:BOOT)=(\S+)', line)
                    if match:
                        self.delete_text(source_buffer, line_number, match.start(1), match.end(1))
                        update_count += 1
                        logger.log_value('%d. Removed the boot path on line' % update_count, line_number)
                        text = f'{squashfs_directory}'
                        text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, match.start(1))
                        source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                        update_count += 1
                        logger.log_value('%d. Updated the boot path on line' % update_count, line_number)
                        # Get the current line because it has changed.
                        line = self.get_line_text(source_buffer, line_number)
                    elif not has_subiquity:
                        # If subiquity is not used and "boot=" is
                        # missing, add it.
                        text = f' boot={squashfs_directory}'
                        text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, text_iter_2.get_line_offset())
                        text_iter_1.forward_char()
                        source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                        update_count += 1
                        logger.log_value('%d. Added the boot path on line' % update_count, line_number)
                        # Get the current line because it has changed.
                        line = self.get_line_text(source_buffer, line_number)
                else:
                    logger.log_value('Warning', 'Expected the initrd path on line %d, but it was not found' % line_number)

            #
            # linux
            #
            elif re.search(r'^\s*(?i:LINUX)\s+', line):

                # vmlinuz
                match = re.search(r'(?i:LINUX)\s+(\S+(?i:VMLINUZ)\S*)', line)
                if match:
                    self.delete_text(source_buffer, line_number, match.start(1), match.end(1))
                    update_count += 1
                    logger.log_value('%d. Removed the vmlinuz path on line' % update_count, line_number)
                    text = f'{os.path.sep}{casper_directory}{os.path.sep}{new_vmlinuz_file_name}'
                    text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, match.start(1))
                    source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                    update_count += 1
                    logger.log_value('%d. Updated the vmlinuz path on line' % update_count, line_number)
                    # Get the current line because it has changed.
                    line = self.get_line_text(source_buffer, line_number)

                    # boot
                    match = re.search(r'(?i:BOOT)=(\S+)', line)
                    if match:
                        self.delete_text(source_buffer, line_number, match.start(1), match.end(1))
                        update_count += 1
                        logger.log_value('%d. Removed the boot path on line' % update_count, line_number)
                        text = f'{squashfs_directory}'
                        text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, match.start(1))
                        source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                        update_count += 1
                        logger.log_value('%d. Updated the boot path on line' % update_count, line_number)
                        # Get the current line because it has changed.
                        line = self.get_line_text(source_buffer, line_number)
                    elif not has_subiquity and not re.search(r'^\s*(?i:APPEND)\s+', self.get_line_text(source_buffer, line_number + 1)):
                        # If subiquity is not used and the next line
                        # does not start with "append" and "boot=" is
                        # missing from this line, add it.
                        text = f' boot={squashfs_directory}'
                        text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, text_iter_2.get_line_offset())
                        text_iter_1.forward_char()
                        source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                        update_count += 1
                        logger.log_value('%d. Added the boot path on line' % update_count, line_number)
                        # Get the current line because it has changed.
                        line = self.get_line_text(source_buffer, line_number)
                else:
                    logger.log_value('Warning', 'Expected the vmlinuz path on line %d, but it was not found' % line_number)

            #
            # kernel
            #
            elif re.search(r'^\s*(?i:KERNEL)\s+', line):

                # vmlinuz
                match = re.search(r'(?i:KERNEL)\s+(\S+(?i:VMLINUZ)\S*)', line)
                if match:
                    self.delete_text(source_buffer, line_number, match.start(1), match.end(1))
                    update_count += 1
                    logger.log_value('%d. Removed the vmlinuz path on line' % update_count, line_number)
                    text = f'{os.path.sep}{casper_directory}{os.path.sep}{new_vmlinuz_file_name}'
                    text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, match.start(1))
                    source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                    update_count += 1
                    logger.log_value('%d. Updated the vmlinuz path on line' % update_count, line_number)
                    # Get the current line because it has changed.
                    line = self.get_line_text(source_buffer, line_number)
                else:
                    logger.log_value('Warning', 'Expected the vmlinuz path on line %d, but it was not found' % line_number)

            #
            # initrd
            #
            elif re.search(r'^\s*(?i:INITRD)\s+', line):

                # initrd
                match = re.search(r'(?i:INITRD)\s+(\S+(?i:INITRD)\S*)', line)
                if match:
                    self.delete_text(source_buffer, line_number, match.start(1), match.end(1))
                    update_count += 1
                    logger.log_value('%d. Removed the initrd path on line' % update_count, line_number)
                    text = f'{os.path.sep}{casper_directory}{os.path.sep}{new_initrd_file_name}'
                    text_iter_1, text_iter_2 = self.insert_text(source_buffer, text, line_number, match.start(1))
                    source_buffer.apply_tag_by_name('HIGHLIGHT', text_iter_1, text_iter_2)
                    update_count += 1
                    logger.log_value('%d. Updated the initrd path on line' % update_count, line_number)
                    # Get the current line because it has changed.
                    line = self.get_line_text(source_buffer, line_number)
                else:
                    logger.log_value('Warning', 'Expected the initrd path on line %d, but it was not found' % line_number)

        return update_count
