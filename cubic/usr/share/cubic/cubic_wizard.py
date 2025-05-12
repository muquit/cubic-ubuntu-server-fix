#!/usr/bin/python3

########################################################################
#                                                                      #
# cubic_wizard.py                                                      #
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

import argcomplete
import argparse
import gi
import glob
import importlib
import mimetypes
import os
import traceback

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk

from cubic.constants import CUBIC_COPYRIGHT
from cubic.constants import STAR, CUBIC_WEBSITE, CUBIC_WIKI, CUBIC_PAGE_HELP, CUBIC_DONATE, CUBIC_SITES, CUBIC_URLS
from cubic import navigator
from cubic.utilities import constructor
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Arguments
########################################################################

parser = argparse.ArgumentParser(
    prog='cubic',
    description='Cubic (Custom Ubuntu ISO Creator) is a GUI wizard to create a customized Live ISO image for Ubuntu and Debian based distributions.')
parser.add_argument('directory', nargs='?', help='directory for a new or existing project')
parser.add_argument('iso', nargs='?', help='original ISO file for a new project (ignored for existing projects)')
parser.add_argument("-l", "--log", action="store_true", help="output a formatted log to a file in the project directory")
parser.add_argument("-v", "--verbose", action="store_true", help="output a formatted log to the console")
parser.add_argument("-V", "--version", action="store_true", help="print version information and exit")

if os.getuid() == 0:
    print('Error: Cubic may not be run using sudo or as root because it is a graphical user interface application.')
    print()
    parser.print_help()
    print()
    exit()

argcomplete.autocomplete(parser)
arguments = parser.parse_args()

if arguments.version:
    version = constructor.get_package_version('cubic')
    display_version = constructor.get_display_version(version)
    urls = constructor.decode_object(CUBIC_URLS)
    website = urls[CUBIC_WEBSITE]
#    print(f'Cubic version... {display_version}')
#    print(f'Copyright....... {CUBIC_COPYRIGHT}')
#    print(f'Website......... {website}')
    print(f"Cubic version... {display_version}-ubuntu-server-fix")
    print(f'Copyright....... {CUBIC_COPYRIGHT}')
    print(f'Website......... {website}')
    print(f'Modified by..... Muhammad Muquit https://www.muquit.com/')
    print(f'Fix URL......... https://github.com/muquit/cubic-ubuntu-server-fix')


    exit()

########################################################################
# Main Application
########################################################################

logger.verbose = arguments.verbose
logger.log = arguments.log
logger.log_title('Cubic - Custom Ubuntu ISO Creator')

try:

    # ------------------------------------------------------------------
    # Initialize.
    # ------------------------------------------------------------------

    # Real path is necessary here.
    model.application.directory = os.path.dirname(os.path.realpath(__file__))

    # Get the user's home directory.
    model.application.user_home = os.path.expanduser('~')

    # Get the running Cubic version.
    model.application.cubic_version = constructor.get_package_version('cubic')
    ### TODO: FOR TESTING ONLY
    ### model.application.cubic_version = '2024.08-87-release~202402210132~ubuntu23.10.1'

    # Get the running kernel version.
    model.application.kernel_version = constructor.get_kernel_version()

    # Set model values from the command line arguments, if supplied.
    if arguments.directory:
        # logger.log_value('Project directory argument', arguments.directory)
        model.arguments.directory = os.path.realpath(arguments.directory)
    if arguments.iso:
        # logger.log_value('Original ISO file path argument', arguments.iso)
        model.arguments.file_path = os.path.realpath(arguments.iso)

    # Add additional mime types.
    mimetypes.init()
    file_path = os.path.join(model.application.directory, 'assets', 'mime.types')
    mimetypes.types_map.update(mimetypes.read_mime_types(file_path))

    # ------------------------------------------------------------------
    # Create the user interface.
    # ------------------------------------------------------------------

    # Load the user interface.
    file_path = os.path.join(model.application.directory, 'cubic_wizard.ui')
    model.builder = Gtk.Builder.new_from_file(file_path)

    # Connect the signals to handlers in the associated module.
    model.builder.connect_signals(navigator)

    #
    # Pages
    #

    logger.log_label('Setup pages')

    # Get the stack.
    pages = model.builder.get_object('pages')

    # Setup each page.
    pattern = os.path.join(model.application.directory, 'cubic', 'pages', '*_page.ui')
    file_paths = sorted(glob.glob(pattern))
    for file_path in file_paths:

        # Get the module name.
        module_name = os.path.basename(file_path)[:-3]
        logger.log_value('Setup', module_name.replace('_', ' '))

        # Load the user interface.
        model.builder.add_from_file(file_path)

        # Load the module.
        module = importlib.import_module(f'cubic.pages.{module_name}')

        # Connect the signals to handlers in the associated module.
        model.builder.connect_signals(module)

        # Add the page to the stack.
        page = model.builder.get_object(module.name)
        pages.add_named(page, module.name)

    # Set the first page for the stack.
    page = model.builder.get_object('start_page')
    pages.set_visible_child(page)

    #
    # Header Bar
    #

    # Add previously loaded widgets to the header bar.

    # TODO: Can adding widgets to the header bar be moved to the individual pages?

    header_bar = model.builder.get_object('header_bar')

    # Project page
    widget = model.builder.get_object('project_page__test_header_bar_button')
    header_bar.add(widget)
    widget = model.builder.get_object('project_page__delete_header_bar_button')
    header_bar.add(widget)
    widget = model.builder.get_object('project_page__header_bar_box')
    header_bar.add(widget)

    # Packages page
    widget = model.builder.get_object('packages_page__header_bar_box_1')
    header_bar.add(widget)
    widget = model.builder.get_object('packages_page__header_bar_box_2')
    header_bar.add(widget)

    # Options page
    options_page__stack_switcher = model.builder.get_object('options_page__stack_switcher')
    options_page__stack = model.builder.get_object('options_page__stack')
    options_page__stack_switcher.set_stack(options_page__stack)

    # Terminal page
    widget = model.builder.get_object('terminal_page__copy_header_bar_button')
    header_bar.add(widget)

    # Finish page
    widget = model.builder.get_object('finish_page__test_header_bar_button')
    header_bar.add(widget)

    #
    # Menu
    #

    # Alert label
    widget = model.builder.get_object('alert_label')
    # Show the alert label if all of the sites have not been visited.
    # widget.set_visible(len(model.application.visited_sites) < len(CUBIC_SITES))
    # Do not show the alert label.
    widget.set_visible(False)

    # Menu items
    # Uncomment the lines below to show a ★ next to the menu item.
    # Remember to uncomment lines in navigator.on_clicked_?_menu_button()
    # functions to remove the ★ once the site has been visited.

    # if CUBIC_WIKI not in model.application.visited_sites:
    #     widget = model.builder.get_object('wiki_menu_button')
    #     label = widget.props.text
    #     new_text = constructor.add_prefix(STAR, label)
    #     if new_text: widget.props.text = new_text

    # if CUBIC_PAGE_HELP not in model.application.visited_sites:
    #     widget = model.builder.get_object('page_help_menu_button')
    #     label = widget.props.text
    #     new_text = constructor.add_prefix(STAR, label)
    #     if new_text: widget.props.text = new_text

    # if CUBIC_WEBSITE not in model.application.visited_sites:
    #     widget = model.builder.get_object('website_menu_button')
    #     label = widget.props.text
    #     new_text = constructor.add_prefix(STAR, label)
    #     if new_text: widget.props.text = new_text

    # if CUBIC_ABOUT not in model.application.visited_sites:
    #     widget = model.builder.get_object('about_menu_button')
    #     label = widget.props.text
    #     new_text = constructor.add_prefix(STAR, label)
    #     if new_text: widget.props.text = new_text

    # if CUBIC_DONATE not in model.application.visited_sites:
    #     widget = model.builder.get_object('donate_menu_button')
    #     label = widget.get_label()
    #     new_text = constructor.add_prefix(STAR, label)
    #     if new_text: widget.set_label(new_text)

    #
    # File Choosers
    #

    logger.log_label('Setup file choosers')

    pattern = os.path.join(model.application.directory, 'cubic', 'choosers', '*_chooser.ui')
    file_paths = sorted(glob.glob(pattern))
    for file_path in file_paths:

        # Get the module name.
        module_name = os.path.basename(file_path)[:-3]
        logger.log_value('Setup', module_name.replace('_', ' '))

        # Load the user interface.
        model.builder.add_from_file(file_path)

        # Load the module.
        module = importlib.import_module(f'cubic.choosers.{module_name}')

        # Connect the signals to handlers in the associated module.
        model.builder.connect_signals(module)

    # ------------------------------------------------------------------
    # Start the user interface.
    # ------------------------------------------------------------------

    # Show the window.
    window = model.builder.get_object('window')
    window.show()

    # Open the application.
    navigator.handle_navigation('open')

    # Start the Gtk main loop.
    Gtk.main()

except Exception as exception:
    logger.log_value('Exception', exception)
    logger.log_value('The trace back is', traceback.format_exc())
