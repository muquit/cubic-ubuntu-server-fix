#!/usr/bin/python3

########################################################################
#                                                                      #
# files_tab.py                                                         #
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

import gi
import os
import re
import shutil

gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('GtkSource', '4')
except ValueError:
    gi.require_version('GtkSource', '3.0')

from gi.repository import GLib
from gi.repository import GtkSource

from cubic.choosers import copy_file_chooser
from cubic.navigator import handle_navigation
from cubic.utilities.files_tree import FilesTree
from cubic.utilities import file_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

# TODO: Improve this pattern.
# FILE_NAME_PATTERN = r'[a-zA-Z0-9][a-zA-Z0-9\.\-_]*[a-zA-Z0-9]'
FILE_NAME_PATTERN = r'[a-zA-Z0-9]([a-zA-Z0-9\.\-_]*[a-zA-Z0-9])*'

DELETE_FILE_MESSAGE = 'Warning. This file will be permanently removed.'
FILE_NAME_EXISTS_MESSAGE = 'A file with this name already exists.'
INVALID_FILE_NAME_MESSAGE = 'Enter a valid file name containing alpha-numeric characters, dashes, underscores, or periods.'
NEW_FILE_NAME_MESSAGE = 'Enter a new name for the file.'

DELETE_DIRECTORY_MESSAGE = 'Warning. This directory and its contents will be permanently removed.'
DIRECTORY_NAME_EXISTS_MESSAGE = 'A directory with this name already exists.'
INVALID_DIRECTORY_NAME_MESSAGE = 'Enter a valid directory name containing alpha-numeric characters, dashes, underscores, or periods.'
NEW_DIRECTORY_NAME_MESSAGE = 'Enter a new name for the directory.'

########################################################################
# Files Tab Class
########################################################################


class FilesTab:

    def __init__(self, file_path):
        """
        Create a new FilesTab.
        This method must be invoked using GLib.idle_add().
        """

        logger.log_label('Initialize Files Tab')

        # Load the user interface and immediately connect the signals to
        # the handlers.
        model.builder.add_from_file(file_path)
        model.builder.connect_signals(
            {
                self.ON_CHANGED_CREATE_DIRECTORY_FILE_NAME_ENTRY: self.on_changed_create_directory_file_name_entry,
                self.ON_CHANGED_CREATE_FILE_FILE_NAME_ENTRY: self.on_changed_create_file_file_name_entry,
                self.ON_CHANGED_RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY: self.on_changed_rename_directory_target_file_name_entry,
                self.ON_CHANGED_RENAME_FILE_TARGET_FILE_NAME_ENTRY: self.on_changed_rename_file_target_file_name_entry,
                self.ON_CLICKED_CREATE_DIRECTORY_BUTTON: self.on_clicked_create_directory_button,
                self.ON_CLICKED_CREATE_FILE_BUTTON: self.on_clicked_create_file_button,
                self.ON_CLICKED_DELETE_DIRECTORY_BUTTON: self.on_clicked_delete_directory_button,
                self.ON_CLICKED_DELETE_FILE_BUTTON: self.on_clicked_delete_file_button,
                self.ON_CLICKED_RENAME_DIRECTORY_BUTTON: self.on_clicked_rename_directory_button,
                self.ON_CLICKED_RENAME_FILE_BUTTON: self.on_clicked_rename_file_button,
                self.ON_CLICKED_COPY_FILES_HEADER_BAR_BUTTON: self.on_clicked_copy_files_header_bar_button,
                self.ON_TOGGLED_CREATE_DIRECTORY_HEADER_BAR_BUTTON: self.on_toggled_create_directory_header_bar_button,
                self.ON_TOGGLED_CREATE_FILE_HEADER_BAR_BUTTON: self.on_toggled_create_file_header_bar_button,
                self.ON_TOGGLED_DELETE_DIRECTORY_HEADER_BAR_BUTTON: self.on_toggled_delete_directory_header_bar_button,
                self.ON_TOGGLED_DELETE_FILE_HEADER_BAR_BUTTON: self.on_toggled_delete_file_header_bar_button,
                self.ON_TOGGLED_RENAME_DIRECTORY_HEADER_BAR_BUTTON: self.on_toggled_rename_directory_header_bar_button,
                self.ON_TOGGLED_RENAME_FILE_HEADER_BAR_BUTTON: self.on_toggled_rename_file_header_bar_button,
                self.ON_TOGGLED_SHOW_ALL_FILES_HEADER_BAR_BUTTON: self.on_toggled_show_all_files_header_bar_button
            })

        self.files_tree = None

    def create_tree(self, root_file_paths, required_file_paths=None):
        """
        This method must be invoked using GLib.idle_add().

        Arguments:
        root_file_paths : list of str
            List of relative paths of the root directories. For example:
            ["boot/grub", "isolinux"]
        required_file_paths : list of str
            List of relative file paths of files that must be shown in
            the tree. For example: ["boot/grub/grub.cfg",
            "isolinux/txt.cfg"]
        """

        # logger.log_label('Create tree')
        # logger.log_value('The root file paths are', root_file_paths)
        # logger.log_value('The required file paths are', required_file_paths)

        # Activate this show all files (filter) button only if there are
        # required file paths.
        button = model.builder.get_object(self.SHOW_ALL_FILES_HEADER_BAR_BUTTON)
        button.set_active(not bool(required_file_paths))

        self.files_tree = FilesTree(root_file_paths=root_file_paths, selection_changed=self.show_pane_for_file, required_file_paths=required_file_paths)

        # TODO: Should we save this? Could be used in FilesTab.show_pane_for_file()
        # Save the root_file paths.
        # self.root_file_paths = root_file_paths

        # Add the new tree view to the scrolled window.
        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_1)
        # child = scrolled_window.get_child()
        # if child: scrolled_window.remove(child)
        scrolled_window.add(self.files_tree.tree_view)

    def remove_tree(self):

        GLib.idle_add(self._remove_tree)

    def _remove_tree(self):

        self.files_tree.remove_watches()
        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_1)
        tree_view = scrolled_window.get_child()
        if tree_view: scrolled_window.remove(tree_view)
        self.files_tree = None

    ####################################################################
    # Header Bar Button Handlers
    ####################################################################

    # ------------------------------------------------------------------
    # Filter
    # ------------------------------------------------------------------

    def on_toggled_show_all_files_header_bar_button(self, button):

        GLib.idle_add(self.toggle_show_all_files_header_bar_button, button)

    def toggle_show_all_files_header_bar_button(self, button):

        is_show_all_files = button.get_active()

        # Before filtering the tree, save the file, marking it as
        # required, in order to include it in the filtered list.
        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)
        child = scrolled_window.get_child()
        if type(child) is GtkSource.View:
            self.files_tree.save_source_view(child)

        self.files_tree.filter(is_show_all_files)

    # ------------------------------------------------------------------
    # Directory
    # ------------------------------------------------------------------

    def untoggle_directory_header_bar_buttons(self, selected_button=None):

        button = model.builder.get_object(self.CREATE_FILE_HEADER_BAR_BUTTON)
        button.handler_block_by_func(self.on_toggled_create_file_header_bar_button)
        button.set_active(button == selected_button)
        button.handler_unblock_by_func(self.on_toggled_create_file_header_bar_button)

        button = model.builder.get_object(self.CREATE_DIRECTORY_HEADER_BAR_BUTTON)
        button.handler_block_by_func(self.on_toggled_create_directory_header_bar_button)
        button.set_active(button == selected_button)
        button.handler_unblock_by_func(self.on_toggled_create_directory_header_bar_button)

        button = model.builder.get_object(self.RENAME_DIRECTORY_HEADER_BAR_BUTTON)
        button.handler_block_by_func(self.on_toggled_rename_directory_header_bar_button)
        button.set_active(button == selected_button)
        button.handler_unblock_by_func(self.on_toggled_rename_directory_header_bar_button)

        button = model.builder.get_object(self.DELETE_DIRECTORY_HEADER_BAR_BUTTON)
        button.handler_block_by_func(self.on_toggled_delete_directory_header_bar_button)
        button.set_active(button == selected_button)
        button.handler_unblock_by_func(self.on_toggled_delete_directory_header_bar_button)

    def on_clicked_copy_files_header_bar_button(self, button):

        GLib.idle_add(self.click_copy_files_header_bar_button, button)

    def click_copy_files_header_bar_button(self, button):

        self.untoggle_directory_header_bar_buttons(button)
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        self.show_pane_for_file(file_name, file_path, file_data, mime_type)
        copy_file_chooser.open(self.selected_uris)

    def on_toggled_create_file_header_bar_button(self, button):

        GLib.idle_add(self.toggle_create_file_header_bar_button, button)

    def toggle_create_file_header_bar_button(self, button):

        is_active = button.get_active()
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        if is_active:
            self.untoggle_directory_header_bar_buttons(button)
            self.show_pane_for_create_file(file_name, file_path, file_data, mime_type)
        else:
            self.show_pane_for_file(file_name, file_path, file_data, mime_type)

    def on_toggled_create_directory_header_bar_button(self, button):

        GLib.idle_add(self.toggle_create_directory_header_bar_button, button)

    def toggle_create_directory_header_bar_button(self, button):

        is_active = button.get_active()
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        if is_active:
            self.untoggle_directory_header_bar_buttons(button)
            self.show_pane_for_create_directory(file_name, file_path, file_data, mime_type)
        else:
            self.show_pane_for_file(file_name, file_path, file_data, mime_type)

    def on_toggled_rename_directory_header_bar_button(self, button):

        GLib.idle_add(self.toggle_rename_directory_header_bar_button, button)

    def toggle_rename_directory_header_bar_button(self, button):

        is_active = button.get_active()
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        if is_active:
            self.untoggle_directory_header_bar_buttons(button)
            self.show_pane_for_rename_directory(file_name, file_path, file_data, mime_type)
        else:
            self.show_pane_for_file(file_name, file_path, file_data, mime_type)

    def on_toggled_delete_directory_header_bar_button(self, button):

        GLib.idle_add(self.toggle_delete_directory_header_bar_button, button)

    def toggle_delete_directory_header_bar_button(self, button):

        is_active = button.get_active()
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        if is_active:
            self.untoggle_directory_header_bar_buttons(button)
            self.show_pane_for_delete_directory(file_name, file_path, file_data, mime_type)
        else:
            self.show_pane_for_file(file_name, file_path, file_data, mime_type)

    # ------------------------------------------------------------------
    # File
    # ------------------------------------------------------------------

    def untoggle_file_header_bar_buttons(self, selected_button=None):

        button = model.builder.get_object(self.RENAME_FILE_HEADER_BAR_BUTTON)
        button.handler_block_by_func(self.on_toggled_rename_file_header_bar_button)
        button.set_active(button == selected_button)
        button.handler_unblock_by_func(self.on_toggled_rename_file_header_bar_button)

        button = model.builder.get_object(self.DELETE_FILE_HEADER_BAR_BUTTON)
        button.handler_block_by_func(self.on_toggled_delete_file_header_bar_button)
        button.set_active(button == selected_button)
        button.handler_unblock_by_func(self.on_toggled_delete_file_header_bar_button)

    def on_toggled_rename_file_header_bar_button(self, button):

        GLib.idle_add(self.toggle_rename_file_header_bar_button, button)

    def toggle_rename_file_header_bar_button(self, button):

        is_active = button.get_active()
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        if is_active:
            self.untoggle_file_header_bar_buttons(button)
            self.show_pane_for_rename_file(file_name, file_path, file_data, mime_type)
        else:
            self.show_pane_for_file(file_name, file_path, file_data, mime_type)

    def on_toggled_delete_file_header_bar_button(self, button):

        GLib.idle_add(self.toggle_delete_file_header_bar_button, button)

    def toggle_delete_file_header_bar_button(self, button):

        is_active = button.get_active()
        file_name, file_path, file_data, mime_type = self.files_tree.get_selected()
        if is_active:
            self.untoggle_file_header_bar_buttons(button)
            self.show_pane_for_delete_file(file_name, file_path, file_data, mime_type)
        else:
            self.show_pane_for_file(file_name, file_path, file_data, mime_type)

    ####################################################################
    # Pane Handlers
    ####################################################################

    # ------------------------------------------------------------------
    # Create File
    # ------------------------------------------------------------------

    def on_changed_create_file_file_name_entry(self, entry):

        GLib.idle_add(self.validate_create_file_file_name)

    def validate_create_file_file_name(self):

        # Get the file name.
        entry = model.builder.get_object(self.CREATE_FILE_FILE_NAME_ENTRY)
        file_name = entry.get_text()

        # Validate file name.
        is_valid = re.fullmatch(FILE_NAME_PATTERN, file_name)

        if is_valid:

            # Get the path for the file.
            label = model.builder.get_object(self.CREATE_FILE_FILE_PATH_LABEL)
            file_path = label.get_text()

            # Get the path for the new file.
            file_path = os.path.join(file_path, file_name)

            # Check if the file already exists.
            full_file_path = self.get_full_file_path(file_path)
            if os.path.exists(full_file_path):
                is_valid = False
                message = FILE_NAME_EXISTS_MESSAGE
            else:
                is_valid = True
                message = ''
        else:
            is_valid = False
            message = INVALID_FILE_NAME_MESSAGE

        button = model.builder.get_object(self.CREATE_FILE_BUTTON)
        button.set_sensitive(is_valid)

        label = model.builder.get_object(self.CREATE_FILE_MESSAGE_LABEL)
        label.set_text(message)
        context = label.get_style_context()
        if not is_valid:
            context.add_class('error')
        else:
            context.remove_class('error')

    def on_clicked_create_file_button(self, button):

        GLib.idle_add(self.create_file)

    def create_file(self):

        # Get the path for the directory.
        label = model.builder.get_object(self.CREATE_FILE_FILE_PATH_LABEL)
        file_path = label.get_text()

        # Get the file name.
        entry = model.builder.get_object(self.CREATE_FILE_FILE_NAME_ENTRY)
        file_name = entry.get_text()

        # Get the path for the new file.
        file_path = os.path.join(file_path, file_name)

        # Create the new file.
        logger.log_value('Create file', file_path)
        full_file_path = self.get_full_file_path(file_path)
        with open(full_file_path, 'a'):
            pass

        # Set target_file_path to notify the the process_IN_CREATE()
        # function to select this file in the tree. After the tree
        # selection changes, the new file will be displayed in the file
        # pane and the header bar buttons will be reset by the
        # show_pane_for_file() callback function.
        self.files_tree.target_file_path = file_path

    # ------------------------------------------------------------------
    # Create Directory
    # ------------------------------------------------------------------

    def on_changed_create_directory_file_name_entry(self, entry):

        GLib.idle_add(self.validate_create_directory_file_name)

    def validate_create_directory_file_name(self):

        # Get the file name.
        entry = model.builder.get_object(self.CREATE_DIRECTORY_FILE_NAME_ENTRY)
        file_name = entry.get_text()

        # Validate file name.
        is_valid = re.fullmatch(FILE_NAME_PATTERN, file_name)

        if is_valid:

            # Get the path for the directory.
            label = model.builder.get_object(self.CREATE_DIRECTORY_FILE_PATH_LABEL)
            file_path = label.get_text()

            # Get the path for the new file.
            file_path = os.path.join(file_path, file_name)

            # Check if the file already exists.
            full_file_path = self.get_full_file_path(file_path)
            if os.path.exists(full_file_path):
                is_valid = False
                message = DIRECTORY_NAME_EXISTS_MESSAGE
            else:
                is_valid = True
                message = ''
        else:
            is_valid = False
            message = INVALID_DIRECTORY_NAME_MESSAGE

        button = model.builder.get_object(self.CREATE_DIRECTORY_BUTTON)
        button.set_sensitive(is_valid)

        label = model.builder.get_object(self.CREATE_DIRECTORY_MESSAGE_LABEL)
        label.set_text(message)
        context = label.get_style_context()
        if not is_valid:
            context.add_class('error')
        else:
            context.remove_class('error')

    def on_clicked_create_directory_button(self, button):

        GLib.idle_add(self.create_directory)

    def create_directory(self):

        # Get the path for the directory.
        label = model.builder.get_object(self.CREATE_DIRECTORY_FILE_PATH_LABEL)
        file_path = label.get_text()

        # Get the file name.
        entry = model.builder.get_object(self.CREATE_DIRECTORY_FILE_NAME_ENTRY)
        file_name = entry.get_text()

        # Get the path for the new file.
        file_path = os.path.join(file_path, file_name)

        # Create the new file.
        logger.log_value('Create directory', file_path)
        full_file_path = self.get_full_file_path(file_path)
        file_utilities.make_directory(full_file_path)

        # Set target_file_path to notify the the process_IN_CREATE()
        # function to select this file in the tree. After the tree
        # selection changes, the new file will be displayed in the file
        # pane and the header bar buttons will be reset by the
        # show_pane_for_file() callback function.
        self.files_tree.target_file_path = file_path

    # ------------------------------------------------------------------
    # Rename Directory
    # ------------------------------------------------------------------

    def on_changed_rename_directory_target_file_name_entry(self, entry):

        GLib.idle_add(self.validate_rename_directory_file_name)

    def validate_rename_directory_file_name(self):

        # Get the file name.
        entry = model.builder.get_object(self.RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY)
        file_name = entry.get_text()

        # Validate file name.
        is_valid = re.fullmatch(FILE_NAME_PATTERN, file_name)

        if is_valid:

            # Get the path for the new file.
            label = model.builder.get_object(self.RENAME_DIRECTORY_FILE_PATH_LABEL)
            file_path = label.get_text()
            parent_directory = os.path.dirname(file_path)
            file_path = os.path.join(parent_directory, file_name)

            # Check if the file already exists.
            full_file_path = self.get_full_file_path(file_path)
            if os.path.exists(full_file_path):
                is_valid = False
                message = DIRECTORY_NAME_EXISTS_MESSAGE
            else:
                is_valid = True
                message = ''
        else:
            is_valid = False
            message = INVALID_DIRECTORY_NAME_MESSAGE

        button = model.builder.get_object(self.RENAME_DIRECTORY_BUTTON)
        button.set_sensitive(is_valid)

        label = model.builder.get_object(self.RENAME_DIRECTORY_MESSAGE_LABEL)
        label.set_text(message)
        context = label.get_style_context()
        if not is_valid:
            context.add_class('error')
        else:
            context.remove_class('error')

    def on_clicked_rename_directory_button(self, button):

        GLib.idle_add(self.rename_directory)

    def rename_directory(self):

        # Get the path for the original file.
        label = model.builder.get_object(self.RENAME_DIRECTORY_FILE_PATH_LABEL)
        source_file_path = label.get_text()

        # Get the path for the new file.
        parent_directory = os.path.dirname(source_file_path)
        entry = model.builder.get_object(self.RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY)
        target_file_name = entry.get_text()
        target_file_path = os.path.join(parent_directory, target_file_name)

        # Update the required file paths. Assume the rename ill succeed.
        ### self.files_tree.update_required_file_paths(source_file_path, target_file_path)

        # Rename the file.
        logger.log_value('Rename directory', f'from {source_file_path} to {target_file_path}')
        full_source_file_path = self.get_full_file_path(source_file_path)
        full_target_file_path = self.get_full_file_path(target_file_path)
        os.rename(full_source_file_path, full_target_file_path)

        # Set target_file_path to notify the the process_IN_MOVED_TO()
        # function to select this file in the tree. After the tree
        # selection changes, the new file will be displayed in the file
        # pane and the header bar buttons will be reset by the
        # show_pane_for_file() callback function.
        self.files_tree.target_file_path = target_file_path

    # ------------------------------------------------------------------
    # Delete Directory
    # ------------------------------------------------------------------

    def on_clicked_delete_directory_button(self, button):

        GLib.idle_add(self.delete_directory)

    def delete_directory(self):

        # Get the path for the file.
        label = model.builder.get_object(self.DELETE_DIRECTORY_FILE_PATH_LABEL)
        file_path = label.get_text()

        # Delete the file.
        # TODO: What to do about FileNotFoundError error?
        logger.log_value('Delete directory', file_path)
        full_file_path = self.get_full_file_path(file_path)
        shutil.rmtree(full_file_path)

        # Set target_file_path to notify the the process_IN_DELETE()
        # function to select this file's parent directory in the tree.
        # After the tree selection changes, the new file will be
        # displayed in the file pane and the header bar buttons will be
        # reset by the change_tree_view_selection() function.
        self.files_tree.target_file_path = file_path

    # ------------------------------------------------------------------
    # Rename File
    # ------------------------------------------------------------------

    def on_changed_rename_file_target_file_name_entry(self, entry):

        GLib.idle_add(self.validate_rename_file_file_name)

    def validate_rename_file_file_name(self):

        # Get the file name.
        entry = model.builder.get_object(self.RENAME_FILE_TARGET_FILE_NAME_ENTRY)
        file_name = entry.get_text()

        # Validate file name.
        is_valid = re.fullmatch(FILE_NAME_PATTERN, file_name)

        if is_valid:

            # Get the path for the new file.
            label = model.builder.get_object(self.RENAME_FILE_FILE_PATH_LABEL)
            file_path = label.get_text()
            parent_directory = os.path.dirname(file_path)
            file_path = os.path.join(parent_directory, file_name)

            # Check if the file already exists.
            full_file_path = self.get_full_file_path(file_path)
            if os.path.exists(full_file_path):
                is_valid = False
                message = FILE_NAME_EXISTS_MESSAGE
            else:
                is_valid = True
                message = ''
        else:
            is_valid = False
            message = INVALID_FILE_NAME_MESSAGE

        button = model.builder.get_object(self.RENAME_FILE_BUTTON)
        button.set_sensitive(is_valid)

        label = model.builder.get_object(self.RENAME_FILE_MESSAGE_LABEL)
        label.set_text(message)
        context = label.get_style_context()
        if not is_valid:
            context.add_class('error')
        else:
            context.remove_class('error')

    def on_clicked_rename_file_button(self, button):

        GLib.idle_add(self.rename_file)

    def rename_file(self):

        # Get the path for the original file.
        label = model.builder.get_object(self.RENAME_FILE_FILE_PATH_LABEL)
        source_file_path = label.get_text()

        # Get the path for the new file.
        parent_directory = os.path.dirname(source_file_path)
        entry = model.builder.get_object(self.RENAME_FILE_TARGET_FILE_NAME_ENTRY)
        target_file_name = entry.get_text()
        target_file_path = os.path.join(parent_directory, target_file_name)

        # Update the required file paths.
        # self.files_tree.update_required_file_paths(source_file_path, target_file_path)

        # Rename the file.
        logger.log_value('Rename file', f'from {source_file_path} to {target_file_path}')
        full_source_file_path = self.get_full_file_path(source_file_path)
        full_target_file_path = self.get_full_file_path(target_file_path)
        os.rename(full_source_file_path, full_target_file_path)

        # Set target_file_path to notify the the process_IN_MOVED_TO()
        # function to select this file in the tree. After the tree
        # selection changes, the new file will be displayed in the file
        # pane and the header bar buttons will be reset by the
        # show_pane_for_file() callback function.
        self.files_tree.target_file_path = target_file_path

    # ------------------------------------------------------------------
    # Delete File
    # ------------------------------------------------------------------

    def on_clicked_delete_file_button(self, button):

        GLib.idle_add(self.delete_file)

    def delete_file(self):

        # Get the path for the file.
        label = model.builder.get_object(self.DELETE_FILE_FILE_PATH_LABEL)
        file_path = label.get_text()

        # Delete the file.
        # TODO: What to do about FileNotFoundError error?
        logger.log_value('Delete directory', file_path)
        full_file_path = self.get_full_file_path(file_path)
        os.remove(full_file_path)

        # Set target_file_path to notify the the process_IN_DELETE()
        # function to select this file's parent directory in the tree.
        # After the tree selection changes, the new file will be
        # displayed in the file pane and the header bar buttons will be
        # reset by the change_tree_view_selection() function.
        self.files_tree.target_file_path = file_path

    ####################################################################
    # Show Pane Functions
    ####################################################################

    # ------------------------------------------------------------------
    # Contents
    # ------------------------------------------------------------------

    def show_pane_for_file(self, file_name, file_path, file_data, mime_type):
        """
        May be called by methods in this class or as a callback from
        FilesTree.
        This method must be invoked using GLib.idle_add().
        """

        logger.log_value('Show pane for file', file_path)

        # Untoggle all header bar buttons.
        self.untoggle_directory_header_bar_buttons()
        self.untoggle_file_header_bar_buttons()

        # Hide the rename and delete buttons for the tree root(s).
        # TODO: What is the best way to determine is_root?
        #       Option 1: is_root = file_path in self.root_file_paths
        #       Option 2: files_tree.is_root()
        is_root = self.files_tree.is_root(file_path)

        self.set_visible(self.RENAME_DIRECTORY_HEADER_BAR_BUTTON, not is_root)
        self.set_visible(self.DELETE_DIRECTORY_HEADER_BAR_BUTTON, not is_root)

        # Show file data in the scrolled window.

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Display the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_text(file_path)
        label.set_visible(True)

        # Display the new child based on the type of file.
        if mime_type == 'directory':
            self.set_visible(self.DIRECTORY_HEADER_BOX, True)
            self.set_visible(self.FILE_HEADER_BOX, False)
            # Set the file name for the view port.
            label = model.builder.get_object(self.FOLDER_NAME)
            label.set_text(file_name)
            # The child is a view port.
            child = model.builder.get_object(self.FOLDER_VIEW_PORT)
        elif file_data == None:
            # File data is read by the FilesTree.change_tree_selection()
            # method. File data will be None if the file could not be
            # read.
            self.set_visible(self.DIRECTORY_HEADER_BOX, False)
            self.set_visible(self.FILE_HEADER_BOX, True)
            # Set the file name for the view port.
            label = model.builder.get_object(self.UNKNOWN_FILE_NAME)
            label.set_text(file_name)
            # The child is a view port.
            child = model.builder.get_object(self.UNKNOWN_VIEW_PORT)
        elif mime_type == 'text':
            self.set_visible(self.DIRECTORY_HEADER_BOX, False)
            self.set_visible(self.FILE_HEADER_BOX, True)
            # The child is a source view.
            child = file_data
        elif mime_type == 'image':
            self.set_visible(self.DIRECTORY_HEADER_BOX, False)
            self.set_visible(self.FILE_HEADER_BOX, True)
            # Set the image for the view port.
            image = model.builder.get_object(self.PICTURE_IMAGE)
            image.set_from_pixbuf(file_data)
            # The child is a view port.
            child = model.builder.get_object(self.PICTURE_VIEW_PORT)
        else:
            self.set_visible(self.DIRECTORY_HEADER_BOX, False)
            self.set_visible(self.FILE_HEADER_BOX, True)
            # Set the file name for the view port.
            label = model.builder.get_object(self.UNKNOWN_FILE_NAME)
            label.set_text(file_name)
            # The child is a view port.
            child = model.builder.get_object(self.UNKNOWN_VIEW_PORT)

        # Add the new child to the scrolled window.
        scrolled_window.add(child)

    # ------------------------------------------------------------------
    # Directory
    # ------------------------------------------------------------------

    def show_pane_for_create_file(self, file_name, file_path, file_data, mime_type):

        logger.log_value('Show pane for create file', file_path)

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Hide the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_visible(False)

        # Display information.

        label = model.builder.get_object(self.CREATE_FILE_FILE_PATH_LABEL)
        # label.set_markup(f'<span font_family="monospace">{file_path}</span>')
        label.set_markup(file_path)

        # entry = model.builder.get_object(self.CREATE_FILE_FILE_NAME_ENTRY)
        # entry.set_text('')

        # label = model.builder.get_object(self.CREATE_FILE_MESSAGE_LABEL)
        # label.set_text('')
        # context = label.get_style_context()
        # context.remove_class('error')

        # button = model.builder.get_object(self.CREATE_FILE_BUTTON)
        # button.set_sensitive(False)

        # Explicitly validate the field because the changed signal will
        # not be generated.
        self.validate_create_file_file_name()

        # Add the new child to the scrolled window.
        view_port = model.builder.get_object(self.CREATE_FILE_VIEW_PORT)
        scrolled_window.add(view_port)

    def show_pane_for_create_directory(self, file_name, file_path, file_data, mime_type):

        logger.log_value('Show pane for create directory', file_path)

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Hide the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_visible(False)

        # Display information.

        label = model.builder.get_object(self.CREATE_DIRECTORY_FILE_PATH_LABEL)
        # label.set_markup(f'<span font_family="monospace">{file_path}</span>')
        label.set_markup(file_path)

        # entry = model.builder.get_object(self.CREATE_DIRECTORY_FILE_NAME_ENTRY)
        # entry.set_text('')

        # label = model.builder.get_object(self.CREATE_DIRECTORY_MESSAGE_LABEL)
        # label.set_text('')
        # context = label.get_style_context()
        # context.remove_class('error')

        # button = model.builder.get_object(self.CREATE_DIRECTORY_BUTTON)
        # button.set_sensitive(False)

        # Explicitly validate the field because the changed signal will
        # not be generated.
        self.validate_create_directory_file_name()

        # Add the new child to the scrolled window.
        view_port = model.builder.get_object(self.CREATE_DIRECTORY_VIEW_PORT)
        scrolled_window.add(view_port)

    def show_pane_for_rename_directory(self, file_name, file_path, file_data, mime_type):

        logger.log_value('Show pane for rename directory', file_path)

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Hide the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_visible(False)

        # Display information.

        label = model.builder.get_object(self.RENAME_DIRECTORY_FILE_PATH_LABEL)
        # label.set_markup(f'<span font_family="monospace">{file_path}</span>')
        label.set_markup(file_path)

        entry = model.builder.get_object(self.RENAME_DIRECTORY_SOURCE_FILE_NAME_ENTRY)
        entry.set_text(file_name)

        entry = model.builder.get_object(self.RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY)
        entry.handler_block_by_func(self.on_changed_rename_directory_target_file_name_entry)
        entry.set_text(file_name)
        entry.handler_unblock_by_func(self.on_changed_rename_directory_target_file_name_entry)

        label = model.builder.get_object(self.RENAME_DIRECTORY_MESSAGE_LABEL)
        label.set_text(NEW_DIRECTORY_NAME_MESSAGE)
        context = label.get_style_context()
        context.remove_class('error')

        # button = model.builder.get_object(self.RENAME_DIRECTORY_BUTTON)
        # button.set_sensitive(False)

        # Add the new child to the scrolled window.
        view_port = model.builder.get_object(self.RENAME_DIRECTORY_VIEW_PORT)
        scrolled_window.add(view_port)

    def show_pane_for_delete_directory(self, file_name, file_path, file_data, mime_type):

        logger.log_value('Show pane for delete directory', file_path)

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Hide the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_visible(False)

        # Display information.

        label = model.builder.get_object(self.DELETE_DIRECTORY_FILE_PATH_LABEL)
        # label.set_markup(f'<span font_family="monospace">{file_path}</span>')
        label.set_markup(file_path)

        entry = model.builder.get_object(self.DELETE_DIRECTORY_FILE_NAME_ENTRY)
        entry.set_text(file_name)

        label = model.builder.get_object(self.DELETE_DIRECTORY_MESSAGE_LABEL)
        label.set_text(DELETE_DIRECTORY_MESSAGE)
        context = label.get_style_context()
        context.add_class('error')

        # button = model.builder.get_object(self.DELETE_DIRECTORY_BUTTON)
        # button.set_sensitive(False)

        # Add the new child to the scrolled window.
        view_port = model.builder.get_object(self.DELETE_DIRECTORY_VIEW_PORT)
        scrolled_window.add(view_port)

    # ------------------------------------------------------------------
    # File
    # ------------------------------------------------------------------

    def show_pane_for_rename_file(self, file_name, file_path, file_data, mime_type):

        logger.log_value('Show pane for rename file', file_path)

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Hide the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_visible(False)

        # Display information.

        label = model.builder.get_object(self.RENAME_FILE_FILE_PATH_LABEL)
        label.set_text(file_path)

        entry = model.builder.get_object(self.RENAME_FILE_SOURCE_FILE_NAME_ENTRY)
        entry.set_text(file_name)

        entry = model.builder.get_object(self.RENAME_FILE_TARGET_FILE_NAME_ENTRY)
        entry.handler_block_by_func(self.on_changed_rename_file_target_file_name_entry)
        entry.set_text(file_name)
        entry.handler_unblock_by_func(self.on_changed_rename_file_target_file_name_entry)

        label = model.builder.get_object(self.RENAME_FILE_MESSAGE_LABEL)
        label.set_text(NEW_FILE_NAME_MESSAGE)
        context = label.get_style_context()
        context.remove_class('error')

        # button = model.builder.get_object(self.RENAME_FILE_BUTTON)
        # button.set_sensitive(False)

        # Add the new child to the scrolled window.
        view_port = model.builder.get_object(self.RENAME_FILE_VIEW_PORT)
        scrolled_window.add(view_port)

    def show_pane_for_delete_file(self, file_name, file_path, file_data, mime_type):

        logger.log_value('Show pane for delete file', file_path)

        scrolled_window = model.builder.get_object(self.SCROLLED_WINDOW_2)

        # Remove the current child from the scrolled window.
        child = scrolled_window.get_child()
        if child: scrolled_window.remove(child)

        # Hide the file path.
        label = model.builder.get_object(self.FILE_PATH_LABEL)
        label.set_visible(False)

        # Display information.

        label = model.builder.get_object(self.DELETE_FILE_FILE_PATH_LABEL)
        label.set_text(file_path)

        entry = model.builder.get_object(self.DELETE_FILE_FILE_NAME_ENTRY)
        entry.set_text(file_name)

        label = model.builder.get_object(self.DELETE_FILE_MESSAGE_LABEL)
        label.set_text(DELETE_FILE_MESSAGE)
        context = label.get_style_context()
        context.add_class('error')

        # button = model.builder.get_object(self.DELETE_FILE_BUTTON)
        # button.set_sensitive(False)

        # Add the new child to the scrolled window.
        view_port = model.builder.get_object(self.DELETE_FILE_VIEW_PORT)
        scrolled_window.add(view_port)

    ####################################################################
    # File Chooser Functions
    ####################################################################

    def selected_uris(self, uris):

        # logger.log_value('The selected uris are', uris)

        model.selected_uris = uris

        model.current_directory = self.files_tree.get_selected()[1]
        logger.log_value('The current directory is', model.current_directory)

        # Go to the copy page.
        handle_navigation(self.COPY_ACTION)

    ####################################################################
    # Search and Replace Functions
    ####################################################################

    def update_file(self, relative_file_path, edit_source_view):
        """
        Update text in the specified file. Update the source view first,
        using the supplied edit_source_view() function. Then save the
        source view to the corresponding file.

        This method checks if the files tree exists before attempting to
        update the source view.

        relative_file_path : str
            A file path relative to the root of the files tree.
        edit_source_view : function
            A function used by files_tree to make changes to the source
            view. This function may add, delete, update, or highlight
            text in the source view.
        """

        # logger.log_label('Search and replace in files')

        # Check if the files tree exists before attempting to update
        # the file. For example:
        # Upon leaving the Options page on back action:
        # 1. The Kernel, Preseed, and Boot tabs are unmapped (as a
        #    consequence of no longer being visible).
        # 2. The Options page leave() function removes the files trees
        #    associated with the Preseed and Boot tabs.
        # Next, when the Kernel tab is unmapped:
        # 3. The options_page.on_unmap__options_page__kernel_tab()
        #    function attempts to update the boot configurations.
        # 4. However, the files tree associated to the boot tab no
        #    longer exists (see step 2 above).

        if self.files_tree: self.files_tree.update_source_view(relative_file_path, edit_source_view)

    def get_line_text(self, source_buffer, line_number):
        """
        Read text from the specified line of the source_buffer.

        Arguments:
        source_buffer : GtkSource.Buffer
            The source buffer to read the text line from.
        line_number : int
            The line number to read.
        """

        text_iter_1 = source_buffer.get_iter_at_line(line_number)
        if not text_iter_1.ends_line():
            text_iter_2 = text_iter_1.copy()
            text_iter_2.forward_to_line_end()
            line_text = source_buffer.get_text(text_iter_1, text_iter_2, True)
        else:
            line_text = ''

        return line_text

    def insert_text(self, source_buffer, text, line_number, line_offset):
        """
        Insert text at specified line and offset in the source buffer.

        Arguments:
        source_buffer : GtkSource.Buffer
            The source buffer to insert text into.
        text : str
            The text to insert.
        line_number : int
            The line number to insert the text on.
        line_offset : int
            The line offset to insert the text at.

        Returns:
        text_iter_1 : Gtk.TextIter
            The start text iter where the text was inserted.
        text_iter_2 : Gtk.TextIter
            The end text iter where the text was inserted.
        """

        text_iter_1 = source_buffer.get_iter_at_line_offset(line_number, line_offset)
        source_buffer.insert(text_iter_1, text)
        # Get the text iter again because the buffer was modified since
        # the iterator was created.
        text_iter_1 = source_buffer.get_iter_at_line_offset(line_number, line_offset)
        text_iter_2 = source_buffer.get_iter_at_line_offset(line_number, line_offset + len(text))

        return text_iter_1, text_iter_2

    def delete_text(self, source_buffer, line_number, line_offset_1, line_offset_2):
        """
        Delete text from the source buffer, corresponding to the
        specified line number and the range specified by the start and
        end offsets.

        Arguments:
        source_buffer : GtkSource.Buffer
            The source buffer to delete text from.
        line_number : int
            The line number to delete text from.
        line_offset_1 : int
            The starting line offset to begin deleting the text.
        line_offset_2 : int
            The ending line offset to stop deleting the text.

        Returns:
        text_iter_1 : Gtk.TextIter
            The start text iter where the text was deleted.
        """

        text_iter_1 = source_buffer.get_iter_at_line_offset(line_number, line_offset_1)
        text_iter_2 = source_buffer.get_iter_at_line_offset(line_number, line_offset_2)
        source_buffer.delete(text_iter_1, text_iter_2)
        # Get the text iter again because the buffer was modified since
        # the iterator was created.
        text_iter_1 = source_buffer.get_iter_at_line_offset(line_number, line_offset_1)

        return text_iter_1

    ####################################################################
    # Miscellaneous Functions
    ####################################################################

    def set_visible(self, widget_name, is_visible):

        widget = model.builder.get_object(widget_name)
        widget.set_visible(is_visible)

    def get_required_file_paths(self):
        """
        This method is used by options_page.
        """

        return self.files_tree.get_required_file_paths()

    def get_full_file_path(self, file_path):

        file_path = os.path.join(model.project.custom_disk_directory, file_path)

        return file_path

    def get_relative_file_path(self, file_path):
        """
        This method is not used.
        """

        file_path = os.path.relpath(file_path, model.project.custom_disk_directory)

        return file_path
