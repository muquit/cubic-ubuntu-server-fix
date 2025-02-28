#!/usr/bin/python3

########################################################################
#                                                                      #
# logger.py                                                            #
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

# https://en.wikipedia.org/wiki/ANSI_escape_code
# https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences

########################################################################
# Imports
########################################################################

import textwrap

from cubic.constants import BACKGROUD_GREEN, BACKGROUD_YELLOW, NORMAL

########################################################################
# Global Variables & Constants
########################################################################

total_width = 80

log = False
log_file = None
verbose = False

########################################################################
# Logging Functions
########################################################################


def log_title(text):

    if verbose or log: _log_title(text)


def log_label(text):

    if verbose or log: _log_label(text)


def log_value(column_a_text, column_b_text=None):

    # if verbose or log: _log_value_top(column_a_text, column_b_text, column_a_initial_indent='    ')
    # if verbose or log: _log_value_bottom(column_a_text, column_b_text, column_a_initial_indent='    ')
    if verbose or log: _log_value_hanging(column_a_text, column_b_text, column_a_initial_indent='  • ', column_a_subsequent_indent='    ')


########################################################################
# Private Logging Functions
########################################################################


def _log_title(text):

    lines = textwrap.fill(str(text).strip(), width=total_width, initial_indent='', subsequent_indent='')

    if verbose:
        print()
        print(f'{BACKGROUD_YELLOW}{lines:<{total_width}}{NORMAL}')
        print()
    if log_file:
        _write('')
        _write(f'{lines:<{total_width}}')
        _write('')


def _log_label(text):

    width_column_a = int(total_width / 2.0) + 3

    column_a_lines = textwrap.wrap(str(text).strip(), width=width_column_a, initial_indent='  ', subsequent_indent='  ')

    column_a_size = len(column_a_lines)

    if verbose:
        print()
        for index in range(column_a_size):
            column_a_line = f'{column_a_lines[index]:<{width_column_a}}'
            print(f'{BACKGROUD_GREEN}{column_a_line}{NORMAL}')
        print()
    if log_file:
        _write('')
        for index in range(column_a_size):
            column_a_line = f'{column_a_lines[index]:<{width_column_a}}'
            _write(f'{column_a_line}')
        _write('')


def _log_value_top(column_a_text, column_b_text=None, column_a_initial_indent='  ', column_a_subsequent_indent='  '):

    # Column A width includes the initial/subsequent indents of four characters.
    # Column B width includes the initial/subsequent indents of one character.
    # The total width is the sum of column A width + column B width.

    width_column_a = int(total_width / 2.0)
    width_column_b = total_width - width_column_a

    column_a_text = str(column_a_text).strip()
    column_a_lines = textwrap.wrap(column_a_text, width=width_column_a, initial_indent=column_a_initial_indent, subsequent_indent=column_a_subsequent_indent)

    column_b_text = str(column_b_text).strip()
    if len(column_b_text) == 0:
        column_b_text = 'Empty'
    column_b_lines = textwrap.wrap(column_b_text, width=width_column_b, initial_indent=' ', subsequent_indent=' ')

    column_a_size = len(column_a_lines)
    column_b_size = len(column_b_lines)

    for index in range(max(column_a_size, column_b_size)):

        # Column A
        if index < column_a_size - 1:
            # Case for all lines prior to the last line.
            column_a_line = f'{column_a_lines[index]:<{width_column_a}}'
        elif index == column_a_size - 1:
            # Case for the last line.
            column_a_line = f'{column_a_lines[index]:.<{width_column_a}}'
        else:
            # Case for non-existent lines.
            column_a_line = ' ' * width_column_a

        # Column B
        if index < column_b_size:
            # Case for all lines prior to the last line.
            column_b_line = f'{column_b_lines[index]:<{width_column_b}}'
        else:
            # Case for non-existent lines.
            column_b_line = ''

        # Print column A and column B.

        if verbose:
            print(f'{column_a_line}{column_b_line}')
        if log_file:
            _write(f'{column_a_line}{column_b_line}')


def _log_value_bottom(column_a_text, column_b_text=None, column_a_initial_indent='  ', column_a_subsequent_indent='  '):

    # Column A width includes the initial/subsequent indents of four characters.
    # Column B width includes the initial/subsequent indents of one character.
    # The total width is the sum of column A width + column B width.

    width_column_a = int(total_width / 2.0)
    width_column_b = total_width - width_column_a

    column_a_text = str(column_a_text).strip()
    column_a_lines = textwrap.wrap(column_a_text, width=width_column_a, initial_indent=column_a_initial_indent, subsequent_indent=column_a_subsequent_indent)

    column_b_text = str(column_b_text).strip()
    if len(column_b_text) == 0:
        column_b_text = 'Empty'
    column_b_lines = textwrap.wrap(column_b_text, width=width_column_b, initial_indent=' ', subsequent_indent=' ')

    column_a_size = len(column_a_lines)
    column_b_size = len(column_b_lines)
    column_b_start = (column_a_size - column_b_size) * (column_a_size > column_b_size)

    for index in range(max(column_a_size, column_b_size)):

        # Column A
        if index < column_a_size - 1:
            # Case for all lines prior to the last line.
            column_a_line = f'{column_a_lines[index]:<{width_column_a}}'
        elif index == column_a_size - 1:
            # Case for the last line.
            column_a_line = f'{column_a_lines[index]:.<{width_column_a}}'
        else:
            # Case for non-existent lines.
            column_a_line = ' ' * width_column_a

        # Column B
        if index >= column_b_start:
            # Case for all lines including the last line.
            column_b_line = f'{column_b_lines[index - column_b_start]:<{width_column_b}}'
        else:
            # Case for non-existent lines.
            column_b_line = ''

        # Print column A and column B.
        if verbose:
            print(f'{column_a_line}{column_b_line}')
        if log_file:
            _write(f'{column_a_line}{column_b_line}')


def _log_value_hanging(column_a_text, column_b_text=None, column_a_initial_indent='  ', column_a_subsequent_indent='  '):

    # Column A width includes the initial/subsequent indents of four characters.
    # Column B width includes the initial/subsequent indents of one character.
    # The total width is the sum of column A width + column B width.

    width_column_a = int(total_width / 2.0)
    width_column_b = total_width - width_column_a

    column_a_text = str(column_a_text).strip()
    column_a_lines = textwrap.wrap(column_a_text, width=width_column_a, initial_indent=column_a_initial_indent, subsequent_indent=column_a_subsequent_indent)

    column_b_text = str(column_b_text).strip()
    if len(column_b_text) == 0:
        column_b_text = 'Empty'
    column_b_lines = textwrap.wrap(column_b_text, width=width_column_b, initial_indent='... ', subsequent_indent='    ')

    column_a_size = len(column_a_lines)
    column_b_size = len(column_b_lines)
    column_b_start = column_a_size - 1

    for index in range(column_a_size + column_b_size - 1):

        # Column A
        if index < column_a_size - 1:
            # Case for all lines prior to the last line.
            column_a_line = f'{column_a_lines[index]:<{width_column_a}}'
        elif index == column_a_size - 1:
            # Case for the last line.
            column_a_line = f'{column_a_lines[index]:.<{width_column_a}}'
        else:
            # Case for non-existent lines.
            column_a_line = ' ' * width_column_a

        # Column B
        if index >= column_b_start:
            # Case for all lines including the last line.
            column_b_line = f'{column_b_lines[index - column_b_start]:<{width_column_b}}'
        else:
            # Case for non-existent lines.
            column_b_line = ''

        # Print column A and column B.
        if verbose:
            print(f'{column_a_line}{column_b_line}')
        if log_file:
            _write(f'{column_a_line}{column_b_line}')


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


def _write(lines):
    with open(log_file, 'a') as file:
        # When writing in text mode, the default is to convert
        # occurrences of \n back to platform-specific line endings.
        # (See https://docs.python.org/3/tutorial/inputoutput.html)
        file.write(f'{lines}\n')
