#!/usr/bin/python3

########################################################################
#                                                                      #
# progressor.py                                                        #
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

# https://pexpect.readthedocs.io/en/stable/
# https://stackoverflow.com/questions/41679513/python-pexpect-pxssh-getting-the-exit-status
# https://docs.python.org/3/c-api/exceptions.html
# https://docs.python.org/3/library/threading.html#thread-objects
# https://docs.python.org/3/library/threading.html#event-objects
# https://docs.python.org/3/c-api/init.html

########################################################################
# Imports
########################################################################

import ctypes
import datetime
import os
import pexpect
import re
import threading
import time
import traceback

from cubic.constants import RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, NORMAL
from cubic.constants import START_PERCENT, FINAL_PERCENT, SCALE_FACTOR
from cubic.utilities import logger
from cubic.utilities import processor

########################################################################
# Global Variables & Constants
########################################################################

# Pattern to match percent in the output. The format is "###.##%".
PERCENT_PATTERN = re.compile(r'[0-9]{1,3}(\.[0-9]{2}){0,1}%')

# Number of steps in the progress at 0%.
START_POSITION = int(START_PERCENT * SCALE_FACTOR)

# Number of steps in the progress at 100%.
FINAL_POSITION = int(FINAL_PERCENT * SCALE_FACTOR)

# The expected duration in seconds of a "typical" process. This is used
# to compute the typical tracker delay while waiting for the first
# process update, or after the final process update, when the percent
# complete is 100% but the computed delay is too large. For example, a
# value of 250.0 seconds implies that a "typical" progress bar should
# take 250 seconds to complete. The typical delay can be calculated as
# 250 seconds duration / 1000 total increments = 0.250 seconds delay per
# increment.
TYPICAL_DURATION = 250.0

# The expected duration in seconds of an "quick" process. This is used
# to compute the minimum tracker delay when the computed delay is too
# small. For example, a value of 0.125 seconds implies that a "quick"
# progress bar should take 0.125 seconds to complete. The minimum delay
# can be calculated as 0.125 seconds duration / 1000 total increments =
# 0.000125 seconds delay per increment.
MINIMUM_DURATION = 0.125

# Exist status 0 indicates the process completed successfully.
OK = 0

# Set to True to print progress information.
is_debug = False

# Remember to invoke initialize_tracker() to set the following values
# before starting the process thread and the tracker.

# The adjusted typical delay per increment.
typical_delay = None

# The adjusted default minimum delay per increment.
minimum_delay = None

# The Event used to control the tracker. When the event is blocked, the
# tracker will stop incrementing and wait for the event to be unblocked.
block_event = None

# The current position of the process.
process_position = None

# The current position of the tracker.
tracker_position = None

# The target position the tracker must reach to stop incrementing.
tracker_target = None

# The delay in seconds before incrementing the tracker position by 1.
delay = None

# The the time when the process position was previously updated.
prior_process_time = None

# The previous position of the process.
prior_process_position = None

# The previous position of the process.
prior_process_period = None

########################################################################
# Tracker Control Functions
########################################################################


def initialize_tracker(quantity):
    """
    Initialize the tracker values. This function must be invoked before
    starting the process thread and the tracker.

    quantity : int
        The optional quantity of processes that will be executed
        sequentially. This value is used to adjust the typical delay and
        the minimum delay in order to minimize the time between progress
        tracker increments at the beginning and end of a process.
    """

    global TYPICAL_DURATION
    global MINIMUM_DURATION
    global typical_delay
    global minimum_delay

    # Reduce the typical delay and the minimum delay by a factor of one
    # for every 10 processes. For example, if the quantity is 1-10, the
    # factor is 1; if the quantity is 11-20, the factor is 2; if the
    # quantity is 100; the factor is 10.
    factor = 1 + int((quantity - 1) / 10)
    typical_delay = TYPICAL_DURATION / FINAL_POSITION / factor
    minimum_delay = MINIMUM_DURATION / FINAL_POSITION / factor

    global block_event
    global process_position
    global tracker_position
    global tracker_target
    global delay
    global prior_process_time
    global prior_process_position
    global prior_process_period

    block_event = threading.Event()

    process_position = START_POSITION
    tracker_position = START_POSITION

    # Display up to 10% while waiting for the process to provide the
    # first update.
    tracker_target = int(0.10 * FINAL_POSITION)

    # Increment the tracker slowly while waiting for the process to
    # provide the first update.
    delay = typical_delay

    prior_process_time = time.time()
    prior_process_position = START_POSITION
    prior_process_period = 0.0

    block(False)  # Unblock.

    if is_debug: print_values(YELLOW)


def update(percent):
    """
    Update the tracker using the reported percent complete.

    If the reported process position is greater than the previous
    process position, update the tracker target position, compute the
    tracker delay, and Unblock the tracking function.
    • Compute the process period (inverse rate of change) of the current
      process position and the previous process position.
    • Use the process period to estimate the time remaining for the
      process to complete.
    • Estimate the tracker delay as the period (inverse rate of change)
      of the current tracker position and the final position.
    • Set the tracker target position as the reported process position.

    Arguments:
    percent : float
        The actual percent complete as intermittently reported by the
        process.
    """

    global typical_delay
    global minimum_delay

    global process_position
    global tracker_position
    global tracker_target
    global delay
    global prior_process_time
    global prior_process_position
    global prior_process_period

    # Only update the tracker target and delay if the reported process
    # position is greater than the previous process position. This
    # avoids redundant updates, circumvents irrelevant updates from some
    # processes such as rsync that report fluctuating process complete
    # percentages, and avoids a division by zero error when calculating
    # the process period.
    reported_process_position = int(percent * SCALE_FACTOR)
    if reported_process_position > prior_process_position:

        # Process

        process_position = reported_process_position
        current_process_time = time.time()
        process_duration = current_process_time - prior_process_time
        process_distance = process_position - prior_process_position
        process_period = process_duration / process_distance
        if prior_process_period:
            process_period = 0.25 * prior_process_period + 0.75 * process_period
        projected_process_distance = FINAL_POSITION - process_position
        projected_process_duration = process_period * projected_process_distance

        # Tracker

        projected_tracker_distance = FINAL_POSITION - tracker_position
        tracker_period = projected_process_duration / projected_tracker_distance
        # When the process is complete, ensure the delay is not too big.
        if process_position == FINAL_POSITION:
            tracker_period = min(tracker_period, typical_delay)
        # Set the delay, ensuring it is not too short.
        delay = max(tracker_period, minimum_delay)
        tracker_target = process_position

        # Save current values.
        prior_process_time = current_process_time
        prior_process_position = process_position
        prior_process_period = process_period

        block(False)  # Unblock.
        if is_debug: print_values(YELLOW)


def block(is_block):
    """
    Block or unblock the tracker thread.

    Arguments:
    is_block : bool
        Whether or not to block the event. If True, threads calling
        wait() will block. If False, all blocked threads will unblock,
        and subsequent threads calling wait() will not block.
    """

    global block_event

    if is_block:
        # Block.
        # Reset the internal flag to false. Subsequently, threads
        # calling wait() will block until set() is called to set the
        # internal flag to true again.
        block_event.clear()
    else:
        # Unblock.
        # Set the internal flag to true. All threads waiting for it
        # to become true are awakened. Threads that call wait() once
        # the flag is true will not block at all.
        block_event.set()


def is_blocked():
    """
    Indicate if the tracker thread is blocked.

    Returns:
    : bool
        True if the tracker thread is blocked.
        False if the tracker thread is not blocked.
    """

    global block_event

    return not block_event.is_set()


def raise_exception(thread, exception):
    """
    Raise the exception to the thread. If the thread does not exist or
    is no longer alive, the exception will not be raised.

    Arguments:
    thread : threading.Thread
        The thread to raise the exception to.
    exception : Exception
        The exception to raise.
    """

    if thread and thread.is_alive():

        thread_id = thread.ident
        logger.log_value('Raise the exception to thread id', thread_id)

        # Asynchronously raise an exception in a thread. The id argument
        # is the thread id of the target thread; exc is the exception
        # object to be raised.
        # See: https://docs.python.org/3/c-api/init.html

        ctypes_thread_id = ctypes.c_long(thread_id)
        ctypes_exception = ctypes.py_object(exception)
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes_thread_id, ctypes_exception)

        block(False)  # Unblock.
        thread.join()

    else:

        logger.log_value('Raise the exception to thread id', 'No thread')


########################################################################
# Process Function
########################################################################

# https://pexpect.readthedocs.io/en/stable/api/pexpect.html#spawn-class
# If you wish to get the exit status of the child you must call the
# close() method. The exit or signal status of the child will be stored
# in self.exitstatus or self.signalstatus. If the child exited normally,
# then exit_status will store the exit return code and signal_status will
# be None. If the child was terminated abnormally with a signal, then
# signal_status will store the signal value and exit_status will be None.


def process_command(command, parent_thread, working_directory=None):
    """
    Execute the command while updating percent complete information from
    the running process. This function should be run as a thread. The
    process thread communicates with the tracker (parent thread) using
    the update() and raise_exception() functions.

    Arguments:
    command : str
        The command to execute.
    parent_thread : threading.Thread
        The parent thread calling this function. Exceptions encountered
        during execution of this thread will be sent to the patent
        thread.
    working_directory : str
        Optional directory to execute the command from.

    Exceptions:
    The exception (of any type) that occurred. If there is a message
    from the process, it will be added to the exception. The exception
    is raised on the parent thread. If the parent thread does not exist
    or is not alive, no exception will not be raised.
    : BaseException
        Exceptions derived from BaseException may be propagated.
    : Exception
        Exceptions derived from Exception may be propagated.
    : "non BaseException"
        Exceptions not derived from BaseException may be propagated.
    : pexpect.EOF
        This exception is only raised if the process exited with an
        error.
    : _PyErr_SetObject
        An exception with an arbitrary Python object as the "value" of
        the exception. This is used to wrap the "non BaseException" or
        pexpect.EOF exceptions.
    """

    current_thread = threading.current_thread()
    current_thread_id = current_thread.ident
    logger.log_value('Started process thread id', f'{MAGENTA}{current_thread_id}{NORMAL}')

    parent_thread_id = parent_thread.ident
    logger.log_value('Process started by thread id', parent_thread_id)

    start_time = datetime.datetime.now()
    formatted_time = f'{start_time:%H:%M:%S.%f}'
    logger.log_value('The process started at', formatted_time)

    process = None
    percent = START_PERCENT
    try:
        process = processor.execute_asynchronous(command, working_directory)
        done = False
        while not done:
            try:
                process.expect(PERCENT_PATTERN)
            except pexpect.EOF as exception:
                # Close the process to obtain the exit status.
                process.close()
                #done = (process.exitstatus is OK)
                if process.exitstatus is OK:
                    # muquit
                    # process completed successfully
                    done = True
                else:
                    # muquit
                    # failed, raise exception
                    raise exception
            else:
                # muquit
                # successfully found a percentage, update progress
                percent = float((process.after)[:-1])
                update(percent)
    except Exception as exception:
        logger.log_value('Error', 'An exception occurred')
        logger.log_value('The process thread id is', current_thread_id)
        stop_time = datetime.datetime.now()
        formatted_time = f'{stop_time:%H:%M:%S.%f}'
        logger.log_value('The process stopped at', formatted_time)
        if process:
            # Close the process to obtain the exit status.
            process.close()
            logger.log_value('The exit status, signal status is', f'{process.exitstatus}, {process.signalstatus}')
            message = process.before.strip().replace('\r\n', '\n')
            logger.log_value('The message is', message)
            # Add the message to the exception.
            exception = type(exception)(f'{str(exception)}{os.linesep}message: {message}')
        logger.log_value('The exception is', exception)
        logger.log_value('The trace back is', traceback.format_exc())
        logger.log_value('Stopped process thread id', f'{MAGENTA}{current_thread_id}{NORMAL}')
        # Raise the exception to the parent thread.
        raise_exception(parent_thread, exception)
    else:
        # Write data to disk.
        os.sync()
        # Only wait after an EOF, otherwise the process will block.
        process.wait()
        stop_time = datetime.datetime.now()
        formatted_time = f'{stop_time:%H:%M:%S.%f}'
        logger.log_value('The process finished at', formatted_time)
        logger.log_value('The exit status, signal status is', f'{process.exitstatus}, {process.signalstatus}')
        message = process.before.strip().replace('\r\n', '\n')
        logger.log_value('The message is', message)
        logger.log_value('Stopped process thread id', f'{MAGENTA}{current_thread_id}{NORMAL}')
        if percent < FINAL_PERCENT:
            logger.log_value('Adjust the final percent', f'from {percent:.2f}% to {FINAL_PERCENT:.2f}%')
            update(FINAL_PERCENT)


########################################################################
# Track Progress Function
########################################################################


def track_progress(command, progress_callback, working_directory=None, quantity=1):
    """
    Start a process for the specified command, track the progress, and
    update the client using the progress callback.

    Arguments:
    quantity : int
        The optional quantity of processes that will be executed
        sequentially. This value is used to adjust the typical delay and
        the minimum delay in order to minimize the time between progress
        tracker increments at the beginning and end of a process.
    command : str
        The command to execute.
    progress_callback : function
        A call back function that accepts a single float argument, used
        to update the client about the progress in percent.
    working_directory : str
        Optional directory to execute the command from.

    Exceptions:
    All exceptions are propagated to the calling thread of this function,
    including exceptions received from the process thread. The exception
    may be of any type.
    : BaseException
        Exceptions derived from BaseException may be propagated.
    : Exception
        Exceptions derived from Exception may be propagated.
    : "non BaseException"
        Exceptions not derived from BaseException may be propagated.
        Exceptions of this type are raised on this thread by the process
        thread.
    : pexpect.EOF
        This exception is only raised if the process exited with an
        error. Exceptions of this type are raised on this thread by the
        process thread.
    : _PyErr_SetObject
        An exception with an arbitrary Python object as the "value" of
        the exception. This is used to wrap the "non BaseException" or
        pexpect.EOF exceptions.
    """

    # ------------------------------------------------------------------
    # Initialize values before starting the process and the tracker.
    # ------------------------------------------------------------------

    # The tracker must be initialized before starting the process thread.
    initialize_tracker(quantity)

    # ------------------------------------------------------------------
    # Start the process to be tracked.
    # ------------------------------------------------------------------

    # The process thread will update the target position and the delay
    # used by the tracker below.

    current_thread = threading.current_thread()
    process_thread = threading.Thread(target=process_command, args=(command, current_thread, working_directory), daemon=True)
    process_thread.start()

    # ------------------------------------------------------------------
    # Track the process.
    # ------------------------------------------------------------------

    # Increment the tracker position and notify the client using the
    # supplied callback function. Block whenever the tracker position
    # reaches the target position.

    global block_event
    global tracker_position
    global tracker_target
    global delay

    while tracker_position < FINAL_POSITION:
        # Display the progress until the final position is reached.
        while tracker_position < tracker_target:
            # Display the progress until the target position is reached.
            time.sleep(delay)
            tracker_position += 1
            progress_callback(tracker_position / SCALE_FACTOR)
            if is_debug: print_values()
        if tracker_target < FINAL_POSITION:
            # Block and wait until the target position increases.
            block(True)  # Block.
            if is_debug: print_values()
            block_event.wait()


########################################################################
# Debug Print Functions
########################################################################


def print_values(color=NORMAL):
    """
    Output a table listing the current progress %, target progress %,
    the delay to increment the tracker, and whether or not the tracker
    is blocked.

    Arguments:
    color: str
        The Terminal Font Color code for the color to print the line in.
        (See the constants module for Terminal Font Color codes).
    """

    global process_position
    global prior_process_position
    global tracker_position
    global tracker_target
    global delay

    blocked_text = f'{RED}  Blocked' if is_blocked() else f'{GREEN}Unblocked'
    print(
        f'{color}'
        f'| Process: {process_position / SCALE_FACTOR:6.2f} % '
        f'| Previous: {prior_process_position / SCALE_FACTOR:6.2f} % '
        f'| Tracker: {tracker_position / SCALE_FACTOR:6.2f} % '
        f'| Target: {tracker_target / SCALE_FACTOR:6.2f} % '
        f'| Delay: {delay:9.7f} '
        f'| {blocked_text}{color} '
        f'|{NORMAL}')
