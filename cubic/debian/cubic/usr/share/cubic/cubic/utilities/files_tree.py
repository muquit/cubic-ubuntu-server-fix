#!/usr/bin/python3

########################################################################
#                                                                      #
# files_tree.py                                                        #
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

# TODO: Ensure IS_EDITED is set consistently.
# TODO: Improve efficiency.

# Gtk.TreeStore - the tree_store used to store tree iters
# Gtk.TreeModel - the tree_store used to display tree iters

########################################################################
# References
########################################################################

# https://docs.python.org/3/library/asyncio-eventloop.html
# https://docs.python.org/3/library/stat.html#stat.S_ISUID
# http://seb.dbzteam.org/pyinotify/
# https://github.com/seb-m/pyinotify/blob/master/python2/examples/tutorial_asyncnotifier.py
# https://github.com/seb-m/pyinotify/wiki
# https://github.com/seb-m/pyinotify/wiki/Tutorial
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeIter.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeModelFilter.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeModel.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreePath.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeSelection.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeStore.html
# https://lazka.github.io/pgi-docs/Gtk-3.0/classes/TreeView.html
# https://lazka.github.io/pgi-docs/GtkSource-4/classes/Buffer.html
# https://lazka.github.io/pgi-docs/GtkSource-4/classes/View.html
# https://manpages.ubuntu.com/manpages/focal/man7/inotify.7.html
# https://stackoverflow.com/a/1098160/10668287
# https://stackoverflow.com/questions/11178743/gtk-3-0-how-to-use-a-gtk-tree_store-with-custom-model-items
# https://stackoverflow.com/questions/15905132/python-pyinotify-moved-files
# https://stackoverflow.com/questions/23433819/creating-a-simple-file-browser-using-python-and-gtktreeview
# https://wiki.gnome.org/Attic/GdkLock
# https://wiki.python.org/moin/TimeComplexity

########################################################################
# Imports
########################################################################

import asyncio
import gi
import icu
import locale
import os
import pyinotify
import stat
import threading

gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')
### TODO: Remove the following if there are no errors in various older
###       Ubuntu releases.
### try:
###     gi.require_version('GtkSource', '4')
### except ValueError:
###     gi.require_version('GtkSource', '3.0')

from gi.repository import GLib
from gi.repository import Gtk
### TODO: Remove the following if there are no errors in various older
###       Ubuntu releases.
### from gi.repository import GtkSource
from gi.repository.GdkPixbuf import Pixbuf

from cubic.utilities.displayer import MONOSPACE_FONT, SOURCE_LANGUAGE, SOURCE_STYLE_SCHEME
from cubic.utilities import file_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

# The IN_MOVED_FROM event must be watched in order to make
# event.src_pathname available to the IN_MOVED_TO event.
# The IN_MOVE_SELF event must be watched in order to correctly update
# event.pathname for subsequent events such as IN_CREATE.
# MASK = pyinotify.ALL_EVENTS
MASK = (pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVE_SELF)

# Used to sort the tree in the tree_iter_compare() method.
COLLATOR = icu.Collator.createInstance(icu.Locale(str(locale.getlocale())))

# tree_row - an array of three values stored by a tree iter
# tree_iter: [FILE_NAME, FILE_PATH, FILE_ICON]

# Indexes for tree_row
FILE_NAME = 0
FILE_PATH = 1
FILE_ICON = 2

# Empty tree row
# [FILE_NAME, FILE_PATH, FILE_ICON]
EMPTY_TREE_ROW = [None, None, None]

# file_map - a dictionary mapping relative file paths to file_info
# {file_path: file_info}
# {file_path: [TREE_ITER, SHOW_FILE, FILE_DATA, MIME_TYPE, IS_EDITED]}

# file_info is an array of five values
# file_info: [TREE_ITER, SHOW_FILE, FILE_DATA, MIME_TYPE, IS_EDITED]
#
# TREE_ITER - Gtk.TreeIter for Gtk.TreeStore
# SHOW_FILE - True if the file is required, False otherwise
# FILE_DATA - GtkSource.View, Gtk.ViewPort, Pixbuf, None
# MIME_TYPE - the mine type of a file
# IS_EDITED - True if the file was modified by Cubic, False otherwise

# Indexes for file_info
TREE_ITER = 0
SHOW_FILE = 1
FILE_DATA = 2
MIME_TYPE = 3
IS_EDITED = 4

# Empty file info
# [TREE_ITER, SHOW_FILE, FILE_DATA, MIME_TYPE, IS_EDITED]
EMPTY_FILE_INFO = [None, False, None, None, False]

TREE_VIEW_UI_FILE_PATH = os.path.join(model.application.directory, 'cubic', 'utilities', 'tree_view.ui')
SOURCE_VIEW_UI_FILE_PATH = os.path.join(model.application.directory, 'cubic', 'utilities', 'source_view.ui')

########################################################################
# File Event Handlers Class
########################################################################


class FileEventHandlers(pyinotify.ProcessEvent):

    def __init__(self, files_tree):

        self.files_tree = files_tree

    def process_IN_CLOSE_WRITE(self, event):
        """
        Handle the event when a file or directory is created in watched
        directory.

        Arguments:
        event : pyinotify.Event
            The inotify event to handle.
        """

        GLib.idle_add(self.files_tree.process_file_close_write, event)

    def process_IN_CREATE(self, event):
        """
        Handle the event when a file or directory is created in watched
        directory.

        Arguments:
        event : pyinotify.Event
            The inotify event to handle.
        """

        GLib.idle_add(self.files_tree.process_file_create, event)

    def process_IN_DELETE(self, event):
        """
        Handle the event when a file or directory is deleted in watched
        directory.

        Arguments:
        event : pyinotify.Event
            The inotify event to handle.
        """

        GLib.idle_add(self.files_tree.process_file_delete, event)

    def process_IN_MOVED_TO(self, event):
        """
        Handle the event when a file or directory is moved to another
        specified watched directory.

        Arguments:
        event : pyinotify.Event
            The inotify event to handle.
        """

        GLib.idle_add(self.files_tree.process_file_moved_to, event)


########################################################################
# Cubic Tree Class
########################################################################


class FilesTree:

    def __init__(self, root_file_paths, selection_changed, required_file_paths=None):
        """
        Create a new FilesTree.

        In this method:
        - tree_model is a Gtk.TreeModelFilter
        - tree_store is a Gtk.TreeStore

        Arguments:
        root_file_paths : path
            Tree root file paths relative to the custom disk directory
            ("../custom-disk").
        selection_changed : function
            The callback function invoked when the tree selection
            changes. Specifically this is FilesTab.show_pane_for_file().
        required_file_paths : list of path
            List of files to always show in the tree, relative to the
            custom disk directory ("../custom-disk").
        """

        logger.log_label('Initialize files tree')

        logger.log_value('The root file paths are', root_file_paths)
        logger.log_value('The required file paths are', required_file_paths)

        # Create a new tree view.
        builder = Gtk.Builder.new_from_file(TREE_VIEW_UI_FILE_PATH)
        self.tree_view = builder.get_object('tree_view')

        # Set the watch manager.
        self.watch_manager = pyinotify.WatchManager()

        # Set the function to call, when a tree selection changes.
        self.selection_changed = selection_changed

        # Create a mapping of relative file paths to file_info's.
        self.file_map = dict()

        # target_file_path is used to notify "process..." methods that a
        # file was added, deleted, or renamed by this application.
        self.target_file_path = None

        # Get the Gtk.TreeModelFilter.
        self.tree_model = self.tree_view.get_model()

        # Get the Gtk.TreeStore.
        tree_store = self.tree_model.get_model()

        # Show all files if there are no required file paths.
        self.is_show_all_files = not bool(required_file_paths)

        # Set the visibility function on the Gtk.TreeModelFilter.
        self.tree_model.set_visible_func(self.tree_iter_visible, None)

        # Set the sort function on the Gtk.TreeStore.
        tree_store.set_default_sort_func(self.tree_iter_compare, None)
        tree_store.set_sort_column_id(Gtk.TREE_SORTABLE_DEFAULT_SORT_COLUMN_ID, Gtk.SortType.ASCENDING)

        # Build the tree and watch the file system for changes.
        self.watch_descriptors_list = []
        file_event_handlers = FileEventHandlers(self)
        for root_file_path in root_file_paths:
            # None represents the tree iter at the root of the tree.
            self.build_tree(root_file_path)
            # Get the full file path.
            full_file_path = self.get_full_file_path(root_file_path)
            # TODO: Is it possible to only add the root file paths, and
            #       then update the watch_manager with auto_add=True ?
            if os.path.exists(full_file_path):
                logger.log_value('Adding watch for', full_file_path)
                watch_descriptors = self.watch_manager.add_watch(full_file_path, MASK, rec=True, auto_add=True)
                self.watch_descriptors_list.append(watch_descriptors)
            else:
                logger.log_value('Not adding watch for', full_file_path)

        # Set required file paths.
        if required_file_paths:
            self.set_required_files(tree_store, required_file_paths)

        # Start the asyncio event loop as a thread.
        logger.log_value('Asyncio thread', 'Start')
        self.event_loop = asyncio.new_event_loop()
        thread = threading.Thread(target=self.event_loop.run_forever, daemon=True)
        thread.start()

        # Add asyncio notifier.
        pyinotify.AsyncioNotifier(self.watch_manager, self.event_loop, default_proc_fun=file_event_handlers)

        # Add the signal handlers for the new tree view.
        builder.connect_signals({'on_changed_tree_selection': self.on_changed_tree_selection})

        # Expand the tree.
        self.tree_model.refilter()
        self.tree_view.expand_all()

        # Select the first tree root.
        tree_selection = self.tree_view.get_selection()
        tree_selection.select_iter(self.tree_model.get_iter_first())

    ####################################################################
    # Handlers
    ####################################################################

    # ------------------------------------------------------------------
    # Selection Handlers
    # ------------------------------------------------------------------

    def on_changed_tree_selection(self, tree_selection):

        GLib.idle_add(self.change_tree_selection, tree_selection)

    def change_tree_selection(self, tree_selection):
        """
        Read the file corresponding to the selected tree iter and store
        the text or image data. Correct the file icon based on the
        file's mime type. Notify the client that that the tree selection
        has changed by invoking the client's callback method with
        details about the selected file.

        Arguments:
        tree_selection : Gtk.TreeSelection
            Helper object to manage the TreeView selection.
        """

        # Note: This method is similar to update_source_view()

        tree_model, tree_iter = tree_selection.get_selected()

        # If noting is selected, simply return.
        # This situation is rare but may occur if a file is moved, and
        # the parent tree iter has not been selected in time.
        if not tree_iter:
            logger.log_value('Waring', 'Nothing is selected')
            return

        file_name = tree_model.get_value(tree_iter, FILE_NAME)
        file_path = tree_model.get_value(tree_iter, FILE_PATH)

        logger.log_value('Change tree selection to', file_path)

        file_info = self.file_map.get(file_path, EMPTY_FILE_INFO)
        file_data = file_info[FILE_DATA]
        mime_type = file_info[MIME_TYPE]
        is_edited = file_info[IS_EDITED]

        # Get the correct mime type and file icon by reading the file.
        # If the file is a text file or image, load the data.
        if mime_type != 'directory':

            full_file_path = self.get_full_file_path(file_path)
            mime_type = file_utilities.read_mime_type(full_file_path)
            if mime_type != file_info[MIME_TYPE]: file_data = None
            file_icon = file_utilities.get_icon_name(mime_type)

            if mime_type == 'text':

                if not file_data:
                    # Get the file data if the file can be read.
                    file_data = self.create_source_view(full_file_path)
                    is_edited = False

                if not file_data:
                    # If the file could not be read, use a generic icon.
                    file_icon = 'application-x-executable'

                # Set the correct icon, mime type, and file data.
                # (File data may be None).
                tree_model.set_value(tree_iter, FILE_ICON, file_icon)

                self.file_map[file_path][MIME_TYPE] = mime_type
                self.file_map[file_path][FILE_DATA] = file_data
                self.file_map[file_path][IS_EDITED] = is_edited

            elif mime_type == 'image':

                if not file_data:
                    # Get the file data if the file can be read.
                    file_data = self.create_pixbuf(full_file_path)
                    is_edited = False

                if not file_data:
                    # If the file could not be read, use a generic icon.
                    file_icon = 'application-x-executable'

                # Set the correct icon, mime type, and file data.
                # (File data may be None).
                tree_model.set_value(tree_iter, FILE_ICON, file_icon)

                self.file_map[file_path][MIME_TYPE] = mime_type
                self.file_map[file_path][FILE_DATA] = file_data
                self.file_map[file_path][IS_EDITED] = is_edited

            else:

                # Use a generic icon.
                file_icon = 'application-x-executable'
                tree_model.set_value(tree_iter, FILE_ICON, file_icon)
                self.file_map[file_path][MIME_TYPE] = mime_type

        self.selection_changed(file_name, file_path, file_data, mime_type)

    def create_pixbuf(self, full_file_path):
        """
        Create a new pixbuf for an image file.

        Arguments:
        full_file_path : path
            Full file path of the file.

        Returns:
        pixbuf : Pixbuf
            Pixbuf with the image from the file.
        """

        logger.log_value('Create pixbuf for', full_file_path)

        try:

            # Create a new pixbuf.
            pixbuf = Pixbuf.new_from_file(full_file_path)

        except Exception as exception:

            # The exception is gdk-pixbuf-error-quark: Couldn’t
            # recognize the image file format for file
            # gi.repository.GLib.Error: gdk-pixbuf-error-quark: Couldn’t
            # recognize the image file format for file

            logger.log_value('Unable to create pixbuf due to', exception)
            pixbuf = None

        return pixbuf

    def create_source_view(self, full_file_path):
        """
        Create a new source view for a text file.

        Arguments:
        full_file_path : path
            Full file path of the file.

        Returns:
        source_view : GtkSource.View
            A source_view containing text from the file and with
            source_view.file_path as the full file path.
        """

        logger.log_value('Create source view for', full_file_path)

        try:

            with open(full_file_path, 'r') as file:

                # Create a new source view.
                builder = Gtk.Builder.new_from_file(SOURCE_VIEW_UI_FILE_PATH)
                source_view = builder.get_object('source_view')

                # Set font, style, and language of the source buffer.
                source_buffer = source_view.get_buffer()
                source_view.override_font(MONOSPACE_FONT)
                source_buffer.set_style_scheme(SOURCE_STYLE_SCHEME)
                source_buffer.set_language(SOURCE_LANGUAGE)

                # Create a tag to highlight text in the source buffer.
                text_tag = source_buffer.create_tag(tag_name='HIGHLIGHT')
                text_tag.set_property('foreground', 'black')
                # https://www.color-meanings.com/shades-of-yellow-color-names-html-hex-rgb-codes/
                # text_tag.set_property('background', '#FEDF00')  # Yellow (Pantone)
                text_tag.set_property('background', '#FFFE71')  # Pastel Yellow

                # Read file into source view buffer.
                source_buffer.begin_not_undoable_action()
                data = file.read()
                source_buffer.set_text(data)
                source_buffer.end_not_undoable_action()
                source_buffer.set_modified(False)

                # Associate the full file path to the source view.
                source_view.file_path = full_file_path

                # Add the signal handlers for the new source view.
                builder.connect_signals({'on_unmap_source_view': (self.on_unmap_source_view)})

        except Exception as exception:

            # open() throws FileNotFoundError, IsADirectoryError
            # read() throws UnicodeDecodeError

            logger.log_value('Unable to create source view due to', exception)
            source_view = None

        return source_view

    # ------------------------------------------------------------------
    # Source View Handlers
    # ------------------------------------------------------------------

    def on_unmap_source_view(self, source_view):
        """
        Handle unmap events for a GtkSource.View.

        Arguments:
        source_view : GtkSource.View
            A source view with source_view.file_path as the full file path.
        """

        logger.log_value('Close source view for', source_view.file_path)

        # Do not use idle_add to save, because the source buffer:
        # 1. does not get saved when idle_add is used when the window
        #    exits
        # 2. has been unmapped and is not being displayed, so idle_add
        #    is unnecessary
        #
        # GLib.idle_add(save_source_view, source_view)

        self.save_source_view(source_view)

    def save_source_view(self, source_view):
        """
        Save changes to the source view buffer if it has been modified.
        The source_view must have the attribute, file_path, representing
        a full file path.

        Arguments:
        source_view : GtkSource.View
            A source view with source_view.file_path as the full file path.
        """

        source_buffer = source_view.get_buffer()
        # Save the changes.
        is_modified = source_buffer.get_modified()
        if is_modified:
            file_path = self.get_relative_file_path(source_view.file_path)
            logger.log_value('Save changes to', file_path)
            self.file_map[file_path][IS_EDITED] = True

            # Set the file as required since it was modified.
            tree_store = self.tree_model.get_model()
            tree_iter = self.file_map[file_path][TREE_ITER]
            self.set_required_file(tree_store, tree_iter)

            # Write the file.
            with open(source_view.file_path, 'w') as file:
                start_iter = source_buffer.get_start_iter()
                end_iter = source_buffer.get_end_iter()
                data = source_buffer.get_text(start_iter, end_iter, True)
                file.write(data)
                source_buffer.set_modified(False)

        else:
            # TODO: Remove this else clause after testing.
            file_path = self.get_relative_file_path(source_view.file_path)
            logger.log_value('Do not save (no changes)', file_path)

    def update_source_view(self, file_path, edit_source_view):
        """
        Read the file corresponding to the tree iter for the specified
        file path, and store the text or image data. Also, correct the
        file icon in the files tree based on the file's mime type. If
        the file is a text file, then update the source view's source
        buffer using the supplied function, and save the updated source
        buffer.

        Arguments:
        file_path : path
            The file path of the file to update.
        edit_source_view : function
            A function used to make changes to the source view. This
            function may add, delete, update, or highlight text in the
            source view.
        """

        # Note: This method is similar to change_tree_selection()

        logger.log_label('Search and replace in file')
        logger.log_value('File path', file_path)

        file_info = self.file_map.get(file_path, EMPTY_FILE_INFO)
        tree_iter = file_info[TREE_ITER]

        # If the tree iter is not found, simply return.
        # This situation is rare but may occur if the tree model is out
        # of sync with model.options.boot_configurations.
        if not tree_iter:
            logger.log_value('Waring', 'No tree iter found')
            return

        file_data = file_info[FILE_DATA]
        mime_type = file_info[MIME_TYPE]
        is_edited = file_info[IS_EDITED]

        # Get the correct mime type and file icon by reading the file.
        # If the file is a text file or image, load the data.
        if mime_type != 'directory':

            tree_model = self.tree_model.get_model()

            full_file_path = self.get_full_file_path(file_path)
            mime_type = file_utilities.read_mime_type(full_file_path)
            if mime_type != file_info[MIME_TYPE]: file_data = None
            file_icon = file_utilities.get_icon_name(mime_type)

            if mime_type == 'text':

                if not file_data:
                    # Get the file data if the file can be read.
                    file_data = self.create_source_view(full_file_path)
                    is_edited = False

                if not file_data:
                    # If the file could not be read, use a generic icon.
                    file_icon = 'application-x-executable'

                # Set the correct icon, mime type, and file data.
                # (File data may be None).
                tree_model.set_value(tree_iter, FILE_ICON, file_icon)

                self.file_map[file_path][MIME_TYPE] = mime_type
                self.file_map[file_path][FILE_DATA] = file_data
                self.file_map[file_path][IS_EDITED] = is_edited

                if file_data:
                    # Update the source view.
                    update_count = edit_source_view(file_data)
                    logger.log_value('Number of updates', update_count)
                    # Save the source view.
                    self.save_source_view(file_data)

            elif mime_type == 'image':

                if not file_data:
                    # Get the file data if the file can be read.
                    file_data = self.create_pixbuf(full_file_path)
                    is_edited = False

                if not file_data:
                    # If the file could not be read, use a generic icon.
                    file_icon = 'application-x-executable'

                # Set the correct icon, mime type, and file data.
                # (File data may be None).
                tree_model.set_value(tree_iter, FILE_ICON, file_icon)

                self.file_map[file_path][MIME_TYPE] = mime_type
                self.file_map[file_path][FILE_DATA] = file_data
                self.file_map[file_path][IS_EDITED] = is_edited

            else:

                # Use a generic icon.
                file_icon = 'application-x-executable'
                tree_model.set_value(tree_iter, FILE_ICON, file_icon)
                self.file_map[file_path][MIME_TYPE] = mime_type

    ####################################################################
    # Tree Functions
    ####################################################################

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_tree(self, file_path, source_file_path=None):
        """
        Build a tree by inserting the file path into the tree. If the
        file path is being moved, then the source file path must be
        specified.

        Arguments:
        file_path : path
            The relative file path for the new tree iter to be inserted
            into the tree.
        source_file_path : path
            The relative file path of the original file, supplied when a
            file is being moved.

        Returns:
        tree_iter : Gtk.TreeIter
            The tree iter of the file path inserted into the tree.
        """

        logger.log_label('Build tree')

        # Get the parent tree iter.
        parent_file_path = os.path.dirname(file_path)
        parent_tree_iter = self.file_map.get(parent_file_path, EMPTY_FILE_INFO)[TREE_ITER]

        logger.log_value('File path', file_path)
        logger.log_value('Source file path', file_path)

        tree_iter = self._build_tree(file_path, parent_tree_iter, source_file_path, file_path)

        return tree_iter

    def _build_tree(self, file_path, parent_tree_iter, source_base_path, target_base_path):
        """
        Recursively build a tree by inserting the file path below the
        specified parent tree iter. If parent tree iter is None, then
        the file path will be inserted as a root node. If the file path
        is being moved, then the source file path must be specified.

        Arguments:
        file_path : path
            The relative file path for the new tree iter to be inserted
            into the tree.
        parent_tree_iter : Gtk.TreeIter
            The tree iter where the new tree iter(s) will be added. If
            parent tree iter is None, then the file path will be
            inserted as a root tree iter.
        source_base_path : path
            The relative file path of the original file, supplied when a
            file is being moved. This value is propagated unchanged
            through each recursion.
        target_base_path : path
            The relative file path of the new file, supplied when a file
            is being moved. This value is propagated unchanged through
            each recursion.

        Returns:
        tree_iter : Gtk.TreeIter
            The tree iter of the file path inserted into the tree.
        """

        full_file_path = self.get_full_file_path(file_path)
        file_info = self.file_map.get(file_path)

        # logger.log_value('File path', file_path)

        if not source_base_path:

            # The file is being created.

            if not file_info:

                # There is no existing file in the file map.

                # Get info for the original file.
                show_file = False
                file_data = None
                mime_type = file_utilities.guess_mime_type(full_file_path)
                is_edited = False

                # Get the file name.
                file_name = os.path.basename(file_path) if parent_tree_iter else file_path

                # Get the icon name.
                file_icon = file_utilities.get_icon_name(mime_type)

                # Append a new tree iter.
                tree_store = self.tree_model.get_model()
                tree_row = [file_name, file_path, file_icon]
                tree_iter = tree_store.append(parent_tree_iter, tree_row)

                # Save the file information.
                self.file_map[file_path] = [tree_iter, show_file, file_data, mime_type, is_edited]

            else:

                # There is an existing file in the file map.

                # Get the tree iter.
                tree_iter = file_info[TREE_ITER]

                # Update the file information; remove the data because
                # it is invalid.
                self.file_map[file_path][FILE_DATA] = None
                self.file_map[file_path][IS_EDITED] = False

        else:

            # The file is being moved.

            if not file_info:

                # There is no existing file in the file map.

                # Recreate the original file path by replacing the
                # initial portion of the path with the source file path.
                relative_file_path = os.path.relpath(file_path, target_base_path)
                original_file_path = os.path.join(source_base_path, relative_file_path)
                original_file_path = os.path.normpath(original_file_path)

                # The original tree iter was removed in process_file_moved_to().
                # tree_store.remove(original_tree_iter)

                # Remove the original file from the file map.
                original_file_info = self.file_map.pop(original_file_path, EMPTY_FILE_INFO)

                # Get info for the original file.
                show_file = original_file_info[SHOW_FILE]
                file_data = original_file_info[FILE_DATA]
                mime_type = original_file_info[MIME_TYPE]
                is_edited = original_file_info[IS_EDITED]

                # Get the file name.
                file_name = os.path.basename(file_path) if parent_tree_iter else file_path

                # Get the icon name.
                file_icon = file_utilities.get_icon_name(mime_type)

                # Update the full file path, if file data is a source view.
                if file_data and hasattr(file_data, 'file_path'):
                    file_data.file_path = full_file_path

                # Append a new tree iter.
                tree_store = self.tree_model.get_model()
                tree_row = [file_name, file_path, file_icon]
                tree_iter = tree_store.append(parent_tree_iter, tree_row)

                # Save the file information.
                self.file_map[file_path] = [tree_iter, show_file, file_data, mime_type, is_edited]

            else:

                # There is an existing file in the file map.

                # Recreate the original file path by replacing the
                # initial portion of the path with the source file path.
                relative_file_path = os.path.relpath(file_path, target_base_path)
                original_file_path = os.path.join(source_base_path, relative_file_path)
                original_file_path = os.path.normpath(original_file_path)

                # The original tree iter was removed in process_file_moved_to().
                # tree_store.remove(original_tree_iter)

                # Remove the original file from the file map.
                original_file_info = self.file_map.pop(original_file_path, EMPTY_FILE_INFO)

                # Get the tree iter.
                tree_iter = file_info[TREE_ITER]

                # Update the file information; remove the data because
                # it is invalid.
                self.file_map[file_path][FILE_DATA] = None
                self.file_map[file_path][IS_EDITED] = False

        # Continue building the tree store.

        if os.path.isdir(full_file_path):

            file_names = os.listdir(full_file_path)

            for file_name in file_names:

                # self._build_tree(os.path.join(file_path, file_name), tree_iter, source_base_path, target_base_path)
                new_file_path = os.path.join(file_path, file_name)
                self._build_tree(new_file_path, tree_iter, source_base_path, target_base_path)

        return tree_iter

    def filter(self, is_show_all_files):
        """
        Filter tree using the tree_iter_visible() method. This method is
        used by files_tab.

        Arguments:
        is_show_all_files : bool
            True to show all files, or False to only show required files.
        """

        # Set the show all files state.
        self.is_show_all_files = is_show_all_files

        # Filter the tree.

        tree_selection = self.tree_view.get_selection()

        # Block the on_changed_tree_selection handler from being invoked
        # for each row while the tree is being filtered.
        tree_selection.handler_block_by_func(self.on_changed_tree_selection)
        self.tree_model.refilter()
        tree_selection.handler_unblock_by_func(self.on_changed_tree_selection)

        # Handle the current tree selection, since it may have changed.
        self.change_tree_selection(tree_selection)

        # Expand all of the rows in the tree.
        self.tree_view.expand_all()

    def tree_iter_visible(self, tree_store, tree_iter, data):
        """
        Check if the file associated to the tree iter should be shown in
        the tree. If the tree is filtered, then only required files will
        be visible. These are files that are in the initial list of
        required file paths or new files created on the files tab. All
        file paths are relative to the custom disk directory
        ("../custom-disk").

        Arguments:
        tree_store : Gtk.TreeStore
            The tree store for the tree iter.
        tree_iter : Gtk.TreeIter
            The tree iter to be checked.
        data : object
            This is unused.

        Returns:
        show_file : bool
            True if the tree iter should be visible, False otherwise.
        """

        if self.is_show_all_files:
            return True
        else:
            file_path = tree_store.get_value(tree_iter, FILE_PATH)
            show_file = self.file_map.get(file_path, EMPTY_FILE_INFO)[SHOW_FILE]
            return show_file

    def tree_iter_compare(self, tree_store, tree_iter_a, tree_iter_b, data):
        """
        Compare the file names of the supplied tree iters. This method
        is used to sort the tree.

        Arguments:
        tree_store : Gtk.TreeStore
            The tree store for the tree iters.
        tree_iter_a : Gtk.TreeIter
            The first tree iter to compare.
        tree_iter_b : Gtk.TreeIter
            The second tree iter to compare.
        data : object
            This is unused.

        Returns:
        int
            -1, if tree_iter_a is less than tree_iter_b
             0, if tree_iter_a is equal to tree_iter_b
             1, if tree_iter_a is greater than tree_iter_b
        """

        file_name_a = tree_store.get_value(tree_iter_a, FILE_NAME)
        file_name_b = tree_store.get_value(tree_iter_b, FILE_NAME)

        return COLLATOR.compare(file_name_a, file_name_b)

    # ------------------------------------------------------------------
    # Information
    # ------------------------------------------------------------------

    def is_root(self, file_path):
        """
        This method is used in FilesTab.show_pane_for_file()

        Arguments:
        file_path : path
            The relative file path of the file.
        """

        # Get the tree store (Gtk.TreeStore).
        tree_store = self.tree_model.get_model()

        # Get the tree iter.
        tree_iter = self.file_map.get(file_path, EMPTY_FILE_INFO)[TREE_ITER]

        return not bool(tree_store.iter_parent(tree_iter))

    '''
    def is_root(self, tree_model, tree_iter):
        """
        This method is not used.

        Arguments:
        tree_model : Gtk.TreeStore or Gtk.TreeModelFilter
        tree_iter : Gtk.TreeIter
        """

        return not bool(tree_model.iter_parent(tree_iter))
    '''

    def get_selected(self):
        """
        Get the file_name, file_path, and file_data for the selected
        tree iter. This method is used by files_tab.

        Returns:
        file_name : str
            The displayable name of the file.
        file_path : path
            The relative file path of the file.
        file_data : Pixbuf or GtkSource.View
            The data (Pixbuf or GtkSource.View) associated to the file.
        """

        tree_selection = self.tree_view.get_selection()
        tree_model, tree_iter = tree_selection.get_selected()

        file_name = tree_model.get_value(tree_iter, FILE_NAME)
        file_path = tree_model.get_value(tree_iter, FILE_PATH)
        file_info = self.file_map.get(file_path, EMPTY_FILE_INFO)
        # tree_iter = file_info[TREE_ITER]
        # show_file = file_info[SHOW_FILE]
        file_data = file_info[FILE_DATA]
        mime_type = file_info[MIME_TYPE]
        is_edited = file_info[IS_EDITED]

        # TODO: Should we return is_edited? If so files_tab will need to
        #       be updated.
        # return file_name, file_path, file_data, mime_type, is_edited
        return file_name, file_path, file_data, mime_type

    ####################################################################
    # File Event Functions
    ####################################################################

    def remove_watches(self):
        """
        Remove all watches for all files in the tree.
        """

        logger.log_label('Removing all file watches')
        for watch_descriptors in self.watch_descriptors_list:
            self.watch_manager.rm_watch(list(watch_descriptors.values()))

        # Stop the event loop.
        logger.log_value('Event loop', 'Stopped')
        self.event_loop.stop()

    def process_file_close_write(self, event):
        """
        Update the tree when a file or directory is created.

        Arguments:
        event : pyinotify.Event
        """

        logger.log_label('Process close write')
        logger.log_value('Path name', event.pathname)
        logger.log_value('Base name', event.name)
        logger.log_value('Watch Descriptors', self.watch_descriptors_list)
        '''
        # Make the file executable by all if it has the ".sh" extension.
        if event.name.endswith('.sh'):
            logger.log_value('Make file executable', event.name)
            old_mode = os.stat(event.pathname).st_mode
            new_mode = old_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            os.chmod(event.pathname, new_mode)
        '''

        file_path = self.get_relative_file_path(event.pathname)
        file_info = self.file_map.get(file_path, EMPTY_FILE_INFO)
        is_edited = file_info[IS_EDITED]

        if not is_edited:

            # Edits were made outside of Cubic.

            logger.log_value('File changed by', 'External')

            source_view = file_info[FILE_DATA]
            if source_view:
                # To prevent Cubic from overwriting a file that has been
                # modified outside of Cubic, mark the buffer as
                # unmodified. Each time a displayed file is edited, its
                # buffer is marked as modified. If the file is
                # overwritten outside of Cubic, the file will reload,
                # but its buffer will still contain the recent edits.
                # When this file is unmapped, the modified buffer will
                # be saved, overwriting the file with old buffer data.
                # The save_source_view() method checks to see if the
                # buffer has been modified before saving a file, so
                # marking the buffer as unmodified will prevented this.
                logger.log_value('Undo buffer', 'Reset')
                source_buffer = source_view.get_buffer()
                source_buffer.set_modified(False)

            # Set the file data as None, so the file will be reloaded
            # when it is displayed.
            logger.log_value('Unload file data', file_path)
            self.file_map[file_path][FILE_DATA] = None

            # If this file is being displayed, reload it.
            selected_file_path = self.get_selected()[1]
            logger.log_value('The selected file path is', selected_file_path)
            if selected_file_path == file_path:
                # If the modified file is being displayed, refresh the
                # display.
                logger.log_value('Reload selected file', selected_file_path)
                tree_selection = self.tree_view.get_selection()
                self.change_tree_selection(tree_selection)

        else:

            # Reset is_edited since the file has been saved.

            logger.log_value('File changed by', 'Cubic')
            logger.log_value('Undo buffer', 'Do not reset')
            self.file_map[file_path][IS_EDITED] = False

    def process_file_create(self, event):
        """
        Update the tree when a file or directory is created, or when a
        file or directory is moved into the tree from outside.

        Arguments:
        event : pyinotify.Event
        """

        logger.log_label('Process file create')
        logger.log_value('Path name', event.pathname)
        logger.log_value('Base name', event.name)
        logger.log_value('Watch Descriptors', self.watch_descriptors_list)

        # Add executable permissions to created files that have the *.sh
        # extension. This applies to new files and files moved into the
        # tree from outside. Files moved into the tree from outside
        # without the *.sh extension retain their existing permissions.
        if event.name.endswith('.sh'):
            # Make the file executable.
            logger.log_value('Make the file executable', event.name)
            mode = os.stat(event.pathname).st_mode
            logger.log_value('The old mode is', oct(mode)[-3:])
            mode = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            logger.log_value('Change the mode to', oct(mode)[-3:])
            os.chmod(event.pathname, mode)
            mode = os.stat(event.pathname).st_mode
            logger.log_value('The new mode is', oct(mode)[-3:])

        # Get the tree store (Gtk.TreeStore).
        tree_store = self.tree_model.get_model()

        # Get the relative file path.
        file_path = self.get_relative_file_path(event.pathname)

        # Add the new row.
        tree_iter = self.build_tree(file_path)

        # Set the new file as 'is required', and re-filter the tree.
        self.set_required_file(tree_store, tree_iter)
        self.tree_model.refilter()

        # Select the new file in the tree, if the file was created by
        # the create_file() or the create_directory() functions.
        if file_path == self.target_file_path:

            # Convert the tree_store tree_iter to the displayable
            # tree_model tree_iter.
            is_iter_valid, tree_iter = self.tree_model.convert_child_iter_to_iter(tree_iter)

            if is_iter_valid:

                # Select the new file in the tree.
                tree_path = self.tree_model.get_path(tree_iter)
                self.tree_view.expand_to_path(tree_path)
                tree_selection = self.tree_view.get_selection()
                tree_selection.select_iter(tree_iter)
                tree_column = self.tree_view.get_column(0)
                self.tree_view.scroll_to_cell(tree_path, tree_column, True, 0.5, 0.0)

                # After the selection changes, the new file will be
                # displayed in the file pane and the header bar buttons
                # will be reset by the selection_changed() callback
                # function.

            self.target_file_path = None

    def process_file_delete(self, event):
        """
        Update the tree when a file or directory is deleted. The
        IN_DELETE event is generated for each file and directory inside
        a directory that is deleted.

        Arguments:
        event : pyinotify.Event
        """

        logger.log_label('Process file delete')
        logger.log_value('Path name', event.pathname)
        logger.log_value('Base name', event.name)
        logger.log_value('Watch Descriptors', self.watch_descriptors_list)

        # Get the tree store (Gtk.TreeStore).
        tree_store = self.tree_model.get_model()

        # Get the relative file path.
        file_path = self.get_relative_file_path(event.pathname)

        # Get the parent tree iter.
        parent_file_path = os.path.dirname(file_path)
        parent_tree_iter = self.file_map.get(parent_file_path, EMPTY_FILE_INFO)[TREE_ITER]

        # Get the tree iter.
        tree_iter = self.file_map.get(file_path, EMPTY_FILE_INFO)[TREE_ITER]

        # Convert the tree_store tree_iter to the displayable
        # tree_model tree_iter.
        tree_selection = self.tree_view.get_selection()

        # Determine if the tree iter is selected.
        is_iter_valid, display_tree_iter = self.tree_model.convert_child_iter_to_iter(tree_iter)
        is_selected = tree_selection.iter_is_selected(display_tree_iter)

        # Remove the row.
        tree_store.remove(tree_iter)

        # Remove the file information.
        self.file_map.pop(file_path, EMPTY_FILE_INFO)

        # Select the parent in the tree, if the deleted tree iter was
        # previously selected. If the file was deleted by the
        # delete_file() or the delete_directory() functions, then the
        # tree iter will have been previously selected.
        if is_selected:

            # Convert the tree_store tree_iter to the displayable
            # tree_model tree_iter.
            is_iter_valid, tree_iter = self.tree_model.convert_child_iter_to_iter(parent_tree_iter)

            if is_iter_valid:

                # Select the new file in the tree.
                tree_path = self.tree_model.get_path(tree_iter)
                self.tree_view.expand_to_path(tree_path)
                tree_selection = self.tree_view.get_selection()
                tree_selection.select_iter(tree_iter)
                tree_column = self.tree_view.get_column(0)
                self.tree_view.scroll_to_cell(tree_path, tree_column, True, 0.5, 0.0)

                # After the selection changes, the new file will be
                # displayed in the file pane and the header bar buttons
                # will be reset by the selection_changed() callback
                # function.

            self.target_file_path = None

    def process_file_moved_to(self, event):
        """
        Update the tree when a file or directory is moved to another
        directory in the tree.

        Arguments:
        event : pyinotify.Event
        """

        logger.log_label('Process file moved to')
        logger.log_value('Path name', event.pathname)
        logger.log_value('Source path name', event.src_pathname)
        logger.log_value('Base name', event.name)
        logger.log_value('Watch Descriptors', self.watch_descriptors_list)

        # Add executable permissions to files that are renamed with the
        # *.sh extension. Remove executable permissions from files that
        # are renamed without the *.sh extension.
        if not event.src_pathname.endswith('.sh') and event.name.endswith('.sh'):
            # Make the file executable.
            logger.log_value('Make file executable', event.name)
            mode = os.stat(event.pathname).st_mode
            logger.log_value('The old mode is', oct(mode)[-3:])
            mode = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            logger.log_value('Change the mode to', oct(mode)[-3:])
            os.chmod(event.pathname, mode)
            mode = os.stat(event.pathname).st_mode
            logger.log_value('The new mode is', oct(mode)[-3:])
        if event.src_pathname.endswith('.sh') and not event.name.endswith('.sh'):
            # Make the file non-executable.
            logger.log_value('Make the file non-executable', event.name)
            mode = os.stat(event.pathname).st_mode
            logger.log_value('The old mode is', oct(mode)[-3:])
            mode = mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH
            logger.log_value('Change the mode to', oct(mode)[-3:])
            os.chmod(event.pathname, mode)
            mode = os.stat(event.pathname).st_mode
            logger.log_value('The new mode is', oct(mode)[-3:])

        # Get the tree store (Gtk.TreeStore).
        tree_store = self.tree_model.get_model()

        # Get the relative file path.
        target_file_path = self.get_relative_file_path(event.pathname)

        # Remove the tree iter.
        source_file_path = self.get_relative_file_path(event.src_pathname)
        source_tree_iter = self.file_map.get(source_file_path, EMPTY_FILE_INFO)[TREE_ITER]

        # Remove the row.
        if source_tree_iter: tree_store.remove(source_tree_iter)

        # Add the new row.
        tree_iter = self.build_tree(target_file_path, source_file_path)

        # Set the new file as 'is required', and re-filter the tree.
        self.set_required_file(tree_store, tree_iter)
        self.tree_model.refilter()

        # Select the new file in the tree, if the file was created by
        # the rename_file() or the rename_directory() functions.
        if target_file_path == self.target_file_path:

            # Convert the tree_store tree_iter to the displayable
            # tree_model tree_iter.
            is_iter_valid, tree_iter = self.tree_model.convert_child_iter_to_iter(tree_iter)

            if is_iter_valid:

                # Select the new file in the tree.
                tree_path = self.tree_model.get_path(tree_iter)
                self.tree_view.expand_to_path(tree_path)
                tree_selection = self.tree_view.get_selection()
                tree_selection.select_iter(tree_iter)
                tree_column = self.tree_view.get_column(0)
                self.tree_view.scroll_to_cell(tree_path, tree_column, True, 0.5, 0.0)

                # After the selection changes, the new file will be
                # displayed in the file pane and the header bar buttons
                # will be reset by the selection_changed() callback
                # function.

            self.target_file_path = None

    ####################################################################
    # Required File Path Functions
    ####################################################################

    def set_required_files(self, tree_model, required_file_paths):
        """
        For each file in the required_file_paths list, designate the
        corresponding tree_iter and its parents as 'required'.

        Arguments:
        tree_model : Gtk.TreeStore or Gtk.TreeModel
        required_file_paths : list of path
            List of required relative file paths, excluding paths ending
            in directories.
        """

        for file_path in required_file_paths:
            tree_iter = self.file_map.get(file_path, EMPTY_FILE_INFO)[TREE_ITER]
            self.set_required_file(tree_model, tree_iter)

    def set_required_file(self, tree_model, tree_iter):
        """
        Recursively traverse the up the tree, designating parent
        tree_iters as 'required', until a parent tree_iter that is
        already designated as 'required' is encountered, or until the
        root tree_iter is reached.

        Arguments:
        tree_model : Gtk.TreeStore or Gtk.TreeModel
        tree_iter : Gtk.TreeIter
            A tree_iter for the tree_model.
        """

        # Stop processing if the tree iter is None. This will happen
        # whenever the corresponding required file path does not exist.
        if not tree_iter: return

        # Set this tree iter as 'is required'.
        file_path = tree_model.get_value(tree_iter, FILE_PATH)
        self.file_map[file_path][SHOW_FILE] = True

        # Get the parent tree iter.
        tree_iter = tree_model.iter_parent(tree_iter)

        # Stop traversing if this is the root (there is not parent).
        if not tree_iter: return

        # Get parent tree iter 'is required'.
        file_path = tree_model.get_value(tree_iter, FILE_PATH)
        show_file = self.file_map.get(file_path, EMPTY_FILE_INFO)[SHOW_FILE]

        # Stop traversing if the parent tree iter already 'is required'.
        if show_file: return

        # Otherwise, recursively update the tree.
        self.set_required_file(tree_model, tree_iter)

    def get_required_file_paths(self):
        """
        Create a sorted list of required relative file paths, excluding
        paths ending in directories. This method is used by files_tab.

        Returns:
        file_paths - List of required relative file paths.
        """

        file_paths = []
        for file_path, file_info in self.file_map.items():
            show_file = file_info[SHOW_FILE]
            if show_file:
                full_file_path = self.get_full_file_path(file_path)
                if os.path.isfile(full_file_path):
                    file_paths.append(file_path)
        file_paths.sort()

        return file_paths

    ####################################################################
    # Miscellaneous Functions
    ####################################################################

    def get_full_file_path(self, file_path):
        """
        Convert the relative file path to a full file path by appending
        the custom disk directory ("../custom-disk").

        Arguments:
        file_path : path
            File path, relative to the custom disk directory
            ("../custom-disk").

        Returns:
        file_path : path
            A full file path.
        """

        file_path = os.path.join(model.project.custom_disk_directory, file_path)

        return file_path

    def get_relative_file_path(self, file_path):
        """
        Convert the full file path to a relative file path by trimming
        the custom disk directory ("../custom-disk") from the beginning.

        Arguments:
        file_path : path
            Full path, containing the custom disk directory
            ("../custom-disk").

        Returns:
        file_path : path
            A relative file path.
        """

        file_path = os.path.relpath(file_path, model.project.custom_disk_directory)

        return file_path
