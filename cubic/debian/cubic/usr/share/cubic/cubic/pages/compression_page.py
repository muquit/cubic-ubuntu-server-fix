#!/usr/bin/python3

########################################################################
#                                                                      #
# compression_page.py                                                  #
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

# https://catchchallenger.first-world.info/wiki/Quick_Benchmark:_Gzip_vs_Bzip2_vs_LZMA_vs_XZ_vs_LZ4_vs_LZO#The_file_test_results
# http://www.ilsistemista.net/index.php/linux-a-unix/44-linux-compressors-comparison-on-centos-6-5-x86-64-lzo-vs-lz4-vs-gzip-vs-bzip2-vs-lzma.html?start=4
# https://fastcompression.blogspot.com/2015/01/zstd-stronger-compression-algorithm.html

########################################################################
# Imports
########################################################################

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import LZ4, LZO, GZIP, ZSTD, XZ
from cubic.pages import options_page
from cubic.utilities import displayer
from cubic.utilities import iso_utilities
from cubic.utilities import logger
from cubic.utilities import model

########################################################################
# Global Variables & Constants
########################################################################

name = 'compression_page'

radio_buttons = {
    LZ4: 'compression_page__radio_button_1',
    LZO: 'compression_page__radio_button_2',
    GZIP: 'compression_page__radio_button_3',
    ZSTD: 'compression_page__radio_button_4',
    XZ: 'compression_page__radio_button_5'
}

compression = None

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

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Generate❭',
            next_action='generate',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        return

    elif action == 'next':

        displayer.reset_buttons(
            back_button_label='❬Back',
            back_action='back',
            back_button_style=None,
            is_back_sensitive=True,
            is_back_visible=True,
            next_button_label='Generate❭',
            next_action='generate',
            next_button_style='suggested-action',
            is_next_sensitive=True,
            is_next_visible=True)

        # 1 = lz4
        # 2 = lzo
        # 3 = gzip
        # 4 = zstd
        # 5 = xz

        # Display the initial selection.
        global compression
        compression = model.options.compression
        displayer.activate_radio_button(radio_buttons[compression], True)

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

    elif action == 'next':

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

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'generate':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        # Update the model to acknowledge changes.
        model.options.compression = compression

        # Save the model values.
        model.project.configuration.save()

        return

    elif action == 'quit':

        displayer.reset_buttons(is_back_sensitive=False, is_next_sensitive=False)

        options_page.preseed_tab.remove_tree()
        options_page.boot_tab.remove_tree()

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


def on_toggled__compression_page__radio_button(toggle_button):

    # 1 = lz4
    # 2 = lzo
    # 3 = gzip
    # 4 = zstd
    # 5 = xz

    if toggle_button.get_active():
        global compression
        compression = toggle_button.get_label()
        logger.log_value('The selected compression is', compression)


########################################################################
# Support Functions
########################################################################

# N/A
