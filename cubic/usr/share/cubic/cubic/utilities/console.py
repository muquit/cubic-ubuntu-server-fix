#!/usr/bin/python3

########################################################################
#                                                                      #
# console.py                                                           #
#                                                                      #
# Copyright (C) 2019 PJ Singh <psingh.cubic@gmail.com>                 #
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

# https://developer.gnome.org/vte/0.48
# https://lazka.github.io/pgi-docs
# https://www.freedesktop.org/software/systemd/man/systemd-nspawn.html

########################################################################
# Imports
########################################################################

import gi

gi.require_version('GLib', '2.0')
gi.require_version('Vte', '2.91')

from gi.repository import GLib
from gi.repository.Vte import PtyFlags, Pty

import os
import pydbus
import sys
import time

from cubic.constants import BOLD_RED, BOLD_GREEN, BOLD_YELLOW, BOLD_BLUE, BOLD_MAGENTA, BOLD_CYAN, NORMAL, NEW_LINE
from cubic.constants import SLEEP_0250_MS
from cubic.utilities import logger
from cubic.utilities import model
from cubic.utilities.processor import execute_synchronous, execute_synchronous_unregistered

########################################################################
# Global Variables & Constants
########################################################################

MACHINE_NAME = 'cubic'

MAX_ATTEMPTS = 3
first_time = True
reenter = True
attempts = 0

pseudo_terminal = None

properties_changed_subscription = None

# A callback function supplied by the client in order to be notified
# whenever the virtual environment starts or exits. This function must
# take a boolean status as the only argument. The function
# terminal.watch_child(process_id) is not used because it only sends a
# child-exited signal when the pseudo terminal exits but does not notify
# clients when the virtual environment has started successfully.

status_callback = None

########################################################################
# Enter Virtual Environment Functions
########################################################################


def enter_virtual_environment(new_status_callback):
    """
    Reset the attempt counter, set the status call back function, and
    enter the virtual environment.

    Arguments:
    new_status_callback : function
        A callback function supplied by the client in order to be
        notified whenever the virtual environment starts or exits. This
        function must take a boolean status as the only argument.
    """

    global first_time
    global reenter
    global attempts
    global status_callback

    first_time = True
    reenter = True
    attempts = 0
    status_callback = new_status_callback

    _enter_virtual_environment()


def _enter_virtual_environment():
    """
    Start the virtual environment in the pseudo terminal.
    """

    logger.log_label('Enter virtual environment')
    logger.log_value('The virtual environment directory is', model.project.custom_root_directory)

    program = os.path.join(model.application.directory, 'commands', 'start-console')
    # The command must be a list, as required by spawn_async().
    command = ['pkexec', program, MACHINE_NAME, model.project.custom_root_directory]
    display_command = ' '.join([os.path.basename(command[1].strip('"'))] + command[2:])
    logger.log_value('Command', display_command)

    # logger.log_value('Set new pseudo terminal', 'None')
    # terminal = model.builder.get_object('terminal_page__terminal')
    # terminal.set_pty(None)

    # The process executed by spawn_async() below is not registered with
    # the processor module. As a result, this process is not
    # terminated by the interrupt_navigation_thread() function of the
    # navigator module. This allows the terminal to continue running
    # while the application navigates away from the Terminal page. The
    # pseudo terminal process must be explicitly killed by executing
    # exit_virtual_environment().

    # Allocate a new pseudo terminal.
    # The global pseudo_terminal is used by entered_virtual_environment()
    # to set the pseudo terminal for the terminal.
    global pseudo_terminal
    pseudo_terminal = Pty.new_sync(PtyFlags.DEFAULT)
    pseudo_terminal.set_utf8(True)

    # The spawn_async() parameters are as follows:
    #
    # https://lazka.github.io/pgi-docs/Vte-2.91/classes/Pty.html#Vte.Pty.spawn_async
    # inspect.getdoc(Vte.Terminal.spawn_async)
    # 'spawn_async(self,
    #              pty_flags:Vte.PtyFlags,
    #              working_directory:str=None,
    #              argv:list, envv:list=None,
    #              spawn_flags_:GLib.SpawnFlags,
    #              child_setup:GLib.SpawnChildSetupFunc=None,
    #              timeout:int,
    #              cancellable:Gio.Cancellable=None,
    #              callback:Vte.TerminalSpawnAsyncCallback=None,
    #              user_data=None)'

    # Start the virtual environment in the pseudo terminal.
    pseudo_terminal.spawn_async(
        working_directory=None,
        argv=command,
        envv=None,
        spawn_flags=(GLib.SpawnFlags.DEFAULT | GLib.SpawnFlags.SEARCH_PATH),
        child_setup=None,
        child_setup_data=None,
        timeout=-1, # milliseconds; -1 = wait indefinitely
        cancellable=None,
        callback=watch_virtual_environment,
        user_data=None)

    #
    # IMPORTANT: Do not add any code here.
    #


def child_setup(*data):
    """
    This function is executed inside the virtual environment, and the
    results are output in the virtual environment terminal. If this
    function is supplied as a parameter to spawn_async(),
    child_setup_data must also be supplied. The function spawn_async()
    requires child_setup_data to be a tuple, and it can have a value,
    such as child_setup_data=('test',), or be empty, such as
    child_setup_data=(,).

    Arguments:
    *data : object
        User data passed to this function.
    """
    logger.log_value('CHILD SETUP', 'START')
    # time.sleep(SLEEP_1000_MS)
    logger.log_value('CHILD SETUP', 'STOP')
    logger.log_value('CHILD DATA', data)


def watch_virtual_environment(pseudo_terminal, task, data):
    """
    Watch the virtual environment. Subscribe to virtual environment
    entered signals and virtual environment exited events.

    A terminal_spawn_async_callback function that is invoked when
    spawn_async() completes.
    https://lazka.github.io/pgi-docs/Gio-2.0/callbacks.html#Gio.AsyncReadyCallback

    Arguments:
    pseudo_terminal : Vte.Pty
        The pseudo terminal.
    task : Gio.Task
        Used to manage data during an asynchronous operation. Used to
        get the process id of the pseudo terminal.
    data : object
        User data passed to the callback.
    """

    logger.log_label('Watch virtual environment')

    # ------------------------------------------------------------------
    # Subscribe to virtual environment entered signals.
    # ------------------------------------------------------------------

    subscribe_virtual_environment_entered()

    # Get the pseudo terminal process id for the task.
    # The function spawn_finish() returns the child_pid, or None.
    # Success is always True, so it is not useful.
    # Gio.Task is used to manage data during an asynchronous operation.
    success, process_id = pseudo_terminal.spawn_finish(task)

    # Save the process id on the pseudo_terminal.
    logger.log_value('The pseudo terminal process id is', process_id)
    pseudo_terminal.process_id = process_id

    # ------------------------------------------------------------------
    # Subscribe to virtual environment exited events.
    # ------------------------------------------------------------------

    subscribe_virtual_environment_exited(process_id, pseudo_terminal)


########################################################################
# Enter Virtual Environment Callback Functions
########################################################################


# https://developer.gnome.org/gio/2.60/GDBusConnection.html#g-dbus-connection-signal-subscribe
def subscribe_virtual_environment_entered():
    """
    Subscribe to virtual environment entered signals, and specify the
    callback function to be invoked when the virtual environment starts.
    The callback function is entered_virtual_environment().
    """

    # logger.log_label('Subscribe virtual environment entered')

    global properties_changed_subscription

    if not properties_changed_subscription:
        system_bus = pydbus.SystemBus()
        logger.log_value('System bus id', id(system_bus))
        properties_changed_subscription = system_bus.subscribe(
            sender='org.freedesktop.systemd1',
            iface='org.freedesktop.DBus.Properties',
            signal='PropertiesChanged',
            object=None,
            arg0=None,
            flags=0,
            signal_fired=entered_virtual_environment)
        logger.log_value('Subscribe to virtual environment entered signals with subscription id', id(properties_changed_subscription))
    else:
        logger.log_value('WARNING. Subscription to virtual environment entered signal already exists with subscription id', id(properties_changed_subscription))


# https://developer.gnome.org/gio/2.60/GDBusConnection.html#g-dbus-connection-signal-unsubscribe
def unsubscribe_virtual_environment_entered():
    """
    Unsubscribe from virtual environment entered signals.
    """

    # logger.log_label('Unsubscribe virtual environment entered')

    global properties_changed_subscription

    if properties_changed_subscription:
        logger.log_value('Unsubscribe from virtual environment entered signals with subscription id', id(properties_changed_subscription))
        properties_changed_subscription.unsubscribe()
        properties_changed_subscription = None
    else:
        logger.log_value('Cannot unsubscribe from virtual environment entered signals', 'The subscription does not exist')


# https://docs.gtk.org/gio/callback.DBusSignalCallback.html
# https://lazka.github.io/pgi-docs/#Gio-2.0/callbacks.html#Gio.DBusSignalCallback
# sender, object, iface, signal, params.unpack()
def entered_virtual_environment(sender, object_path, interface, signal, parameters):
    """
    The callback function to be invoked when the pseudo terminal starts.

    Arguments:
    # connection : Gio.DBusConnection
    #     A Gio.DBusConnection.
    sender : str
        The unique bus name of the sender of the signal.
    object_path : str
        The object path that the signal was emitted on.
    interface : str
        The name of the interface.
    signal : str
        The name of the signal.
    parameters : GLib.Variant tuple
        Signal parameters that are used to determine if the virtual
        environment started successfully.
    # *user_data : object
    #     User data passed when subscribing to the signal.
    """

    parameter_a, parameter_b, parameter_c = parameters

    active_state = None
    if 'ActiveState' in parameter_b:
        active_state = parameter_b['ActiveState']

    sub_state = None
    if 'SubState' in parameter_b:
        sub_state = parameter_b['SubState']

    job_status = None
    job_path = None
    if 'Job' in parameter_b:
        job_status, job_path = parameter_b['Job']
        job_status = int(job_status)

    if active_state == 'active' and sub_state == 'running' and job_status == 0 and job_path == os.path.sep:
        logger.log_label('Entered virtual environment')
        _entered_virtual_environment(active_state, sub_state, job_status, job_path)
    # else:
    #     logger.log_label('Unable to enter virtual environment')


# https://docs.gtk.org/gio/callback.DBusSignalCallback.html
# https://lazka.github.io/pgi-docs/#Gio-2.0/callbacks.html#Gio.DBusSignalCallback
# sender, object, iface, signal, params.unpack()
def _entered_virtual_environment(active_state, sub_state, job_status, job_path):
    """
    Notify the user that the virtual environment started and reset the
    attempt counter.

    Arguments:
    active_state : str
        The ActiveState from the parameters passed to the callback.
    sub_state : str
        The SubState from the parameters passed to the callback.
    job_status : int
        The status of the Job from the parameters passed to the callback.
    job_path : str
        The path of the Job from the parameters passed to the callback.
    """

    # logger.log_value('Successfully entered virtual environment?', 'Yes')
    logger.log_value('Active State', active_state)
    logger.log_value('Sub State', sub_state)
    logger.log_value('Job status', job_status)
    logger.log_value('Job path', job_path)

    unsubscribe_virtual_environment_entered()

    # Set the pseudo terminal for the terminal.
    global pseudo_terminal
    logger.log_value('Set new pseudo terminal', pseudo_terminal.get_fd())
    terminal = model.builder.get_object('terminal_page__terminal')

    # The function terminal.reset() doesn't work.
    # Reset the terminal if the root directory has changed.
    # global custom_root_directory
    # # logger.log_value('* custom_root_directory', custom_root_directory)
    # # logger.log_value('* model.project.custom_root_directory', model.project.custom_root_directory)
    # if custom_root_directory != model.project.custom_root_directory:
    #     logger.log_value('Reset the terminal?', 'Yes')
    #     terminal.reset(True, False)
    #     custom_root_directory = model.project.custom_root_directory
    # else:
    #     logger.log_value('Reset the terminal?', 'No')

    terminal.set_pty(pseudo_terminal)

    # Display message in the terminal.
    send_message_to_terminal(f'{BOLD_GREEN}You have entered the virtual environment.{NORMAL}')

    # https://stackoverflow.com/questions/11686510/how-to-enable-transparency-in-vte-terminal

    # Notify clients that the virtual environment started.
    global status_callback
    if status_callback: status_callback(True)

    # Reset attempt.
    global first_time
    first_time = False
    global attempts
    attempts = 0


########################################################################
# Exit Virtual Environment Callback Functions
########################################################################


def subscribe_virtual_environment_exited(process_id, pseudo_terminal):
    """
    Subscribe virtual environment exited events, and specify the
    callback function to be invoked when the virtual environment exits.
    The callback function is exited_virtual_environment().

    Arguments:
    process_id : int
        The process id of the pseudo terminal.
    pseudo_terminal : Vte.Pty
        The pseudo terminal.
    """

    # logger.log_label('Subscribe virtual environment exited')

    # Set a function to be called when the child process exits.
    # https://lazka.github.io/pgi-docs/#GLib-2.0/callbacks.html#GLib.ChildWatchFunc
    # https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.child_watch_add
    logger.log_value('Subscribe to virtual environment exited events for process id', process_id)
    # GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, process_id, exited_virtual_environment, pseudo_terminal)
    GLib.child_watch_add(GLib.PRIORITY_HIGH_IDLE, process_id, exited_virtual_environment, pseudo_terminal)

    # To use the terminal.watch_child(process_id) function instead,
    # exited_virtual_environment() must be registered as the handler for
    # child-exited signals.
    #
    # logger.log_value('Watch child', process_id)
    # terminal = model.builder.get_object('terminal_page__terminal')
    # terminal.watch_child(process_id)


def exited_virtual_environment(process_id, status, pseudo_terminal):
    """
    The callback function to be invoked when the pseudo terminal exits.

    This function's arguments match the arguments for:
    https://lazka.github.io/pgi-docs/#GLib-2.0/callbacks.html#GLib.ChildWatchFunc

    GLib.spawn_close_pid() should be used on all platforms, even though
    it doesn't do anything under UNIX.
    https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.spawn_close_pid
    GLib.spawn_close_pid(process_id)

    Arguments:
    process_id : int
        The process id of the pseudo terminal.
    status : int
        The exit status of the pseudo terminal.
    pseudo_terminal : Vte.Pty
        The pseudo terminal.
    """

    # References:
    # https://stackoverflow.com/questions/1535672/how-to-interpret-status-code-in-python-commands-getstatusoutput/1535675#1535675
    # https://lazka.github.io/pgi-docs/GLib-2.0/functions.html#GLib.spawn_check_exit_status
    # https://docs.python.org/3/library/os.html

    # Different ways to exit the terminal, and the corresponding status
    # values:
    #
    # • Execute the following from outside Cubic's terminal.
    #   $ pkexec /usr/share/cubic/commands/stop-process <pid of start-console>
    #   status = 9
    #
    # • Execute the following from outside Cubic's terminal.
    #   $ sudo kill -9 <pid of start-console>
    #   status = 9
    #
    # • Execute the following from outside Cubic's terminal.
    #   $ sudo pkill --full start-console
    #   status = 15
    #   $ sudo pkill --signal 9 --full start-console
    #   status = 9
    #
    # • Execute the following from outside Cubic's terminal.
    #   $ sudo machinectl terminate cubic
    #   status = 256
    #
    # • Type "exit" in Cubic's terminal.
    #   status = 0
    #
    # • Click Quit, Back, Next, or the window's exit control.
    #   status = 9
    #   Uses the exit_virtual_environment_using_kill() function.

    logger.log_label('Exited virtual environment')

    # The following message is printed to the terminal when the virtual
    # environment is exited using "sudo machinectl terminate cubic":
    #   "Container termination requested. Exiting.
    #    Container cubic terminated by signal KILL."
    # To prevent this message from being displayed, the terminal's
    # pseudo terminal can be reset.
    #
    # In Ubuntu 20.04, Vte crashes with Segmentation fault when the
    # terminal's Pty is set to None. Reference Bug #1877232:
    #   https://bugs.launchpad.net/cubic/+bug/1877232.
    #
    # Reset the terminal's Pty.
    # terminal = model.builder.get_object('terminal_page__terminal')
    # terminal.set_pty(None)
    #
    # In Ubuntu 19.10,  Vte crashes with Segmentation fault when the
    # terminal's Pty is set to a new uninitialized Pty():
    #   "VTE-CRITICAL **: 19:00:44.648: int vte_pty_get_fd(VtePty*):
    #    assertion 'priv->pty_fd != -1' failed"
    #
    # Set a new dummy Pty for the terminal.
    # terminal = model.builder.get_object('terminal_page__terminal')
    # dummy_pseudo_terminal = Pty.new_sync(PtyFlags.DEFAULT)
    # terminal.set_pty(dummy_pseudo_terminal)
    #
    # To avoid both issues above, do not reset the terminal's Pty.

    # The signal number that killed the process.
    signal = status % 256  # Gets the low byte.

    # The exit status of the process (only set if the signal is 0).
    exit_code = status >> 8  # Gets the high byte.

    logger.log_value('Process id', process_id)
    logger.log_value('Pseudo terminal', pseudo_terminal.get_fd())
    logger.log_value('Status', BOLD_CYAN + str(status) + NORMAL)
    logger.log_value('Signal', BOLD_RED + str(signal) + NORMAL)
    logger.log_value('Exit Code', BOLD_YELLOW + str(exit_code) + NORMAL)

    # Notify clients that the virtual environment exited.
    global status_callback
    if status_callback: status_callback(False)

    # Unsubscribe from virtual environment entered signals because the
    # virtual environment already exited.
    unsubscribe_virtual_environment_entered()

    global MAX_ATTEMPTS
    global first_time
    global reenter
    global attempts

    attempts += 1

    logger.log_value('MAX_ATTEMPTS', MAX_ATTEMPTS)
    logger.log_value('First time', first_time)
    logger.log_value('Reenter', reenter)
    logger.log_value('Attempts', f'{BOLD_YELLOW}{attempts} of {MAX_ATTEMPTS} times{NORMAL}')

    # The status is a 16-bit number:
    # - The low byte (right byte) contains the signal number that killed
    #   the process.
    # - The high byte (left byte) is only set when the signal is zero.
    #   It contains the exit status of the process.
    #
    # ---------  ------  ---------  --------------------------------
    # Status     Signal  Exit Code  Note
    # ---------  ------  ---------  --------------------------------
    #         0       0          0  Process exited without error
    #     1-255   1-255          0  Process terminated by signal
    #       256       0          1  Process terminated by machinectl
    # 257-65280       0  257-65280  Process exited with error
    # ---------  ------  ---------  --------------------------------

    # Display message in the terminal.
    if (first_time and attempts == MAX_ATTEMPTS) or (not first_time and attempts == 1):
        if status == 0:
            # The process exited normally.
            GLib.idle_add(send_message_to_terminal, f'{BOLD_YELLOW}You have exited the virtual environment.{NORMAL}')
        elif status >= 1 and status <= 255:
            # The process exited due to a signal.
            # Do not use GLib.idle_add().
            send_message_to_terminal(f'{NEW_LINE}{BOLD_RED}You have exited the virtual environment.{NORMAL}')
        elif status == 256:
            # The process was terminated by machinectl terminate.
            GLib.idle_add(send_message_to_terminal, f'{BOLD_RED}You have exited the virtual environment.{NORMAL}')
        elif status >= 257 and status <= 65280:
            # The process exited normally with an error code.
            GLib.idle_add(send_message_to_terminal, f'{BOLD_YELLOW}You have exited the virtual environment.{NORMAL}')
        else:
            # This situation will never happen.
            GLib.idle_add(send_message_to_terminal, f'{BOLD_BLUE}You have exited the virtual environment.{NORMAL}')
        # Pause to allow GLib.idle_add() to display the message.
        time.sleep(SLEEP_0250_MS)

    # Decide to reenter the virtual environment.
    if reenter and attempts < MAX_ATTEMPTS:
        logger.log_value('Attempt to restart the virtual environment?', 'Yes')
        _enter_virtual_environment()
    else:
        reenter = False
        logger.log_value('Attempt to restart the virtual environment?', 'No')


########################################################################
# Exit Virtual Environment Functions
########################################################################


def exit_virtual_environment():
    """
    Exit the virtual environment.

    The process executed by spawn_async() in the
    _enter_virtual_environment() function is not registered with the
    processor module. As a result, this process is not terminated
    by the interrupt_navigation_thread() function of the navigator
    module. This permits the terminal to continue running while the
    application navigates away from the Terminal page, and is useful for
    navigating to the Terminal Copy page. Therefore, the pseudo terminal
    process must be explicitly killed by executing
    exit_virtual_environment().
    """

    logger.log_label('Exit virtual environment')

    global reenter
    reenter = False
    try:
        sys.stdout.flush()
        exit_virtual_environment_using_kill()
    except Exception as exception:
        logger.log_value('Warning', exception)


def exit_virtual_environment_using_kill():
    """
    Exit the virtual environment process using kill.
    """

    # logger.log_label('Exit the virtual environment process using kill')

    terminal = model.builder.get_object('terminal_page__terminal')
    pseudo_terminal = terminal.get_pty()
    if pseudo_terminal:
        if hasattr(pseudo_terminal, 'process_id'):
            # If the pseudo terminal does not have a process id attribute,
            # then the virtual environment has already exited.
            process_id = pseudo_terminal.process_id
            program = os.path.join(model.application.directory, 'commands', 'stop-process')
            # TODO: Should we use execute_synchronous_unregistered() ?
            command = ['pkexec', program, process_id]
            result, exit_status, signal_status = execute_synchronous(command)
        else:
            logger.log_value('There is no virtual environment to exit. The pseudo terminal is ', pseudo_terminal)
    else:
        logger.log_value('There is no virtual environment to exit. The pseudo terminal is ', pseudo_terminal)


'''
def exit_virtual_environment_using_kill_ORIGINAL():
    """
    Exit the virtual environment process using kill.
    """

    logger.log_label('Exit the virtual environment process using kill')

    terminal = model.builder.get_object('terminal_page__terminal')
    pseudo_terminal = terminal.get_pty()
    if pseudo_terminal:
        process_id = pseudo_terminal.process_id
        exit_status, signal_status = terminate_process(process_id)
'''


def exit_virtual_environment_using_machinectl():
    """
    Exit virtual environment using machinectl'.
    """

    logger.log_label('Exit virtual environment using machinectl')

    program = os.path.join(model.application.directory, 'commands', 'stop-console')
    # TODO: Should we use execute_synchronous_unregistered() ?
    command = ['pkexec', program, MACHINE_NAME]
    result, exit_status, signal_status = execute_synchronous(command)


########################################################################
# Check Virtual Environment Functions
########################################################################


def is_virtual_environment_running():
    """
    Check if the virtual environment is running. This function is not
    very reliable because the virtual environment may take some time to
    start or stop.

    Returns:
    : bool
        True if the virtual environment is running. False if the virtual
        environment is not running.
    """

    logger.log_label('Check virtual environment')
    command = 'machinectl --property=State show cubic'
    result, exit_status, signal_status = execute_synchronous(command)
    if 'running' in result:
        logger.log_value('Is the virtual environment running?', 'Yes')
        is_running = True
    else:
        logger.log_value('Is the virtual environment running?', 'No')
        is_running = False

    return is_running


########################################################################
# Support Functions
########################################################################
'''
def get_bash_process_id(pseudo_terminal_process_id):

    logger.log_label('Get the bash child process id for the pseudo terminal')

    bash_process_id = None

    command = f'pstree -p {pseudo_terminal_process_id}'
    process_pid, result, exit_status, signal_status = execute_synchronous_unregistered(command)

    if not exit_status and not signal_status:
        bash_process_id_information = re.search(r'bash\\((\\d+)\\)', result)
        if bash_process_id_information:
            bash_process_id = bash_process_id_information.group(1)
        else:
            logger.log_value(f'1. Unable to get the bash child process id for the pseudo terminal with process id {process_id} using result', result)
    else:
        logger.log_value(f'2. Unable to get the bash child process id for the pseudo terminal with process id  {process_id} using result', result)

    return bash_process_id


def get_current_directory():

    current_directory = None

    logger.log_label('Get the current directory')

    global pseudo_terminal
    bash_process_id = get_bash_process_id(pseudo_terminal.process_id)

    program = os.path.join(model.application.directory, 'commands', 'current-directory')
    command = ['pkexec', program, bash_process_id]
    process_pid, result, exit_status, signal_status = execute_synchronous_unregistered(command)

    if not exit_status and not signal_status:
        current_directory = result
        logger.log_value('The current directory is', current_directory)
    else:
        logger.log_value('Unable to get the current directory using result', current_directory)

    return current_directory
'''


def get_current_directory():
    """
    Get the current directory in the terminal.

    Returns:
    : str
        The current directory in the terminal or None if the current
        directory could not be determined.
    """

    logger.log_label('Get the current directory')

    global pseudo_terminal
    process_id = pseudo_terminal.process_id
    program = os.path.join(model.application.directory, 'commands', 'current-directory')
    command = ['pkexec', program, process_id]
    process_pid, result, exit_status, signal_status = execute_synchronous_unregistered(command)

    if not exit_status and not signal_status:
        # logger.log_value('The current directory is', result)
        return result
    else:
        logger.log_value('Unable to get the current directory', result)
        return None


def send_message_to_terminal(text=None):
    """
    Send a message to the terminal and print a new line.

    Arguments:
    text : str
        Optional text to send to the terminal. The default value is
        None. If text is None, a new line is printed to the terminal.
    """

    terminal = model.builder.get_object('terminal_page__terminal')

    try:
        # Using Vte.Terminal 2.90 or 2.91
        # Print the message.
        if text:
            terminal.feed(NEW_LINE + text, -1)
        # Print a new line. (This is necessary).
        terminal.feed(NEW_LINE, -1)
        logger.log_value('Send text to terminal', text)
    except TypeError:
        # Using Vte.Terminal "new" 2.91
        # Print the message.
        if text:
            terminal.feed(bytes(NEW_LINE + text, encoding='utf-8'))
        # Print a new line. (This is necessary).
        terminal.feed(bytes(NEW_LINE, encoding='utf-8'))
        logger.log_value('Send bytes to terminal', text)


def send_command_to_terminal(text):
    """
    This function is not used.
    This function is the same as send_text_to_terminal().

    Send a command to the terminal.

    Arguments:
    text : str
        The command to send to the terminal.
    """

    terminal = model.builder.get_object('terminal_page__terminal')
    # Vte.Terminal 2.90 or 2.91
    # terminal.feed_child(text, -1)
    # Vte.Terminal 2.91
    terminal.feed_child(bytes(text, encoding='utf-8'))
    logger.log_value('Send bytes to terminal', text)


def send_text_to_terminal(text):
    """
    This function is used by terminal_page to drag and drop text into
    the terminal.
    This function is the same as send_command_to_terminal().

    Send text to the terminal.

    Arguments:
    text : str
        The text to send to the terminal.
    """

    terminal = model.builder.get_object('terminal_page__terminal')
    # Vte.Terminal 2.90 or 2.91
    # terminal.feed_child(text, -1)
    # Vte.Terminal 2.91
    terminal.feed_child(bytes(text, encoding='utf-8'))
    logger.log_value('Send bytes to terminal', text)
