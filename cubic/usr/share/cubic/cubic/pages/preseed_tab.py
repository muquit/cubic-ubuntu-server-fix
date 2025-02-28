#!/usr/bin/python3

########################################################################
#                                                                      #
# preseed_tab.py                                                       #
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

from cubic.utilities.files_tab import FilesTab
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Preseed Tab Class
########################################################################


class PreseedTab(FilesTab):

    def __init__(self):
        """
        Create a new PreseedTab.
        This method must be invoked using GLib.idle_add().
        """

        logger.log_label('Initialize Preseed Tab')

        self.COPY_ACTION = 'copy-preseed'

        # Widget names.

        self.COPY_FILES_HEADER_BAR_BUTTON = 'preseed_tab__copy_files_header_bar_button'
        self.CREATE_DIRECTORY_BUTTON = 'preseed_tab__create_directory_button'
        self.CREATE_DIRECTORY_FILE_NAME_ENTRY = 'preseed_tab__create_directory_file_name_entry'
        self.CREATE_DIRECTORY_FILE_PATH_LABEL = 'preseed_tab__create_directory_file_path_label'
        self.CREATE_DIRECTORY_HEADER_BAR_BUTTON = 'preseed_tab__create_directory_header_bar_button'
        self.CREATE_DIRECTORY_MESSAGE_LABEL = 'preseed_tab__create_directory_message_label'
        self.CREATE_DIRECTORY_VIEW_PORT = 'preseed_tab__create_directory_view_port'
        self.CREATE_FILE_BUTTON = 'preseed_tab__create_file_button'
        self.CREATE_FILE_FILE_NAME_ENTRY = 'preseed_tab__create_file_file_name_entry'
        self.CREATE_FILE_FILE_PATH_LABEL = 'preseed_tab__create_file_file_path_label'
        self.CREATE_FILE_HEADER_BAR_BUTTON = 'preseed_tab__create_file_header_bar_button'
        self.CREATE_FILE_MESSAGE_LABEL = 'preseed_tab__create_file_message_label'
        self.CREATE_FILE_VIEW_PORT = 'preseed_tab__create_file_view_port'
        self.DELETE_DIRECTORY_BUTTON = 'preseed_tab__delete_directory_button'
        self.DELETE_DIRECTORY_FILE_NAME_ENTRY = 'preseed_tab__delete_directory_file_name_entry'
        self.DELETE_DIRECTORY_FILE_PATH_LABEL = 'preseed_tab__delete_directory_file_path_label'
        self.DELETE_DIRECTORY_HEADER_BAR_BUTTON = 'preseed_tab__delete_directory_header_bar_button'
        self.DELETE_DIRECTORY_MESSAGE_LABEL = 'preseed_tab__delete_directory_message_label'
        self.DELETE_DIRECTORY_VIEW_PORT = 'preseed_tab__delete_directory_view_port'
        self.DELETE_FILE_BUTTON = 'preseed_tab__delete_file_button'
        self.DELETE_FILE_FILE_NAME_ENTRY = 'preseed_tab__delete_file_file_name_entry'
        self.DELETE_FILE_FILE_PATH_LABEL = 'preseed_tab__delete_file_file_path_label'
        self.DELETE_FILE_HEADER_BAR_BUTTON = 'preseed_tab__delete_file_header_bar_button'
        self.DELETE_FILE_MESSAGE_LABEL = 'preseed_tab__delete_file_message_label'
        self.DELETE_FILE_VIEW_PORT = 'preseed_tab__delete_file_view_port'
        self.DIRECTORY_HEADER_BOX = 'preseed_tab__directory_header_bar_box'
        self.FILE_HEADER_BOX = 'preseed_tab__file_header_bar_box'
        self.FILE_PATH_LABEL = 'preseed_tab__file_path_label'
        self.FOLDER_NAME = 'preseed_tab__folder_name'
        self.FOLDER_VIEW_PORT = 'preseed_tab__folder_view_port'
        self.PICTURE_IMAGE = 'preseed_tab__picture_image'
        self.PICTURE_VIEW_PORT = 'preseed_tab__picture_view_port'
        self.RENAME_DIRECTORY_BUTTON = 'preseed_tab__rename_directory_button'
        self.RENAME_DIRECTORY_FILE_PATH_LABEL = 'preseed_tab__rename_directory_file_path_label'
        self.RENAME_DIRECTORY_HEADER_BAR_BUTTON = 'preseed_tab__rename_directory_header_bar_button'
        self.RENAME_DIRECTORY_MESSAGE_LABEL = 'preseed_tab__rename_directory_message_label'
        self.RENAME_DIRECTORY_SOURCE_FILE_NAME_ENTRY = 'preseed_tab__rename_directory_source_file_name_entry'
        self.RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY = 'preseed_tab__rename_directory_target_file_name_entry'
        self.RENAME_DIRECTORY_VIEW_PORT = 'preseed_tab__rename_directory_view_port'
        self.RENAME_FILE_BUTTON = 'preseed_tab__rename_file_button'
        self.RENAME_FILE_FILE_PATH_LABEL = 'preseed_tab__rename_file_file_path_label'
        self.RENAME_FILE_HEADER_BAR_BUTTON = 'preseed_tab__rename_file_header_bar_button'
        self.RENAME_FILE_MESSAGE_LABEL = 'preseed_tab__rename_file_message_label'
        self.RENAME_FILE_SOURCE_FILE_NAME_ENTRY = 'preseed_tab__rename_file_source_file_name_entry'
        self.RENAME_FILE_TARGET_FILE_NAME_ENTRY = 'preseed_tab__rename_file_target_file_name_entry'
        self.RENAME_FILE_VIEW_PORT = 'preseed_tab__rename_file_view_port'
        self.SCROLLED_WINDOW_1 = 'preseed_tab__scrolled_window_1'
        self.SCROLLED_WINDOW_2 = 'preseed_tab__scrolled_window_2'
        self.SHOW_ALL_FILES_HEADER_BAR_BUTTON = 'preseed_tab__show_all_files_header_bar_button'
        self.UNKNOWN_FILE_NAME = 'preseed_tab__unknown_file_file_name'
        self.UNKNOWN_VIEW_PORT = 'preseed_tab__unknown_file_view_port'

        # Signal handler names.

        self.ON_CHANGED_CREATE_DIRECTORY_FILE_NAME_ENTRY = 'on_changed__preseed_tab__create_directory_file_name_entry'
        self.ON_CHANGED_CREATE_FILE_FILE_NAME_ENTRY = 'on_changed__preseed_tab__create_file_file_name_entry'
        self.ON_CHANGED_RENAME_DIRECTORY_TARGET_FILE_NAME_ENTRY = 'on_changed__preseed_tab__rename_directory_target_file_name_entry'
        self.ON_CHANGED_RENAME_FILE_TARGET_FILE_NAME_ENTRY = 'on_changed__preseed_tab__rename_file_target_file_name_entry'
        self.ON_CLICKED_CREATE_DIRECTORY_BUTTON = 'on_clicked__preseed_tab__create_directory_button'
        self.ON_CLICKED_CREATE_FILE_BUTTON = 'on_clicked__preseed_tab__create_file_button'
        self.ON_CLICKED_DELETE_DIRECTORY_BUTTON = 'on_clicked__preseed_tab__delete_directory_button'
        self.ON_CLICKED_DELETE_FILE_BUTTON = 'on_clicked__preseed_tab__delete_file_button'
        self.ON_CLICKED_RENAME_DIRECTORY_BUTTON = 'on_clicked__preseed_tab__rename_directory_button'
        self.ON_CLICKED_RENAME_FILE_BUTTON = 'on_clicked__preseed_tab__rename_file_button'
        self.ON_CLICKED_COPY_FILES_HEADER_BAR_BUTTON = 'on_clicked__preseed_tab__copy_files_header_bar_button'
        self.ON_TOGGLED_CREATE_DIRECTORY_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__create_directory_header_bar_button'
        self.ON_TOGGLED_CREATE_FILE_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__create_file_header_bar_button'
        self.ON_TOGGLED_DELETE_DIRECTORY_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__delete_directory_header_bar_button'
        self.ON_TOGGLED_DELETE_FILE_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__delete_file_header_bar_button'
        self.ON_TOGGLED_RENAME_DIRECTORY_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__rename_directory_header_bar_button'
        self.ON_TOGGLED_RENAME_FILE_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__rename_file_header_bar_button'
        self.ON_TOGGLED_SHOW_ALL_FILES_HEADER_BAR_BUTTON = 'on_toggled__preseed_tab__show_all_files_header_bar_button'

        file_path = os.path.join(model.application.directory, 'cubic', 'pages', 'preseed_tab.ui')
        super().__init__(file_path)
