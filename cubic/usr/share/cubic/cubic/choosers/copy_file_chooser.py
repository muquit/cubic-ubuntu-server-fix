#!/usr/bin/python3

########################################################################
#                                                                      #
# copy_file_chooser.py                                                 #
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

from cubic.utilities import displayer
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'copy_file_chooser'
callback = None

########################################################################
# Functions
########################################################################


def open(calback, file_path=None):

    displayer.set_sensitive('window', False)

    # Since "*" does not exist in a directory, the directory will be
    # opened, and no file will be selected.
    # See https://lazka.github.io/pgi-docs/Gtk-3.0/classes/FileChooser.html#Gtk.FileChooser.set_filename

    if file_path:
        if not os.path.exists(file_path):
            # The file or directory does not exist.
            directory = os.path.dirname(file_path)
            if os.path.isdir(directory):
                file_path = os.path.join(directory, '*')
            else:
                file_path = os.path.join(model.application.user_home, '*')
    else:
        file_path = os.path.join(model.application.user_home, '*')

    displayer.show_file_chooser(name, file_path, 'copy_file_chooser__select_button_1', 'copy_file_chooser__select_button_2')

    set_callback(calback)


def close():

    displayer.set_sensitive('window', False)
    displayer.hide(name)
    displayer.set_sensitive('window', True)


def set_callback(new_callback):

    global callback
    callback = new_callback


def get_selected_file_paths():

    dialog = model.builder.get_object(name)
    file_paths = dialog.get_filenames()
    return file_paths


def get_selected_uris():

    dialog = model.builder.get_object(name)
    uris = dialog.get_uris()
    return uris


def on_clicked__copy_file_chooser__cancel_button(widget):

    logger.log_label('Clicked copy file chooser cancel button')
    close()


def on_selection_changed__copy_file_chooser(widget):

    uris = get_selected_uris()
    if uris:
        displayer.set_sensitive('copy_file_chooser__select_button_1', True)
        displayer.set_sensitive('copy_file_chooser__select_button_2', True)
    else:
        displayer.set_sensitive('copy_file_chooser__select_button_1', False)
        displayer.set_sensitive('copy_file_chooser__select_button_2', False)


def on_file_activated__copy_file_chooser(widget):

    logger.log_label('Activated copy file chooser file')
    uris = get_selected_uris()
    logger.log_value('The number of files selected', len(uris))
    logger.log_value('The selected uris are', uris)
    if uris:
        close()
        callback(uris)
    else:
        logger.log_value('Error.', 'No files or directories selected')
        uris = None


def on_clicked__copy_file_chooser__select_button(widget):

    logger.log_label('Clicked copy file chooser select button')
    uris = get_selected_uris()
    logger.log_value('The number of files selected', len(uris))
    logger.log_value('The selected uris are', uris)
    if uris:
        close()
        callback(uris)
    else:
        logger.log_value('Error.', 'No files or directories selected')
        uris = None


def on_map__copy_file_chooser__header_bar(header_bar):

    is_visible = header_bar.is_visible()
    button_box = model.builder.get_object('copy_file_chooser__button_box')

    # Do not use GLib.idle_add because hiding the button_box must be
    # immediate.
    button_box.set_visible(not is_visible)


def on_delete_event__copy_file_chooser(widget, event):

    logger.log_label('Delete copy file chooser')
    close()
    return True
