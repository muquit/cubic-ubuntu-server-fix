#!/usr/bin/python3

########################################################################
#                                                                      #
# emulator.py                                                          #
#                                                                      #
# Copyright (C) 2021 PJ Singh <psingh.cubic@gmail.com>                 #
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
# but WITHOUT ANY WARRANTY, without even the implied warranty of       #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the         #
# GNU General Public License for more details.                         #
#                                                                      #
# You should have received a copy of the GNU General Public License    #
# along with Cubic. If not, see <http://www.gnu.org/licenses/>.        #
#                                                                      #
########################################################################
"""
Launches QEMU to test the disk image.
Use Ctrl-Alt-G to toggle mouse capture.
"""

########################################################################
# References
########################################################################

# https://www.qemu.org
# https://wiki.qemu.org
# https://ubuntu.com/server/docs/virtualization-qemu
# http://manpages.ubuntu.com/manpages/impish/en/man1/qemu-system-x86_64.1.html

########################################################################
# Imports
########################################################################

import gi
import os
import psutil

gi.require_version('GLib', '2.0')
from gi.repository import GLib

from cubic.constants import BOLD_RED, NORMAL
from cubic.constants import MEMORY_INCREMENT, MIN_RESERVE_MEMORY, MIN_AVAILABLE_MEMORY, MIN_AVAILABLE_MEMORY_MIB, MIN_AVAILABLE_MEMORY_GIB
from cubic.constants import MIB, GIB
from cubic.utilities import constructor
from cubic.utilities import file_utilities
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.processor import execute_asynchronous

########################################################################
# Global Variables & Constants
########################################################################

# Emulator status codes
EXITED = -1
RUNNING = 0
ERROR = 1
"""
A callback function supplied by the client in order to be notified
whenever the emulator starts or exits. The function must accept an int
argument of emulator.EXITED, emulator.RUNNING, or emulator.ERROR.
"""
status_callback = None

########################################################################
# Start Emulator Functions
########################################################################


def start_emulator(new_status_callback):

    global status_callback
    status_callback = new_status_callback

    _start_emulator()

    # Assume the emulator is running.
    logger.log_value('Emulator status', 'Started')
    if status_callback:
        status_callback(RUNNING)


def _start_emulator():

    emulator_memory, emulator_memory_mib, emulator_memory_gib = allocate_emulator_memory()

    custom_iso_file_path = os.path.join(model.generated.iso_directory, model.generated.iso_file_name)

    # Escape ',' in file path with ',,' per qemu requirements.
    custom_iso_file_path = custom_iso_file_path.replace(',', ',,')

    # Check if the host CPU supports Kernel-based virtualization (KVM).
    # • vms - Intel flag
    # • svm - AMD flag
    is_virtualization_supported = host_has_virtualization_support()
    logger.log_value('System supports virtualization', is_virtualization_supported)

    # Check if the host supports gtk.
    is_gtk_display_supported = host_has_gtk_display_support()
    logger.log_value('System supports GTK display', is_gtk_display_supported)

    if is_virtualization_supported and is_gtk_display_supported:
        command = (
            'qemu-system-x86_64'
            ' --name "Cubic"'
            ' -M pc'
            ' -enable-kvm'
            ' -cpu host'
            f' -m {emulator_memory_mib:d}M'
            ' -display gtk,zoom-to-fit=on'
            ' -device intel-hda'
            ' -device hda-duplex'
            f' -drive format=raw,file="{custom_iso_file_path}"')
    elif is_virtualization_supported:
        logger.log_value('Warning', f'{BOLD_RED}System does not support GTk display{NORMAL}')
        command = (
            'qemu-system-x86_64'
            ' --name "Cubic"'
            ' -M pc'
            ' -enable-kvm'
            ' -cpu host'
            f' -m {emulator_memory_mib:d}M'
            ' -device intel-hda'
            ' -device hda-duplex'
            f' -drive format=raw,file="{custom_iso_file_path}"')
    elif is_gtk_display_supported:
        logger.log_value('Warning', f'{BOLD_RED}System does not support virtualization{NORMAL}')
        command = (
            'qemu-system-x86_64'
            ' --name "Cubic"'
            ' -M pc'
            f' -m {emulator_memory_mib:d}M'
            ' -display gtk,zoom-to-fit=on'
            ' -device intel-hda'
            ' -device hda-duplex'
            f' -drive format=raw,file="{custom_iso_file_path}"')
    else:
        logger.log_value('Warning', f'{BOLD_RED}System does not support virtualization{NORMAL}')
        logger.log_value('Warning', f'{BOLD_RED}System does not support GTk display{NORMAL}')
        command = (
            'qemu-system-x86_64'
            ' --name "Cubic"'
            ' -M pc'
            f' -m {emulator_memory_mib:d}M'
            ' -device intel-hda'
            ' -device hda-duplex'
            f' -drive format=raw,file="{custom_iso_file_path}"')

    # Start the emulator.
    process = execute_asynchronous(command)

    # Subscribe to emulator exited events.
    subscribe_emulator_exited(process.pid)


########################################################################
# Exit Emulator Callback Functions
########################################################################


def subscribe_emulator_exited(process_id):

    logger.log_value('Subscribe to emulator exited events for process id', process_id)
    GLib.child_watch_add(GLib.PRIORITY_HIGH_IDLE, process_id, exited_emulator)


def exited_emulator(process_id, status):

    logger.log_value('Emulator status', 'Exited')

    # The signal number that killed the process.
    signal = status % 256  # Gets the low byte.

    # The exit status of the process (only set if the signal is 0).
    exit_code = status >> 8  # Gets the high byte.
    logger.log_value('Process id', process_id)
    logger.log_value('Status', str(status))
    logger.log_value('Signal', str(signal))
    logger.log_value('Exit Code', str(exit_code))

    # Notify clients that the emulator exited.
    global status_callback
    if status_callback:
        if exit_code:
            status_callback(ERROR)
        else:
            status_callback(EXITED)


def remove_status_callback():
    """
    Set the status call back to None. The child watch on the process id
    is not removed, but the call back function will not be invoked when
    the process exits.
    """

    # TODO: See if it is possible to remove the child watch. If so, the
    #       "if status_callback" checks can be removed.

    global status_callback
    status_callback = None


########################################################################
# Support Functions
########################################################################


def host_has_virtualization_support():
    """
    Check if the host CPU supports Kernel-based virtualization (KVM).
    • vms - Intel flag
    • svm - AMD flag
    """

    has_support = file_utilities.file_contains_any_word('/proc/cpuinfo', 'vmx', 'svm')
    logger.log_value('The host system supports virtualization?', has_support)

    return has_support


def host_has_gtk_display_support():
    """
    Check if the host supports gtk.
    """

    has_support = bool(constructor.get_package_version('qemu-system-gui'))
    logger.log_value('The host system supports GTK display?', has_support)

    return has_support


def get_total_system_memory():
    """
    Get the total system memory.

    Returns:
    memory : int
        The amount of total memory in Bytes.
    memory_mib : int
        The amount of total memory in MiB.
    memory_gib : int
        The amount of total memory in GiB.
    """

    # Get the total system memory in bytes.
    memory = psutil.virtual_memory().total
    memory_mib = memory / MIB
    memory_gib = memory / GIB

    # logger.log_value('Total system memory', f'{memory_gib:.2f} GiB ({memory_mib:.2f} MiB)')

    return memory, memory_mib, memory_gib


def get_available_system_memory():
    """
    Get the available system memory.

    Returns:
    memory : int
        The amount of available memory in Bytes.
    memory_mib : int
        The amount of available memory in MiB.
    memory_gib : int
        The amount of available memory in GiB.
    """

    # Get the available system memory in bytes.
    memory = psutil.virtual_memory().available
    memory_mib = memory / MIB
    memory_gib = memory / GIB

    # logger.log_value('Available system memory', f'{memory_gib:.2f} GiB ({memory_mib:.2f} MiB)')

    return memory, memory_mib, memory_gib


def check_available_memory():

    total_memory, total_memory_mib, total_memory_gib = get_total_system_memory()
    logger.log_value('Total system memory', f'{total_memory_gib:.2f} GiB ({total_memory_mib:.2f} MiB)')

    logger.log_value('Minimum available memory required to enable testing', f'{MIN_AVAILABLE_MEMORY_GIB:.2f} GiB ({MIN_AVAILABLE_MEMORY_MIB:.2f} MiB)')

    available_memory, available_memory_mib, available_memory_gib = get_available_system_memory()
    logger.log_value('Available system memory', f'{available_memory_gib:.2f} GiB ({available_memory_mib:.2f} MiB)')

    # Enable testing if the system has at least 1.5 GiB available memory.
    is_adequate = available_memory > MIN_AVAILABLE_MEMORY

    return is_adequate


def allocate_emulator_memory():
    """
    Calculate the amount of memory to allocate to the emulator. Reserve
    at least 525 MiB of available memory after allocating memory to the
    emulator in increments of 256 MiB.

    Returns:
    emulator_memory : int
        The amount of emulator memory in Bytes.
    emulator_memory_mib : int
        The amount of emulator memory in MiB.
    emulator_memory_gib : int
        The amount of emulator memory in GiB.
    """

    total_memory, total_memory_mib, total_memory_gib = get_total_system_memory()
    logger.log_value('Total system memory', f'{total_memory_gib:.2f} GiB ({total_memory_mib:.2f} MiB)')

    available_memory, available_memory_mib, available_memory_gib = get_available_system_memory()
    logger.log_value('Available system memory', f'{available_memory_gib:.2f} GiB ({available_memory_mib:.2f} MiB)')

    # Calculate the memory to allocate to the emulator in bytes.
    emulator_memory = int((int((available_memory - MIN_RESERVE_MEMORY) / MEMORY_INCREMENT)) * MEMORY_INCREMENT)
    emulator_memory_mib = int(emulator_memory / MIB)
    emulator_memory_gib = int(emulator_memory / GIB)
    model.emulator_memory = emulator_memory
    logger.log_value('Memory allocated to the emulator', f'{emulator_memory_gib:.2f} GiB ({emulator_memory_mib:.2f} MiB)')

    # Calculate the reserved system memory.
    reserve_system_memory_bytes = available_memory - emulator_memory
    reserve_system_memory_mib = reserve_system_memory_bytes / MIB
    reserve_system_memory_gib = reserve_system_memory_bytes / GIB
    logger.log_value('Reserved system memory', f'{reserve_system_memory_gib:.2f} GiB ({reserve_system_memory_mib:.2f} MiB)')

    return emulator_memory, emulator_memory_mib, emulator_memory_gib
