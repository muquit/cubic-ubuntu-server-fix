#!/usr/bin/python3

########################################################################
#                                                                      #
# constructor.py                                                       #
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

# https://apt-team.pages.debian.net/python-apt/library/index.html
# https://docs.python.org/3/library/time.html#time.strftime
# https://docs.python.org/3/library/time.html#time.strptime
# https://time.strftime.org/

########################################################################
# Imports
########################################################################

# import apt
import os
import pickle
import platform
import re
import time
import zlib

from cubic.constants import BLANK_VERSION_0000, CUBIC_VERSION_0000
from cubic.constants import ISO_MOUNT_POINT, CUSTOM_ROOT_DIRECTORY, CUSTOM_DISK_DIRECTORY
from cubic.constants import LOG_FILE_NAME
from cubic.constants import NUMBERS_LOWER_CASE, NUMBERS_TITLE_CASE
from cubic.constants import OK
from cubic.constants import TIME_STAMP_FORMAT, TIME_STAMP_FORMAT_YYYYMMDDHHMMSS, VERSION_NUMBER_FORMAT
from cubic.utilities import logger
from cubic.utilities.processor import execute_synchronous

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Functions
########################################################################


def add_prefix(prefix, text):
    """
    Add the prefix to the text.

    Arguments:
    prefix : str
        The prefix to add.
    text:
        The text.

    Returns:
    : str
        The new text with the prefix added.
    : None
        If the text did not change.
    """

    if not text.startswith(prefix):
        return f'{prefix} {text}'
    else:
        return None


def remove_prefix(prefix, text):
    """
    Remove the prefix from the text.

    Arguments:
    prefix : str
        The prefix to remove.
    text:
        The text.

    Returns:
    : str
        The new text with the prefix removed.
    : None
        If the text did not change.
    """

    if text.startswith(prefix):
        return text[2:]
    else:
        return None


def change_prefix(prefix, text, is_prepend):
    """
    Prepend or remove the prefix from the text.

    Arguments:
    prefix : str
        The prefix to append, or the existing prefix to remove.
    text:
        The text to append or remove the prefix from.
    is_prepend : bool
        True to prepend the prefix.
        False to remove the prefix.

    Returns:
    : str
        The new text with the prefix prepended or removed.
    None
        If the text did not change.
    """

    if not text.startswith(prefix) and is_prepend:
        # Append prefix.
        return f'{prefix} {text}'
    elif text.startswith(prefix) and not is_prepend:
        # Remove_prefix.
        return text[2:]
    return None


def number_as_text(number, title_case=False):
    """
    Get the word or localized numeral format of the number

    Arguments:
    number : int
        The number to format.
    title_case : bool
        Use title case for the word representation of the number.
    Returns:
    : str
        The word format of the number in title or lower case, or the
        localized numeral format of the number if the number is greater
        than 9.
    """

    if number < len(NUMBERS_TITLE_CASE):
        if title_case:
            return NUMBERS_TITLE_CASE[number]
        else:
            return NUMBERS_LOWER_CASE[number]
    else:
        return f'{number:n}'


def get_plural(singular_text, plural_text, number):
    """
    Select the singular or plural text.

    Arguments:
    singular_text : str
        Text that should be used if the number is one.
    plural_text : str
        Text that should be used if the number is not one (i.e. if the
        number is 0, 2, 3, etc.).

    Returns:
    : str
        The singular text if the number is 1, or plural text otherwise.
    """

    return singular_text if number == 1 else plural_text


def assemble_paths(*paths):
    """
    Creates a list of paths using using an arbitrary number of lists
    containing path components (i.e. file names, directory names, or
    sub-paths).

    Example:

        results = assemble_paths(['start'],                      \
                                 ['dir_a', 'dir_b'],             \
                                 ['file_1', 'file_2', 'file_3'], \
                                 ['*'])

        print(results)

        ['start/dir_a/file_1/*', \
         'start/dir_a/file_2/*', \
         'start/dir_a/file_3/*', \
         'start/dir_b/file_1/*', \
         'start/dir_b/file_2/*', \
         'start/dir_b/file_3/*']

    Arguments:
    *paths : arbitrary number of lists of str
        An arbitrary number of lists. Each list contains path components
        (i.e. file names, directory names, or sub-paths).

    Returns:
    results : list of str
        A list of paths.
    """
    results = []
    prefix = ''
    _assemble_paths(prefix, paths, results)
    return results


def _assemble_paths(prefix, paths, results):
    """
    Creates a list of paths using using a list of lists containing path
    components (i.e. file names, directory names, or sub-paths).

    Example: paths = ['start'], \
                     ['dir_a', 'dir_b'], \
                     ['file_1', 'file_2', 'file_3'], \
                     ['*']

    Arguments:
    prefix : str
        The incomplete file path that is being assembled.
    paths : list of lists of str
        A list of lists containing path components (i.e. file names,
        directory names, or sub-paths).
    results : list of str
        A list of paths.

    Returns:
        None
    """
    if not paths:
        results.append(prefix)
    else:
        top_row = paths[0]
        paths = paths[1:]
        for column in top_row:
            path = os.path.join(prefix, column)
            _assemble_paths(path, paths, results)


def construct_rsync_includes(*paths):
    """
    Create --include="..." arguments for the rsync command.

    Arguments:
    *paths : arbitrary number of lists of str
        An arbitrary number of lists. Each list contains path components
        (i.e. file names, directory names, or sub-paths).

    Returns:
    includes : str
        A series --include="..." arguments.
    """

    paths = assemble_paths(*paths)
    logger.log_value('The include paths are', paths)

    includes = ''
    for path in paths:
        includes += f' --include="{path}"'
    return includes.strip()


def construct_rsync_excludes(*paths):
    """
    Create --exclude="..." arguments for the rsync command.

    Arguments:
    *paths : arbitrary number of lists of str
        An arbitrary number of lists. Each list contains path components
        (i.e. file names, directory names, or sub-paths).

    Returns:
    excludes : str
        A series --exclude="..." arguments.
    """

    paths = assemble_paths(*paths)
    logger.log_value('The exclude paths are', paths)

    excludes = ''
    for path in paths:
        excludes += f' --exclude="{path}"'
    return excludes.strip()


def get_os_distribution(root_directory='/'):
    """
    Get the value of ID from '/etc/os-release'

    Arguments:
    root_directory : str
        Optional root directory of the OS. The default value is "/",
        which will get the distribution of the host OS. Use
        model.project.custom_root_directory to get the distribution of
        the custom OS.

    Returns:
    distribution : bool
        True OS distribution.
    """

    distribution = None
    file_path = os.path.join(root_directory, 'etc/os-release')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.split('=', 1)
                key = key.strip().upper() if key else None
                if key == 'ID':
                    distribution = value.strip().lower() if value else None
                    break

    return distribution


def os_is_distribution(distribution, root_directory=os.path.sep):
    """
    Read the value of ID from "/etc/os-release".

    Arguments:
    distribution
        The distribution to check, for example, "pop" for Pop!_OS or
        "elementary" for Elementary.
    root_directory : str
        Optional root directory of the OS. The default value is "/",
        which will get the distribution of the host OS. Use
        model.project.custom_root_directory to get the distribution of
        the custom OS.

    Returns:
    is_distribution : bool
        True if the OS distribution matches the specified distribution.
        False otherwise.
    """

    is_distribution = False
    distribution = distribution.lower()
    file_path = os.path.join(root_directory, 'etc/os-release')
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line: continue
                if line.startswith('#'): continue
                key, value = line.split('=', 1)
                key = key.strip().upper() if key else None
                value = value.strip().lower() if value else None
                if key == 'ID':
                    if root_directory == '/':
                        logger.log_value('The host OS distribution is', value)
                    else:
                        logger.log_value('The custom OS distribution is', value)
                    if distribution in value:
                        is_distribution = True
                        break
                elif key == 'ID_LIKE':
                    if root_directory == '/':
                        logger.log_value('The host OS distribution like is', value)
                    else:
                        logger.log_value('The custom OS distribution like is', value)
                    if distribution in value:
                        is_distribution = True
                        break

    return is_distribution


def get_kernel_version():
    """
    Get the version of the currently running kernel.

    Returns:
    result : str
        The version of the currently running kernel.
    """

    return platform.release()


def get_kernel_version_ALTERNATIVE():
    """
    Get the version of the currently running kernel.

    Returns:
    result : str
        The version of the currently running kernel.
    """

    command = 'uname -r'
    result, exit_status, signal_status = execute_synchronous(command)

    return result


def get_display_version(package_version):
    """
    Get a displayable package version number. Delimiter characters, such as "-",
    "+", "~", etc., are replaced with ".", and the version is truncated to
    exclude alpha characters.

    For example, "2021.10-61-release~202110150101~ubuntu21.10.1" will be
    converted to "2021.10.61".

    Returns:
    : str
        A truncated package version with leading digits delimited by ".". If a
        displayable version can not be determined, the version is "00.00.00".
    """

    try:
        # return re.search(r'([\d\W]*\d).*', re.sub(r'\W', '.', package_version))[1]
        version = re.sub(r'\W', '.', package_version)
        version = re.search(r'(^[\d\W]*\d).*', version)
        version = version.group(1)
        return version
    except TypeError:
        logger.log_value('Type error getting display version for', package_version)
        version = BLANK_VERSION_0000
        return version
    except IndexError:
        logger.log_value('Index error getting display version for', package_version)
        version = BLANK_VERSION_0000
        return version
    except AttributeError:
        logger.log_value('Attribute error getting display version for', package_version)
        version = BLANK_VERSION_0000
        return version
    except Exception:
        logger.log_value('Exception getting display version for', package_version)
        version = BLANK_VERSION_0000
        return version


def get_display_version_ORIGINAL(package_version):
    """
    Get a displayable Cubic version in "YYYY.MM.RR" format. For example,
    the package version "2021.10-61-release~202110150101~ubuntu21.10.1"
    maps to "2021.10.61".

    Returns:
    : str
        The Cubic package version in "YYYY.MM.RR" format.
    """

    if package_version:
        return '.'.join(package_version.split('-')[0:2])
    else:
        return CUBIC_VERSION_0000


def get_installed_packages_list(root_directory=os.path.sep):
    """
    This function is not used.

    Create a list of installed package details. Each package detail is a
    list containing the following elements. Only package name and
    package version are populated.
        1: package name
        2: package version

    Also see prepare_page.create_package_details_list().

    Arguments:
    root_directory : str
        The root directory of "var/lib/dpkg" (the dpkg database).

    Returns:
    package_details_list : list
        A list of package details.
    """

    logger.log_label('Create list of installed packages')

    package_details_list = []

    # The --root option was added to dpkg-query in Ubuntu 22.04 (dpkg
    # package 1.21.1ubuntu2.1 and higher). Older versions of dpkg-query
    # only support the --admindir option (dpkg package 1.20.9ubuntu2.2
    # and lower).
    admin_directory = os.path.join(root_directory, 'var/lib/dpkg')
    command = 'dpkg-query --admindir="%s" --show' % (admin_directory)
    result, exit_status, signal_status = execute_synchronous(command)

    if result:
        packages = result.splitlines()
        for package in packages:
            package_name, package_version = package.split()

            # Create a new package details for the current package.
            # 1: package name
            # 2: package version
            package_details = [package_name, package_version]
            package_details_list.append(package_details)

    package_count = len(package_details_list)
    logger.log_value('Total number of installed packages', package_count)

    return package_details_list


'''
def get_installed_packages_list_01(root_directory=os.path.sep):
    """
    This function is not used.
    See prepare_page.create_package_details_list().

    Get a list of installed packages.

    Arguments:
    root_directory : str
        Optional root directory of "var/lib/dpkg" (the dpkg database).
        The default value is "/", which will get the packages list for
        the host system. Use model.project.custom_root_directory to get
        the packages list for the custom OS.

    Returns:
    installed_packages_list : list of tuples
        A list of tuples (package name, package version).
    """

    installed_packages_list = []

    apt_cache = apt.Cache(rootdir=root_directory)
    for package in apt_cache:
        if apt_cache[package.name].is_installed:
            # package_details = f'{package.name}\t{package.installed.version}'
            package_details = (package.name, package.installed.version)
            installed_packages_list.append(package_details)
    package_count = len(installed_packages_list)
    logger.log_value('Total number of installed packages', package_count)

    return installed_packages_list


def get_installed_packages_list(root_directory=os.path.sep):
    """
    This function is not used.

    Create a list of installed package details. Each package detail is a
    list containing the following elements. Only package name and
    package version are populated.
        1: package name
        2: package version

    Also see prepare_page.create_package_details_list().

    Arguments:
    root_directory : str
        The root directory of "var/lib/dpkg" (the dpkg database).

    Returns:
    package_details_list : list
        A list of package details.
    """

    logger.log_label('Create list of installed packages')

    package_details_list = []

    # The --root option was added to dpkg-query in Ubuntu 22.04 (dpkg
    # package 1.21.1ubuntu2.1 and higher). Older versions of dpkg-query
    # only support the --admindir option (dpkg package 1.20.9ubuntu2.2
    # and lower).
    command = 'dpkg-query --root="%s" --show' % (root_directory)
    result, exit_status, signal_status = execute_synchronous(command)

    if result:
        packages = result.splitlines()
        for package in packages:
            package_name, package_version = package.split()

            # Create a new package details for the current package.
            # 1: package name
            # 2: package version
            package_details = [package_name, package_version]
            package_details_list.append(package_details)

    package_count = len(package_details_list)
    logger.log_value('Total number of installed packages', len(package_details_list))

    return package_details_list
'''


def get_package_version(package_name, root_directory=os.path.sep):
    """
    Get the installed version of the specified package.

    Arguments:
    package_name : str
        The name of the package.
    root_directory : str
        Optional root directory of "var/lib/dpkg" (the dpkg database).
        The default value is "/", which will get the version of the
        specified package installed on the host system. Use
        model.project.custom_root_directory to get the version of the
        specified package installed on the on the custom OS.

    Returns:
    : str
        The version of the specified package, or None if the package
        does not exist.
    """

    # The --root option was added to dpkg-query in Ubuntu 22.04 (dpkg
    # package 1.21.1ubuntu2.1 and higher). Older versions of dpkg-query
    # only support the --admindir option (dpkg package 1.20.9ubuntu2.2
    # and lower).
    admin_directory = os.path.join(root_directory, 'var/lib/dpkg')
    command = 'dpkg-query --admindir="%s" --show --showformat="${Version}\n" "%s"' % (admin_directory, package_name)
    result, exit_status, signal_status = execute_synchronous(command)

    return result if exit_status == OK else None


'''
See https://bugs.launchpad.net/cubic/+bug/1952803
See https://answers.launchpad.net/cubic/+question/699691

from cubic.navigator import InterruptException
def get_package_version_01(package_name, root_directory=os.path.sep):
    """
    Get the installed version of the specified package.

    Arguments:
    package_name : str
        The name of the package.
    root_directory : str
        Optional root directory of "var/lib/dpkg" (the dpkg database).
        The default value is "/", which will get the version of the
        specified package installed on the host system. Use
        model.project.custom_root_directory to get the version of the
        specified package installed on the on the custom OS.

    Returns:
    : str
        The version of the specified package, or None if the package
        does not exist.
    """

    # Exception hierarchy:
    #   Object
    #   └── BaseException
    #       └── Exception
    #           ├── builtins.OSError
    #           │   ├── apt.cache.FetchCancelledException
    #           │   ├── apt.cache.FetchFailedException
    #           │   └── apt.cache.LockFailedException
    #           ├── builtins.SystemError
    #           │   └── apt_pkg.Error
    #           ├── builtins.ValueError
    #           │   └── apt_pkg.CacheMismatchError
    #           ├── cubic.navigator.InterruptException
    #           └── SystemError

    try:
        apt_cache = apt.Cache(rootdir=root_directory)
        package = apt_cache[package_name]
        return package.installed.version
    except InterruptException as exception:
        raise exception
    except Exception as exception:
        logger.log_value('Error. Unable to get the package version', package_name)
        logger.log_value('The exception is', exception)
        return None


import apt_pkg
def get_package_version_02(package_name, root_directory=os.path.sep):
    """
    Get the installed version of the specified package.

    Arguments:
    package_name : str
        The name of the package.
    root_directory : str
        Optional root directory of "var/lib/dpkg" (the dpkg database).
        The default value is "/", which will get the version of the
        specified package installed on the host system. Use
        model.project.custom_root_directory to get the version of the
        specified package installed on the on the custom OS.

    Returns:
    : str
        The version of the specified package, or None if the package
        does not exist.
    """

    # Exception hierarchy:
    #   Object
    #   └── BaseException
    #       └── Exception
    #           ├── builtins.OSError
    #           │   ├── apt.cache.FetchCancelledException
    #           │   ├── apt.cache.FetchFailedException
    #           │   └── apt.cache.LockFailedException
    #           ├── builtins.SystemError
    #           │   └── apt_pkg.Error
    #           ├── builtins.ValueError
    #           │   └── apt_pkg.CacheMismatchError
    #           ├── cubic.navigator.InterruptException
    #           └── SystemError

    try:
        apt_cache = apt.Cache(rootdir=root_directory)
        package = apt_cache[package_name]
        return package.installed.version
    except AttributeError as exception:
        # AttributeError: 'NoneType' object has no attribute 'version'
        return None
    except KeyError as exception:
        # KeyError: "The cache has no package named '___'".
        return None
    except apt.cache.FetchCancelledException
        # Exception that is thrown when the user cancels a fetch operation.
        return None
    except apt.cache.FetchFailedException
        # Exception that is thrown when fetching fails.
        return None
    except apt.cache.LockFailedException
        # Exception that is thrown when locking fails.
        return None
    except apt_pkg.Error as exception:
        # Exception class for most python-apt exceptions. This class
        # replaces the use of SystemError in previous versions of
        # python-apt. It inherits from SystemError, so make sure to
        # catch this class first.
        return None
    except apt_pkg.CacheMismatchError as exception:
        # Raised when passing an object from a different cache to apt_pkg.DepCache methods
        return None
    except SystemError as exception:
        # Inherits from Exception.
        return None


def get_package_version_03(package_name, root_directory=os.path.sep):
    """
    Get the installed version of the specified package.

    Arguments:
    package_name : str
        The name of the package.
    root_directory : str
        Optional root directory of "var/lib/dpkg" (the dpkg database).
        The default value is "/", which will get the version of the
        specified package installed on the host system. Use
        model.project.custom_root_directory to get the version of the
        specified package installed on the on the custom OS.

    Returns:
    : str
        The version of the specified package, or None if the package
        does not exist.
    """

    # Exception hierarchy:
    #   Object
    #   └── BaseException
    #       └── Exception
    #           ├── builtins.OSError
    #           │   ├── apt.cache.FetchCancelledException
    #           │   ├── apt.cache.FetchFailedException
    #           │   └── apt.cache.LockFailedException
    #           ├── builtins.SystemError
    #           │   └── apt_pkg.Error
    #           ├── builtins.ValueError
    #           │   └── apt_pkg.CacheMismatchError
    #           ├── cubic.navigator.InterruptException
    #           └── SystemError

    try:
        apt_cache = apt.Cache(rootdir=root_directory)
        package = apt_cache[package_name]
        return package.installed.version
    except AttributeError as exception:
        # AttributeError: 'NoneType' object has no attribute 'version'
        return None
    except KeyError as exception:
        # KeyError: "The cache has no package named '___'".
        return None


def get_package_version_04(package_name, root_directory=os.path.sep):
    """
    Get the installed version of the specified package.

    Arguments:
    package_name : str
        The name of the package.
    root_directory : str
        Optional root directory of "var/lib/dpkg" (the dpkg database).
        The default value is "/", which will get the version of the
        specified package installed on the host system. Use
        model.project.custom_root_directory to get the version of the
        specified package installed on the on the custom OS.

    Returns:
    : str
        The version of the specified package, or None if the package
        does not exist.
    """

    # The --root option was added to dpkg-query in Ubuntu 22.04 (dpkg
    # package 1.21.1ubuntu2.1 and higher). Older versions of dpkg-query
    # only support the --admindir option (dpkg package 1.20.9ubuntu2.2
    # and lower).
    command = 'dpkg-query --root="%s" --show --showformat="${Version}\n" "%s"' % (root_directory, package_name)
    result, exit_status, signal_status = execute_synchronous(command)

    return result if exit_status == OK else None
'''


def construct_custom_iso_version_number():
    """
    Construct the custom ISO version number using the current date.

    Returns:
    version : str
        A custom ISO version number.
    """

    # logger.log_label('Construct custom disk image version number')

    version = time.strftime(VERSION_NUMBER_FORMAT)

    # logger.log_value('The constructed custom disk image version number is', version)

    return version


def get_current_time_stamp(time_stamp_format=TIME_STAMP_FORMAT):
    """
    Get the current time stamp in the specified format.

    Arguments:
    time_stamp : str
        Optional time stamp format. The default is TIME_STAMP_FORMAT.

    Returns:
    time_stamp : str
        The current time stamp.
    """

    # logger.log_label('Get the current time stamp in the specified format')

    time_stamp = time.strftime(time_stamp_format)

    return time_stamp


def reformat_time_stamp(time_stamp, new_format, *old_formats):
    """
    Convert a time stamp to a new format.

    Arguments:
    time_stamp : str
        The original time stamp string to be converted.
    new_format: str
        The format of the new time stamp string.
    old_formats: str
        A tuple of possible old time stamp formats to try.

    Returns:
    time_stamp : str
        The reformatted time stamp.
    """

    # logger.log_label('Get current time stamp in localized format')

    time_stamp = time_stamp.strip()
    logger.log_value('Reformat the time stamp', time_stamp)

    if not old_formats:
        old_formats = (TIME_STAMP_FORMAT, )

    for old_format in old_formats:
        logger.log_value('Try old time stamp format', old_format)
        try:
            struct_time = time.strptime(time_stamp, old_format)
            logger.log_value('Matched the time stamp format?', 'Yes')
            break
        except ValueError as exception:
            logger.log_value('Matched the time stamp format?', 'No')
            # This situation should never happen. If it does, time.strftime()
            # will result in an exception, and the original cause will need to
            # identified and corrected.
            struct_time = None

    logger.log_value('The new time stamp format is', new_format)

    time_stamp = time.strftime(new_format, struct_time).strip()
    logger.log_value('The reformatted time stamp is', time_stamp)

    return time_stamp


def get_file_time_stamp(file_path):
    """
    Get the last modification time stamp of the specified file.

    Returns:
    time_stamp : str
        The last modification time stamp of the specified file.
    """

    # logger.log_label('Get file create date time')

    time_stamp = os.path.getmtime(file_path)
    time_stamp = time.localtime(time_stamp)
    time_stamp = time.strftime(TIME_STAMP_FORMAT, time_stamp)

    return time_stamp


def construct_log_file_path(project_directory):
    """
    Construct the full file path for the log file. This file is located
    in the Cubic project directory.

    Arguments:
    project_directory : str
        The project directory.

    Returns:
    file_path : str
        The full file path for the config.conf file.
    """

    # logger.log_label('Construct the log file path')
    # logger.log_value('The project directory is', project_directory)

    time_stamp = get_current_time_stamp(TIME_STAMP_FORMAT_YYYYMMDDHHMMSS)
    # file_path = os.path.join(project_directory, f'cubic.{time_stamp}.log')
    file_path = os.path.join(project_directory, LOG_FILE_NAME % time_stamp)
    # logger.log_value('The constructed log file path is', file_path)

    return file_path


def construct_application_configuration_file_path(user_home):
    """
    Construct the full file path for the "config.conf" file. This file
    is located in the Cubic project directory.

    Arguments:
    user_home : str
        The user's home directory.

    Returns:
    file_path : str
        The full file path for the config.conf file.
    """

    # logger.log_label('Construct the application configuration file path')
    # logger.log_value('The user home directory is', user_home)

    file_path = os.path.join(user_home, '.config', 'cubic', 'cubic.conf')
    # logger.log_value('The constructed application configuration file path is', file_path)

    return file_path


def construct_project_configuration_file_path(project_directory):
    """
    Construct the full file path for the "config.conf" file. This file
    is located in the Cubic project directory.

    Arguments:
    project_directory : str
        The project directory.

    Returns:
    file_path : str
        The full file path for the config.conf file.
    """

    # logger.log_label('Construct the project configuration file path')
    # logger.log_value('The project directory is', project_directory)

    file_path = os.path.join(project_directory, 'cubic.conf')
    # logger.log_value('The constructed project configuration file path is', file_path)

    return file_path


def construct_original_iso_mount_point(project_directory):
    """
    Construct the full file path for the mount point for the original
    ISO. This file is located in the Cubic project directory.

    Arguments:
    project_directory : str
        The project directory.

    Returns:
    original_iso_mount_point : str
        The full file path for the original ISO mount point.
    """

    # logger.log_label('Construct the original disk image mount point')
    # logger.log_value('The project directory is', project_directory)

    original_iso_mount_point = os.path.join(project_directory, ISO_MOUNT_POINT)
    # logger.log_value('The constructed original disk image mount point is', original_iso_mount_point)

    return original_iso_mount_point


def construct_custom_root_directory(project_directory):
    """
    Construct the full file path for the custom root directory. This
    directory is located in the Cubic project directory.

    Arguments:
    project_directory : str
        The project directory.

    Returns:
    custom_root_directory : str
        The full file path for the custom root directory.
    """

    # logger.log_label('Construct the custom root directory')
    # logger.log_value('The project directory is', project_directory)

    custom_root_directory = os.path.join(project_directory, CUSTOM_ROOT_DIRECTORY)
    # logger.log_value('The constructed custom root directory is', custom_root_directory)

    return custom_root_directory


def construct_custom_disk_directory(project_directory):
    """
    Construct the full file path for the custom disk directory. This
    directory is located in the Cubic project directory.

    Arguments:
    project_directory : str
        The project directory.

    Returns:
    custom_disk_directory : str
        The full file path for the custom disk directory.
    """

    # logger.log_label('Construct the custom disk directory')
    # logger.log_value('The project directory is', project_directory)

    custom_disk_directory = os.path.join(project_directory, CUSTOM_DISK_DIRECTORY)
    # logger.log_value('The constructed custom disk directory is', custom_disk_directory)

    return custom_disk_directory


def construct_custom_iso_file_name(original_iso_file_name, custom_iso_version_number):
    """
    Construct the custom ISO file name using the original ISO file name
    and custom ISO version_number.

    Arguments:
    original_iso_file_name : str
        The original ISO file name.
    custom_iso_version_number : str
        The custom ISO version number.

    Returns:
    custom_iso_file_name : str
        The custom ISO file name with a ".iso" extension.
    """

    logger.log_label('Construct the custom disk image file name')
    logger.log_value('The original disk image file name is', original_iso_file_name)
    logger.log_value('The custom disk image version number is', custom_iso_version_number)

    if original_iso_file_name:

        # original_iso_file_name = re.sub('\.iso$', '',
        #                                      original_iso_file_name)
        original_iso_file_name = original_iso_file_name[:-4]

        # original_iso_file_name ◀ (text_a)(version)(text_b)
        pattern = r'(^.*)(\d{4}\.\d{2}\.\d{2})(.*$)'
        match = re.search(pattern, original_iso_file_name)
        if match:
            # Version exists in original_iso_file_name.
            text_a = match.group(1)
            version = match.group(2)
            text_b = match.group(3)
            logger.log_value('text a', text_a)
            logger.log_value('version', version)
            logger.log_value('text b', text_b)
            # text_a ◀ (text_c)(release)(point_release)(text_d)
            pattern = r'(^.*?)(\d{2}\.\d{1,2})(\.\d{1,2}){0,1}(.*$)'
            match = re.search(pattern, text_a)
            if match:
                # Release exists in text_a.
                text_c = match.group(1)
                release = match.group(2)
                point_release = match.group(3)
                text_d = match.group(4)
                logger.log_value('text c', text_c)
                logger.log_value('release', release)
                logger.log_value('point release', point_release)
                logger.log_value('text d', text_d)
                if not point_release:
                    point_release = '.0'
                    logger.log_value('new point_release', point_release)
                    text_a = f'{text_c}{release}{point_release}{text_d}'
                    logger.log_value('new text a', text_a)
            else:
                # text_b ◀ (text_c)(release)(point_release)(text_d)
                match = re.search(pattern, text_b)
                if match:
                    # Release exists in text_b.
                    text_c = match.group(1)
                    release = match.group(2)
                    point_release = match.group(3)
                    text_d = match.group(4)
                    logger.log_value('text c', text_c)
                    logger.log_value('release', release)
                    logger.log_value('point release', point_release)
                    logger.log_value('text d', text_d)
                    if not point_release:
                        point_release = '.0'
                        logger.log_value('new point_release', point_release)
                        text_b = f'{text_c}{release}{point_release}{text_d}'
                        logger.log_value('new text b', text_b)
            custom_iso_file_name = f'{text_a}{custom_iso_version_number}{text_b}.iso'
        else:
            # original_volume_id ◀ (text_a)(release)(point_release)(text_b)
            pattern = r'(^.*?)(\d{2}\.\d{1,2})(\.\d{1,2}){0,1}(.*$)'
            match = re.search(pattern, original_iso_file_name)
            if match:
                # Release exists in original_iso_file_name.
                text_a = match.group(1)
                release = match.group(2)
                point_release = match.group(3)
                text_b = match.group(4)
                logger.log_value('text a', text_a)
                logger.log_value('release', release)
                logger.log_value('point release', point_release)
                logger.log_value('text b', text_b)
                if not point_release:
                    point_release = '.0'
                    logger.log_value('new point_release', point_release)
                custom_iso_file_name = f'{text_a}{release}{point_release}-{custom_iso_version_number}{text_b}.iso'
            else:
                custom_iso_file_name = f'{original_iso_file_name}-{custom_iso_version_number}.iso'
        # logger.log_value('The constructed custom disk image file name is', custom_iso_file_name)
    else:
        custom_iso_file_name = None
        # logger.log_value('The constructed custom disk image file name is', custom_iso_file_name)

    return custom_iso_file_name


def construct_custom_iso_volume_id(original_iso_volume_id, custom_iso_version_number):
    """
    Construct the custom ISO volume id using the original ISO volume id
    and custom ISO version number.

    Arguments:
    original_iso_volume_id : str
        The original ISO file name.
    custom_iso_version_number : str
        The custom ISO version number.

    Returns:
    custom_iso_volume_id : str
        The custom ISO volume id.
    """

    logger.log_label('Construct the custom disk image volume id')
    logger.log_value('The original disk image volume id is', original_iso_volume_id)
    logger.log_value('The custom disk image version number is', custom_iso_version_number)

    if original_iso_volume_id:
        # original_iso_volume_id ◀ (text_a)(version)(text_b)
        pattern = r'(^.*)(\d{4}\.\d{2}\.\d{2})(.*$)'
        match = re.search(pattern, original_iso_volume_id)
        if match:
            # Version exists in original_iso_volume_id.
            text_a = match.group(1)
            version = match.group(2)
            text_b = match.group(3)
            logger.log_value('text a', text_a)
            logger.log_value('version', version)
            logger.log_value('text b', text_b)
            # text_a ◀ (text_c)(release)(point_release)(text_d)
            pattern = r'(^.*?)(\d{2}\.\d{1,2})(\.\d{1,2}){0,1}(.*$)'
            match = re.search(pattern, text_a)
            if match:
                # Release exists in text_a.
                text_c = match.group(1)
                release = match.group(2)
                point_release = match.group(3)
                text_d = match.group(4)
                logger.log_value('text c', text_c)
                logger.log_value('release', release)
                logger.log_value('point release', point_release)
                logger.log_value('text d', text_d)
                if not point_release:
                    point_release = '.0'
                    logger.log_value('new point_release', point_release)
                    text_a = f'{text_c}{release}{point_release}{text_d}'
                    logger.log_value('new text a', text_a)
            else:
                # text_b ◀ (text_c)(release)(point_release)(text_d)
                match = re.search(pattern, text_b)
                if match:
                    # Release exists in text_b.
                    text_c = match.group(1)
                    release = match.group(2)
                    point_release = match.group(3)
                    text_d = match.group(4)
                    logger.log_value('text c', text_c)
                    logger.log_value('release', release)
                    logger.log_value('point release', point_release)
                    logger.log_value('text d', text_d)
                    if not point_release:
                        point_release = '.0'
                        logger.log_value('new point_release', point_release)
                        text_b = f'{text_c}{release}{point_release}{text_d}'
                        logger.log_value('new text b', text_b)
            custom_iso_volume_id = f'{text_a}{custom_iso_version_number}{text_b}'
        else:
            # original_volume_id ◀ (text_a)(release)(point_release)(text_b)
            pattern = r'(^.*?)(\d{2}\.\d{1,2})(\.\d{1,2}){0,1}(.*$)'
            match = re.search(pattern, original_iso_volume_id)
            if match:
                # Release exists in original_iso_volume_id.
                text_a = match.group(1)
                release = match.group(2)
                point_release = match.group(3)
                text_b = match.group(4)
                logger.log_value('text a', text_a)
                logger.log_value('release', release)
                logger.log_value('point release', point_release)
                logger.log_value('text b', text_b)
                if not point_release:
                    point_release = '.0'
                    logger.log_value('new point_release', point_release)
                custom_iso_volume_id = f'{text_a}{release}{point_release} {custom_iso_version_number}{text_b}'
            else:
                custom_iso_volume_id = f'{original_iso_volume_id} {custom_iso_version_number}'
        # If volume id is longer than 32 characters, and there is a space
        # within the last five positions, trim the space and subsequent
        # characters.
        if len(custom_iso_volume_id) > 32:
            try:
                index_of_space = custom_iso_volume_id.rindex(' ', 27, 32)
                logger.log_value('The custom ISO volume id is too long', f'Trim all characters after the space at index {index_of_space}')
            except ValueError as exception:
                custom_iso_volume_id = custom_iso_volume_id[:32]
                logger.log_value('The custom ISO volume id is too long', 'Trim to 32 characters')
            else:
                custom_iso_volume_id = custom_iso_volume_id[:index_of_space]
        # logger.log_value('The constructed custom disk image volume id is', custom_iso_volume_id)
    else:
        custom_iso_volume_id = None
        # logger.log_value('The constructed custom disk image volume id is', custom_iso_volume_id)

    return custom_iso_volume_id


def construct_custom_iso_release_name(original_iso_release_name):
    """
    Construct the custom ISO release name using the original ISO release
    name.

    Arguments:
    original_iso_release_name : str
        The original ISO release name.

    Returns:
    custom_iso_release_name : str
        The custom ISO release name.
    """

    # logger.log_label('Construct the custom disk image release name')
    # logger.log_value('The original disk image release name is', original_iso_release_name)

    try:
        # Remove the prefix "Custom" if it exists.
        original_iso_release_name = re.sub(r'^Custom\s*', '', original_iso_release_name)
        custom_iso_release_name = f'Custom {original_iso_release_name}'
    except Exception as exception:
        logger.log_value('Encountered exception while creating custom disk image release name', exception)
        custom_iso_release_name = ''
    # logger.log_value('The constructed custom disk image release name is', custom_iso_release_name)

    return custom_iso_release_name


def construct_custom_iso_disk_name(custom_iso_volume_id, custom_iso_release_name):
    """
    Construct the custom ISO release name using the original ISO release
    name.

    Arguments:
    custom_iso_volume_id : str
        The custom ISO volume id.
    custom_iso_release_name : str
        The custom ISO release name.

    Returns:
    custom_iso_disk_name : str
        The custom ISO disk name.
    """

    # logger.log_label('Construct custom disk image disk name')
    # logger.log_value('The custom disk image volume id is', custom_iso_volume_id)
    # logger.log_value('The custom disk image release name is', custom_iso_release_name)

    if custom_iso_volume_id and custom_iso_release_name:
        custom_iso_disk_name = f'{custom_iso_volume_id} "{custom_iso_release_name}"'
    elif custom_iso_volume_id:
        custom_iso_disk_name = f'{custom_iso_volume_id}'
    elif custom_iso_release_name:
        custom_iso_disk_name = f'"{custom_iso_release_name}"'
    else:
        custom_iso_disk_name = ''

    # logger.log_value('The constructed custom disk image disk name is', custom_iso_disk_name)

    return custom_iso_disk_name


def construct_custom_iso_checksum_file_name(custom_iso_file_name):
    """
    Construct the custom ISO checksum file name using the custom ISO
    file name.

    Arguments:

    custom_iso_file_name : str
        The custom ISO file name.

    Returns:
    custom_iso_checksum_file_name : str
        The custom ISO checksum file name  with a ".md5" extension.
    """

    # logger.log_label('Construct the custom disk image checksum file name')
    # logger.log_value('The custom disk image file name is', custom_iso_file_name)

    try:
        # file_name_root = splitext(custom_iso_file_name)[0]
        # file_name_root = re.search(r'(.*?)\.iso*', custom_iso_file_name).group(1)
        # file_name_root = re.search(r'(.*?)(?:(?:\.iso)*)$', custom_iso_file_name).group(1)
        custom_iso_checksum_file_name = f'{custom_iso_file_name[:-4]}.md5'
    except Exception as exception:
        logger.log_value('Encountered exception while creating custom disk image checksum file name', exception)
        custom_iso_checksum_file_name = 'custom.md5'

    # logger.log_value('The constructed custom disk image checksum file name is', custom_iso_checksum_file_name)

    return custom_iso_checksum_file_name


def encode(t):
    """
    Convert text into a hex string.

    Arguments:

    t : str
        The text.

    Returns:
    h : str
        The hex string.
    """

    b = t.encode('utf-8')
    z = zlib.compress(b)
    h = z.hex().upper()

    return h


def decode(h):
    """
    Convert a hex string into text.

    Arguments:
    h : str
        The hex string.

    Returns:
    t : str
        The text.
    """

    z = bytes.fromhex(h)
    b = zlib.decompress(z)
    t = b.decode('utf-8')

    return t


def encode_object(o):
    """
    Convert an object into a hex string.

    Arguments:

    o : object
        The object.

    Returns:
    h : str
        The hex string.
    """
    b = pickle.dumps(o)
    z = zlib.compress(b)
    h = z.hex().upper()

    return h


def decode_object(h):
    """
    Convert a hex string into an object.

    Arguments:
    h : str
        The hex string.

    Returns:
    o : object
        The object.
    """

    z = bytes.fromhex(h)
    b = zlib.decompress(z)
    o = pickle.loads(b)

    return o
