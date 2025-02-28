#!/usr/bin/python3

########################################################################
#                                                                      #
# options_page.py                                                      #
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

# TODO: Explicitly set model.options.boot_configurations to the default
#       value if it is None or empty (usually due to an exception).
# TODO: Set header widgets visible or hidden for all actions in the
#       start(), enter(), and leave() functions, and in all map and
#       unmap functions.

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

import gi
import os

gi.require_version('GLib', '2.0')

from gi.repository import GLib

from cubic.constants import BOLD_RED, NORMAL
from cubic.pages.boot_tab import BootTab
from cubic.pages.kernel_tab import KernelTab
from cubic.pages.preseed_tab import PreseedTab
from cubic.utilities import displayer
from cubic.utilities import file_utilities
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.processor import execute_synchronous

########################################################################
# Global Variables & Constants
########################################################################

name = 'options_page'

kernel_tab = None
preseed_tab = None
boot_tab = None

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

    if action == 'back':

        validate_page()

        displayer.set_visible('title_label', False)
        displayer.set_visible('options_page__stack_switcher', True)

        return

    if action == 'cancel':

        validate_page()

        displayer.set_visible('title_label', False)
        displayer.set_visible('options_page__stack_switcher', True)

        return

    if action == 'copy-preseed':

        validate_page()

        displayer.set_visible('title_label', False)
        displayer.set_visible('options_page__stack_switcher', True)

        return

    if action == 'copy-boot':

        validate_page()

        displayer.set_visible('title_label', False)
        displayer.set_visible('options_page__stack_switcher', True)

        return

    elif action == 'next':

        # Setup the Kernel tab.
        GLib.idle_add(setup_kernel_tab)

        # Setup the Preseed tab.
        GLib.idle_add(setup_preseed_tab)

        # Setup the Boot tab.
        GLib.idle_add(setup_boot_tab)

        validate_page()

        displayer.set_visible('title_label', False)
        displayer.set_visible('options_page__stack_switcher', True)

        return

    elif action == 'next-options':

        # Setup the Kernel tab.
        GLib.idle_add(setup_kernel_tab)

        # Setup the Preseed tab.
        GLib.idle_add(setup_preseed_tab)

        # Setup the Boot tab.
        GLib.idle_add(setup_boot_tab)

        validate_page()

        displayer.set_visible('title_label', False)
        displayer.set_visible('options_page__stack_switcher', True)

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

    if action == 'back':

        return

    elif action == 'cancel':

        return

    elif action == 'copy-preseed':

        return

    elif action == 'copy-boot':

        return

    elif action == 'next':

        return

    elif action == 'next-options':

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

    if action == 'back':

        # Show the Packages page.

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('title_label', True)
        displayer.set_visible('options_page__stack_switcher', False)

        # displayer.set_visible('kernel_tab__header_bar_box', False)
        displayer.set_visible('preseed_tab__header_bar_box', False)
        displayer.set_visible('boot_tab__header_bar_box', False)

        # Update the model to acknowledge changes.
        model.options.boot_configurations = boot_tab.get_required_file_paths()

        preseed_tab.remove_tree()
        boot_tab.remove_tree()

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'copy-preseed':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('title_label', True)
        displayer.set_visible('options_page__stack_switcher', False)

        # Update the model to acknowledge changes.
        model.options.boot_configurations = boot_tab.get_required_file_paths()

        return

    elif action == 'copy-boot':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('title_label', True)
        displayer.set_visible('options_page__stack_switcher', False)

        # Update the model to acknowledge changes.
        model.options.boot_configurations = boot_tab.get_required_file_paths()

        return

    elif action == 'back-terminal':

        # Do not show the Packages page.

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('title_label', True)
        displayer.set_visible('options_page__stack_switcher', False)

        # displayer.set_visible('kernel_tab__header_bar_box', False)
        displayer.set_visible('preseed_tab__header_bar_box', False)
        displayer.set_visible('boot_tab__header_bar_box', False)

        # Update the model to acknowledge changes.
        model.options.boot_configurations = boot_tab.get_required_file_paths()

        preseed_tab.remove_tree()
        boot_tab.remove_tree()

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'next':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        displayer.set_visible('title_label', True)
        displayer.set_visible('options_page__stack_switcher', False)

        # displayer.set_visible('kernel_tab__header_bar_box', False)
        displayer.set_visible('preseed_tab__header_bar_box', False)
        displayer.set_visible('boot_tab__header_bar_box', False)

        # Update the model to acknowledge changes.
        model.options.boot_configurations = boot_tab.get_required_file_paths()

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Update the model to acknowledge changes.
        model.options.boot_configurations = boot_tab.get_required_file_paths()

        preseed_tab.remove_tree()
        boot_tab.remove_tree()

        # Save the model values.
        model.project.configuration.save()

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


def on_map__options_page__kernel_tab(*args):

    logger.log_label('Show Options page, Kernel tab')
    # displayer.set_visible('kernel_tab__header_bar_box', True)

    # displayer.set_visible('kernel_tab__header_bar_box', False)
    displayer.set_visible('preseed_tab__header_bar_box', False)
    displayer.set_visible('boot_tab__header_bar_box', False)


def on_unmap__options_page__kernel_tab(*args):

    logger.log_value('Leave', 'Options page Kernel tab')
    # displayer.set_visible('kernel_tab__header_bar_box', False)

    # Update the boot configurations if the selected kernel has changed.
    if kernel_tab.selected_kernel_index != model.selected_kernel_index:

        # Save the selected kernel in the model.
        model.selected_kernel_index = kernel_tab.selected_kernel_index

        # Update the boot configurations based on the selected kernel.
        GLib.idle_add(boot_tab.update_boot_configurations, model.options.boot_configurations)


def on_map__options_page__preseed_tab(*args):

    logger.log_label('Show Options page, Preseed tab')

    # displayer.set_visible('kernel_tab__header_bar_box', False)
    displayer.set_visible('preseed_tab__header_bar_box', True)
    displayer.set_visible('boot_tab__header_bar_box', False)


def on_unmap__options_page__preseed_tab(*args):

    logger.log_value('Leave', 'Options page Preseed tab')

    displayer.set_visible('preseed_tab__header_bar_box', False)


def on_map__options_page__boot_tab(*args):

    logger.log_label('Show Options page, Boot tab')

    # displayer.set_visible('kernel_tab__header_bar_box', False)
    displayer.set_visible('preseed_tab__header_bar_box', False)
    displayer.set_visible('boot_tab__header_bar_box', True)


def on_unmap__options_page__boot_tab(*args):

    logger.log_value('Leave', 'Options page Boot tab')

    displayer.set_visible('boot_tab__header_bar_box', False)


########################################################################
# Support Functions
########################################################################


def setup_kernel_tab():
    """
    Setup the Kernel tab.
    This function must be invoked using GLib.idle_add().
    """

    global kernel_tab
    if not kernel_tab:

        # Load the user interface and connect the signals to handlers in
        # the associated module.
        kernel_tab = KernelTab()

        grid = model.builder.get_object('options_page__kernel_tab__grid')
        scrolled_window = model.builder.get_object('kernel_tab__scrolled_window')
        grid.attach(scrolled_window, 0, 1, 1, 1)

        # Add previously loaded widgets to the header bar.
        # header_bar = model.builder.get_object('header_bar')
        # box = model.builder.get_object('kernel_tab__header_bar_box')
        # header_bar.add(box)
        # box.set_visible(False)

    # Create the list of kernels.
    kernel_tab.create_linux_kernels_list()

    # Save the selected kernel in the model.
    model.selected_kernel_index = kernel_tab.selected_kernel_index


def setup_preseed_tab():
    """
    Setup the Preseed tab.
    This function must be invoked using GLib.idle_add().
    """

    global preseed_tab
    if not preseed_tab:

        # Load the user interface and connect the signals to handlers in
        # the associated module.
        preseed_tab = PreseedTab()

        grid = model.builder.get_object('options_page__preseed_tab__grid')
        panes = model.builder.get_object('preseed_tab__panes')
        grid.attach(panes, 0, 1, 1, 1)

        # Add previously loaded widgets to the header bar.
        header_bar = model.builder.get_object('header_bar')
        box = model.builder.get_object('preseed_tab__header_bar_box')
        header_bar.add(box)
        box.set_visible(False)

    # Ensure root directories in the files tree exist, in order to avoid
    # FileNotFoundError errors and to allow adding new items to them.

    # If the preseed directory does not exist, create it. The preseed
    # directory is optional.
    file_path = os.path.join(model.project.custom_disk_directory, 'preseed')
    file_utilities.make_directory(file_path)

    # Create the list of preseed files.
    preseed_tab.create_tree(['preseed'])


def setup_boot_tab():
    """
    Setup the Boot tab.
    This function must be invoked using GLib.idle_add().
    """

    # Boot configuration files:
    #
    # Ubuntu
    # • isolinux/txt.cfg
    #
    # Linux Mint (Bug #1885464)
    # • isolinux/isolinux.cfg
    #
    # Elementry
    # • isolinux/live.cfg
    #
    # Debian (Enhancement GH:#114)
    # • isolinux/menu.cfg
    #
    # Grml Live Linux (Enhancement GH:#93)
    # • boot/grub/grml64full_default.cfg
    # • boot/grub/grml64full_options.cfg
    # • boot/isolinux/default.cfg
    # • boot/isolinux/grml.cfg
    # • boot/isolinux/hidden.cfg

    # Prepare the boot tab.

    global boot_tab
    if not boot_tab:

        # Load the user interface and connect the signals to handlers in
        # the associated module.
        boot_tab = BootTab()

        grid = model.builder.get_object('options_page__boot_tab__grid')
        panes = model.builder.get_object('boot_tab__panes')
        grid.attach(panes, 0, 1, 1, 1)

        # Add previously loaded widgets to the header bar.
        header_bar = model.builder.get_object('header_bar')
        box = model.builder.get_object('boot_tab__header_bar_box')
        header_bar.add(box)
        box.set_visible(False)

    # Identify relative root directories for the boot configurations.
    # Ensure root directories in the files tree exist, in order to avoid
    # FileNotFoundError errors and to allow adding new items to them.

    root_file_paths = []

    # The boot directory is required. If it does not exist, create it.
    file_path = os.path.join(model.project.custom_disk_directory, 'boot')
    file_utilities.make_directories(file_path)
    if os.path.isdir(file_path):
        root_file_paths.append('boot')

    # The isolinux directory is optional.
    file_path = os.path.join(model.project.custom_disk_directory, 'isolinux')
    # file_utilities.make_directories(file_path)
    if os.path.isdir(file_path):
        root_file_paths.append('isolinux')

    # Get the the boot configuration files. These are text files located
    # in the root file paths that contain the words vmlinuz and initrd.
    if not model.options.boot_configurations:
        # Use raw string ("r") to avoid syntax warninings. See GH:#340.
        # - SyntaxWarning: invalid escape sequence '\|'
        # - SyntaxWarning: invalid escape sequence '\;'
        command = rf'find {" ".join(root_file_paths)} -type f -exec grep -HiIl "linux.*vmlinuz\|kernel.*vmlinuz" {{}} \;'
        result, exit_status, signal_status = execute_synchronous(command, model.project.custom_disk_directory)
        model.options.boot_configurations = result.split()

    # Create the tree of boot configurations files.
    # boot_tab.create_tree(['boot/grub', 'isolinux'], model.options.boot_configurations)
    boot_tab.create_tree(root_file_paths, model.options.boot_configurations)

    # Update the boot configurations based on the selected kernel.
    # Since _setup_boot_tab was invoked using GLib.idle_add(), there is
    # no need to use GLib.idle_add() here.
    boot_tab.update_boot_configurations(model.options.boot_configurations)


########################################################################
# Validation Functions
########################################################################


def validate_page():
    """
    Determine if the Packages page should be skipped.
    """

    if model.layout.standard_remove_file_name:
        # Show the Packages page.
        # logger.log_value('Show the Packages page?', 'Yes')
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

    else:
        # Do not show the Packages page.
        # logger.log_value('Show the Packages page?', 'No')
        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back-terminal',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Next❭',
            next_action='next',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)
