#!/usr/bin/python3

########################################################################
#                                                                      #
# iso_utilities.py                                                     #
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

# TOTO: Remove all invocations of log_label(), and add this logging to
#       the calling function.

########################################################################
# References
########################################################################

# N/A

########################################################################
# Imports
########################################################################

import os
import re

from cubic.constants import MULTIPLES, IMAGE_FILE_NAME
from cubic.utilities import file_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.processor import execute_synchronous

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Disk Mount / Unmount
########################################################################


def mount(iso_file_path, iso_mount_point, user_id=None, group_id=None):
    """
    If user, group, or other has the execute permission for a file, all
    three will be assigned the execute permission for the file when the
    ISO is mounted.
    """

    logger.log_label('Mount the ISO image')
    logger.log_value('The ISO file path is', iso_file_path)
    logger.log_value('The mount point is', iso_mount_point)
    logger.log_value('The user id is', user_id)
    logger.log_value('The group id is', group_id)

    program = os.path.join(model.application.directory, 'commands', 'mount-iso')
    if user_id and group_id:
        command = ['pkexec', program, iso_file_path, iso_mount_point, user_id, group_id]
    else:
        command = ['pkexec', program, iso_file_path, iso_mount_point]
    result, exit_status, signal_status = execute_synchronous(command)

    logger.log_value('The result is', result)
    logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')

    return result, exit_status, signal_status


def unmount(iso_mount_point):

    logger.log_value('Unmount ISO', iso_mount_point)

    program = os.path.join(model.application.directory, 'commands', 'unmount-iso')
    command = ['pkexec', program, iso_mount_point]
    result, exit_status, signal_status = execute_synchronous(command)

    logger.log_value('The result is', result)
    logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')

    return result, exit_status, signal_status


def is_mounted(iso_mount_point, iso_file_path=None):

    if iso_file_path:
        return _is_mounted_1(iso_mount_point, iso_file_path)
    else:
        return _is_mounted_2(iso_mount_point)


def _is_mounted_1(iso_mount_point, iso_file_path):

    logger.log_label('Check if the ISO image is mounted')
    logger.log_value('The mount point is', iso_mount_point)
    logger.log_value('The ISO file path is', iso_file_path)

    # Real path is necessary here.
    # The the output of the mount command only includes real paths.
    real_iso_mount_point = os.path.realpath(iso_mount_point)
    real_iso_file_path = os.path.realpath(iso_file_path)

    # The function os.path.islink() can not be used because it only
    # checks if the last item in the path is a link.
    if iso_mount_point != real_iso_mount_point:
        iso_mount_point = real_iso_mount_point
        logger.log_value('The mount point is a link to', iso_mount_point)
    if iso_file_path != real_iso_file_path:
        iso_file_path = real_iso_file_path
        logger.log_value('The ISO file path is a link to', iso_file_path)

    command = 'mount'
    result, exit_status, signal_status = execute_synchronous(command)
    is_mounted = False
    if not exit_status and not signal_status:
        mount_information = re.search(r'%s\s*on\s*%s' % (re.escape(iso_file_path), re.escape(iso_mount_point)), result)
        is_mounted = bool(mount_information)

    logger.log_value('Is mounted?', is_mounted)

    return is_mounted


def _is_mounted_2(iso_mount_point):

    logger.log_label('Check if the mount point is mounted')
    logger.log_value('The mount point is', iso_mount_point)

    # The link target is provided for information purposes only.
    # The function os.path.islink() can not be used because it only
    # checks if the last item in the path is a link.
    real_iso_mount_point = os.path.realpath(iso_mount_point)
    if iso_mount_point != real_iso_mount_point:
        logger.log_value('The mount point is a link to', real_iso_mount_point)

    # Realpath is not necessary here, because the function
    # os.path.ismount() also works for symlinks.
    is_mounted = os.path.ismount(iso_mount_point)

    logger.log_value('Is mounted?', is_mounted)

    return is_mounted


def unmount_iso_and_delete_mount_point(iso_mount_point):
    """
    Unmount the ISO and delete the mount point.
    """

    logger.log_value('Unmount the ISO and delete the mount point', iso_mount_point)
    if os.path.exists(iso_mount_point):
        result, exit_status, signal_status = unmount(iso_mount_point)
        if not signal_status:
            logger.log_value('Delete the mount point', iso_mount_point)
            result, exit_status, signal_status = file_utilities.delete_directory(iso_mount_point)
            if not signal_status:
                logger.log_value('Deleted the mount point', iso_mount_point)
                pass
            else:
                logger.log_value('Unable to delete the mount point', iso_mount_point)
        else:
            logger.log_value('Unable to unmount the ISO and delete the mount point', iso_mount_point)
    else:
        logger.log_value('Skipping. The mount point does not exist', iso_mount_point)


########################################################################
# ISO Information
########################################################################


def get_iso_volume_id(iso_file_path):

    logger.log_label('Get ISO image volume id')
    logger.log_value('ISO image', iso_file_path)

    # Get the original ISO image volume id.
    command = f'isoinfo -d -i "{iso_file_path}"'
    result, exit_status, signal_status = execute_synchronous(command)
    # iso_volume_id = 'Unknown ISO image volume id'
    iso_volume_id = ''
    if not exit_status and not signal_status:
        iso_volume_id = re.sub(r'.*Volume id:\s+(.*[^\n]).*Volume\s+set\s+id.*', r'\1', result, 0, re.DOTALL)[:32]
    logger.log_value('ISO image volume id', iso_volume_id)

    return iso_volume_id


def get_iso_release_name(iso_mount_point):

    logger.log_label('Get ISO image release name')
    logger.log_value('ISO image mount point', iso_mount_point)

    # Read the original ISO image README.diskdefines file.
    # file_path = os.path.join(iso_mount_point, 'README.diskdefines')

    # Read the original ISO image .disk/info file.
    file_path = os.path.join(iso_mount_point, '.disk', 'info')

    iso_release_name = None
    matches = file_utilities.find_in_file(r'"(.*)"', file_path)
    if matches:
        iso_release_name = matches[0]
        logger.log_value('ISO image release name', iso_release_name)
    else:
        logger.log_value('ISO image release name', 'Not found')

    return iso_release_name


def get_iso_disk_name(iso_mount_point):

    logger.log_label('Get ISO image disk name')
    logger.log_value('ISO image mount point', iso_mount_point)

    # Read the original ISO image README.diskdefines file.
    file_path = os.path.join(iso_mount_point, 'README.diskdefines')

    iso_disk_name = None
    matches = file_utilities.find_in_file(r'DISKNAME *(.*)', file_path)
    if matches:
        iso_disk_name = matches[0]
        logger.log_value('ISO image disk name', iso_disk_name)
    else:
        logger.log_value('ISO image disk name', 'Not found')

    return iso_disk_name


def get_iso_release_notes_url(iso_mount_point):

    logger.log_label('Get ISO image release notes URL')
    logger.log_value('ISO image mount point', iso_mount_point)

    # Read the original ISO image release_notes_url file.
    file_path = os.path.join(iso_mount_point, '.disk', 'release_notes_url')
    iso_release_notes_url = file_utilities.read_file(file_path)

    return iso_release_notes_url


########################################################################
# ORIGINAL
########################################################################
"""
These functions use threads which can be terminated.
"""


def get_iso_release_name_ORIGINAL(iso_mount_point):

    logger.log_label('Get ISO image release name')
    logger.log_value('ISO image mount point', iso_mount_point)

    # Read the original ISO image README.diskdefines file.
    file_path = os.path.join(iso_mount_point, 'README.diskdefines')
    command = f'cat "{file_path}"'
    result, exit_status, signal_status = execute_synchronous(command)
    # Get the original ISO image release name.
    # iso_release_name = 'Unknown ISO image release name'
    iso_release_name = ''
    if not exit_status and not signal_status:
        iso_release_name_infromation = re.search(r'DISKNAME.*"(.*)"', result)
        if iso_release_name_infromation:
            iso_release_name = iso_release_name_infromation.group(1)
    logger.log_value('ISO image release name', iso_release_name)

    return iso_release_name


def get_iso_disk_name_ORIGINAL(iso_mount_point):

    logger.log_label('Get ISO image disk name')
    logger.log_value('ISO image mount point', iso_mount_point)

    # Read the original ISO image README.diskdefines file.
    file_path = os.path.join(iso_mount_point, 'README.diskdefines')
    command = f'cat "{file_path}"'
    result, exit_status, signal_status = execute_synchronous(command)
    # Get the original ISO image disk name.
    # iso_disk_name = 'Unknown ISO image disk name'
    iso_disk_name = ''
    if not exit_status and not signal_status:
        iso_disk_name_information = re.search(r'DISKNAME *(.*)', result)
        if iso_disk_name_information:
            iso_disk_name = iso_disk_name_information.group(1)
    logger.log_value('ISO image disk name', iso_disk_name)

    return iso_disk_name


def get_iso_release_notes_url_ORIGINAL(directory):

    logger.log_label('Get ISO image release notes URL')
    logger.log_value('ISO image mount point', directory)

    # Read the original ISO image release_notes_url file.
    file_path = os.path.join(directory, '.disk', 'release_notes_url')
    command = f'cat "{file_path}"'
    result, exit_status, signal_status = execute_synchronous(command)
    # Get the original ISO image release notes URL.
    # iso_release_notes_url = 'Unknown ISO image release notes URL'
    iso_release_notes_url = ''
    if not exit_status and not signal_status:
        iso_release_notes_url = result
    logger.log_value('ISO image release notes URL', iso_release_notes_url)

    return iso_release_notes_url


########################################################################
# Generate ISO Template Functions
########################################################################


def get_iso_report():

    # logger.log_label('Get ISO report')

    iso_file_path = os.path.join(model.original.iso_directory, model.original.iso_file_name)

    logger.log_value('Get ISO report for', iso_file_path)

    command = f'xorriso -indev "{iso_file_path}" -report_el_torito as_mkisofs'
    result, exit_status, signal_status = execute_synchronous(command)
    # logger.log_value('The result is', result)
    # logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')

    # The exit status and signal status can not be used to assess
    # failure or success. On failure exit status may be 0 or any number
    # and singal status is always None. On success exit status may be 0
    # and singal status is always None.

    # Partition the result on '-V'. If '-V' is not present, iso
    # information will be an empty string ''.
    iso_report = ''.join(result.partition('-V')[1:])

    logger.log_value('The ISO report is', iso_report)

    return iso_report


def generate_iso_template(iso_report):

    # logger.log_label('Generate the ISO template')

    # Reset the image number used to name *.img files.
    global image_number
    image_number = 0

    template = ''
    lines = iso_report.split(os.linesep)
    for line in lines:

        # Remove '\r\n' at the end of each line.
        line = line.strip()

        # logger.log_value('The original line is', line)

        # Apply rules to create the template.
        is_error, line = handle_volume_id(line)
        if is_error: return None
        is_error, line = handle_modification_date(line)
        if is_error: return None
        is_error, line = handle_interval_path(line)
        if is_error: return None
        is_error, line = handle_part_like_isohybrid(line)
        if is_error: return None

        # logger.log_value('The updated line is', line)

        # Append the new line to the template.
        if line: template = template + line + os.linesep

    return template


def handle_volume_id(line):
    """
    Make the volume ID variable.

    Assume "-V" is always on a line by itself.
    """

    if not line.startswith('-V'): return False, line

    line = "-V '{volume_id}'"

    return False, line


def handle_volume_id_ALTERNATIVE(line):
    """
    Make the volume ID variable.
    """

    # re.sub(r"KEY='.*?'\s*|\s*KEY='.*?'|KEY=\S*\s*|\s*KEY=\S*", "", line)

    if '-V' not in line: return False, line

    line = re.sub(r"\s*-V\s+'.*'\s*|\s*-V\s+\S*\s*", " -V '{volume_id}' ", line).strip()

    return False, line


def handle_modification_date(line):
    """
    Remove the modification time stamp.

    Assume "--modification-date" is always on a line by itself.
    """

    if not line.startswith('--modification-date'): return False, line

    line = ''

    return False, line


def handle_modification_date_ALTERNATIVE(line):
    """
    Remove the modification time stamp.
    """
    # re.sub(r"KEY='.*?'\s*|\s*KEY='.*?'|KEY=\S*\s*|\s*KEY=\S*", "", line)

    if '--modification-date' not in line: return False, line

    # remove = '"--modification-date\s*=\s*\S*'
    # line = re.sub(r"{remove}*\s*|\s*{remove}".format(remove=remove), "", line).strip()
    # line = re.sub(r"--modification-date\s*=\s*\S*\s*|\s*--modification-date\s*=\s*\S*", "", line).strip()
    line = re.sub(r"\s*--modification-date\s*=\s*\S*\s*", " ", line).strip()

    return False, line


def handle_interval_path(line):
    """
    Update the interval path.
    """

    if '--interval' not in line: return False, line

    logger.log_value('The interval path is', line)

    # Format: interval:"Flags":"Interval":"Zeroizers":"Source"
    # [1] = text before
    # [ ] = --interval
    # [2] = 1st argument of interval (flags)
    # [3] = 2nd argument of interval (interval)
    # [4] = 3rd argument of interval (zeroizers)
    # [5] = 4th argument of interval (source)
    # [6] = text after

    result = re.search(r"(.*?)\s*--interval:(.*):(.*):(.*):('.*'|[^'\s]*)\s*(.*)", line)
    before = result[1].strip()
    flags = result[2].strip()
    interval = result[3].strip()
    zeroizers = result[4].strip()
    source = result[5].strip("'")
    after = result[6]

    if flags == 'local_fs':

        # Interval path:
        # flags     - unchanged
        # interval  -   changed
        # zeroizers - unchanged
        # source    -   changed

        # Get the interval information (range of bytes in the original ISO).
        # start_block, stop_block, block_count, block_units = parse_interval(interval)

        interval_information = parse_interval(interval)

        # Return if error.
        if not interval_information: return True, line

        start_block, stop_block, block_count, block_units, block_size = interval_information

        # Get the original ISO image file path.
        iso_file_path = os.path.join(model.original.iso_directory, model.original.iso_file_name)

        # Get the ISO partition image file name.
        image_file_name = get_iso_partition_image_file_name()

        # Get the ISO partition image file path.
        image_file_path = os.path.join(model.project.directory, image_file_name)

        # Create the ISO partition image file.
        is_error = extract_image(iso_file_path, image_file_path, block_size, start_block, block_count)

        # Return if error.
        if is_error: return True, line

        # Create a new interval in units of "d" (512).
        # start_block = 0
        # stop_block = int((block_count - 1) * block_size / 512)
        # interval = f'{start_block}d-{stop_block}d'

        # Create a new interval using the original units.
        start_block = 0
        stop_block = block_count - 1
        interval = f'{start_block}{block_units}-{stop_block}{block_units}'

        # Get the source.
        source = f"'{{boot_image_directory}}{os.path.sep}{image_file_name}'"

    elif flags.startswith('appended_partition'):

        # Interval path:
        # flags     -   changed
        # interval  - unchanged
        # zeroizers - unchanged
        # source    - unchanged

        # Update the flags.

        flags = re.search(r'(appended_partition_\d{0,3}).*', flags).group(1)

    else:

        # Return error.
        return True, line

    # Correct spacing between quotes is critical.
    space_before, space_after = get_spacers(before, after)

    # Assemble the new line.
    line = f"{before}{space_before}--interval:{flags}:{interval}:{zeroizers}:{source}{space_after}{after}"

    logger.log_value('The interval path is', line)

    return False, line


def parse_interval(interval):

    # The interval references a range of bytes in the original ISO.

    logger.log_value('The interval is', interval)

    start_block, stop_block = interval.split('-')

    # Get the start block (skip blocks).
    result = re.search(r'(\d+)(\w*)', start_block)
    start_block = int(result.group(1))
    logger.log_value('The start block is', start_block)

    # Get the block units (k, m, g, t, s, d).
    block_units = result.group(2)
    logger.log_value('The block units are', block_units)

    # Get the block size.
    # Assume start block size is same as stop block size.
    block_size = MULTIPLES.get(block_units, 1)
    logger.log_value('The block size is', block_size)

    # Ger the stop block.
    result = re.search(r'(\d+)(\w*)', stop_block)
    stop_block = int(result.group(1))
    logger.log_value('The stop block is', stop_block)

    # Assume stop block size is same as start block size.
    # Get the block units (k, m, g, t, s, d).
    # block_units = result.group(2)
    # logger.log_value('The block units are', block_units)
    #
    # Get the block size.
    # block_size = MULTIPLES.get(block_units, 1)
    # logger.log_value('The block size is', block_size)

    # Ger the block count.
    block_count = stop_block - start_block + 1
    logger.log_value('The block count is', block_count)

    return start_block, stop_block, block_count, block_units, block_size


def get_iso_partition_image_file_name():

    # Get the image file name.
    global image_number
    image_number = image_number + 1
    image_file_name = IMAGE_FILE_NAME % image_number

    return image_file_name


def get_spacers(before, after):

    # Correct spacing between quotes is critical.
    if before and after and before[-1] == "'" and after[0] == "'":
        space_before = ''
        space_after = ''
    elif before and after:
        space_before = ' '
        space_after = ' '
    elif before and not after:
        space_before = ' '
        space_after = ''
    elif not before and after:
        space_before = ''
        space_after = ' '
    else:
        space_before = ''
        space_after = ''

    return space_before, space_after


def handle_part_like_isohybrid(line):
    """
    Replace -part_like_isohybrid' with '-appended_part_as_gpt'. The
    output of Xorriso <= 1.5.2 incorrectly reports that
    '-part_like_isohybrid' is being used, whenever an ISO is using
    '--mbr-force-bootable'.

    Assume "-part_like_isohybrid" is is always on a line by itself.
    """

    if not line.startswith('-part_like_isohybrid'): return False, line

    line = '-appended_part_as_gpt'

    return False, line


def handle_part_like_isohybrid_ALTERNATIVE(line):
    """
    Replace -part_like_isohybrid' with '-appended_part_as_gpt'. The
    output of Xorriso <= 1.5.2 incorrectly reports that
    '-part_like_isohybrid' is being used, whenever an ISO is using
    '--mbr-force-bootable'.
    """

    # re.sub(r"KEY='.*?'\s*|\s*KEY='.*?'|KEY=\S*\s*|\s*KEY=\S*", "", line)

    if '-part_like_isohybrid' not in line: return False, line

    line = re.sub(r'\s*-part_like_isohybrid\s*', ' -appended_part_as_gpt ', line).strip()

    return False, line


def extract_image(iso_file_path, imgage_file_path, block_size, skip_blocks, block_count):

    # logger.log_label('Extract image')

    logger.log_value('Extract image from', iso_file_path)
    logger.log_value('Extract image to', imgage_file_path)
    # logger.log_value('The block size is', block_size)
    # logger.log_value('The skip blocks is', skip_blocks)
    # logger.log_value('The block count is', block_count)
    logger.log_value('Extract image blocks', f'block size: {block_size}, skip blocks: {skip_blocks}, block count: {block_count}')

    command = (f'dd if="{iso_file_path}" ' \
               f'bs="{block_size}" '       \
               f'skip="{skip_blocks}" '    \
               f'count="{block_count}" '   \
               f'of="{imgage_file_path}"')
    result, exit_status, signal_status = execute_synchronous(command)

    logger.log_value('The result is', result)
    logger.log_value('The exit status, signal status is', f'{exit_status}, {signal_status}')

    if not exit_status:
        is_error = False
    else:
        is_error = True

    return is_error
