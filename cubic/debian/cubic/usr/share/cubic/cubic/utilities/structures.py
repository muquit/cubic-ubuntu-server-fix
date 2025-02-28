#!/usr/bin/python3

########################################################################
#                                                                      #
# structures.py                                                        #
#                                                                      #
# Copyright (C) 2020, 2024 PJ Singh <psingh.cubic@gmail.com>           #
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

# https://docs.python.org/3/reference/datamodel.html

########################################################################
# Imports
########################################################################

from cubic.utilities import logger

########################################################################
# Global Variables & Constants
########################################################################

# N/A

########################################################################
# Fields Class
########################################################################


class Fields:
    """
    Store multiple key value pairs, allow assignment of values to keys
    using the "=" operator, and optionally print a log output whenever
    a new value is set.

    The log output has the format:
    "Set <fields name> <key key>... <value>".

    Logging can optionally be turned off for each assignment operation
    by specifying the value as a tuple containing "value, False".
    Logging is turned on by default, so specifying "value, True" is
    unnecessary.

    Each time a value is assigned, it will be logged if:
    • Logging is not turned off for the assignment
    • The key and value are new
    • The value for an existing key has changed

    Each time a value is assigned, it will not be logged if:
    • Logging is turned off for the assignment
    • The value for an existing key has not changed

    Notes:
    • The name of the Fields is stored with all underscore "_"
      characters replaced with space " " characters and leading and
      trailing spaces removed to expedite printing the log in a
      readable format.
    • Keys are displayed with all underscore "_" characters replaced
      with space " " characters and leading and trailing spaces removed
      to facilitate printing the log in a readable format.
    • Keys can be any accepted Python variable name, with the
      restriction that the word "name" may not be used.
    • Values can be any Python type (str, int, bool, list, etc).
    • If the value is a string, all underscore "_" characters will be
      replaced with space " " characters and leading and trailing spaces
      will be removed to facilitate printing the log in a readable
      format.
    • If the value is a tuple, the second item must be False to turn off
      logging.

    Examples:

    car_parts = Fields('sports_car')
    # The name of the Fields, "sports car", will be used in all output

    car_parts.name
    # Output: sports car

    car_parts.engine = '  V6  '
    # Output: Set sports car engine................. V6

    car_parts.engine
    Output: V6

    car_parts.spare_tire = None
    # Output: Set sports car spare tire............. Empty

    car_parts.spare_tire
    # Output: None

    car_parts.has_anti_lock_breaks = True
    # Output: Set sports car has anti lock breaks... True

    car_parts.has_anti_lock_breaks
    # Output: True

    car_parts.has_cd_player = False
    # Output: Set sports car has cd player.......... False

    car_parts.has_cd_player
    # Output: False

    car_parts.number_of_seats = 2
    # Output: Set sports car number_of_seats........ 2

    car_parts.number_of_seats
    # Output: 2

    car_parts.secret_agent = 'James Bond', False
    # No output, because logging was turned off for this assignment

    car_parts.secret_agent
    # Output: James Bond
    """

    def __init__(self, name):
        """
        Create a new instance of Fields with the specified name.

        Arguments:
        self : Fields
            The Fields class.
        name : str
            The name of the new Fields. All underscore "_" characters
            will be replaced with space " " characters and leading and
            trailing spaces will be removed to facilitate printing the
            log in a readable format.

        Returns:
        : Fields
            A new instance of Fields with the specified name.
        """

        super().__setattr__('name', name.replace('_', ' ').strip())

    def __setattr__(self, key, value):
        """
        Override the assignment operation to optionally print a log
        output whenever a new value is set.

        The log output has the format:
        "Set <fields name> <key>... <value>".

        Arguments:
        key : str
            The name of the variable being set; can be any accepted
            Python variable name, with the restriction that the word
            "name" may not be used. The key will be displayed with all
            underscore "_" characters replaced with space " " characters
            and leading and trailing spaces removed.

        value : object or tuple
            The value to be set; can be any Python type (str, int, bool,
            list, etc). If the value is a string, all underscore "_"
            characters will be replaced with space " " characters and
            leading and trailing spaces will be removed. If the value is
            a tuple, the second item must be False to turn off logging.
        """

        # Check if an additional parameter was supplied, and set is_log.
        if isinstance(value, tuple):
            value, is_log = value
        else:
            is_log = True
        if isinstance(value, str):
            value = str(value).strip()
        if value is None:
            # Check if value is None to retain boolean False values.
            # (Do not use "if not value:").
            value = ''
        if not hasattr(self, key):
            if is_log:
                display_key = key.replace('_', ' ').strip()
                logger.log_value(f'Set {self.name} {display_key}', value)
            super().__setattr__(key, value)
        elif self.__getattribute__(key) != value:
            if is_log:
                display_key = key.replace('_', ' ').strip()
                logger.log_value(f'Set {self.name} {display_key}', value)
            super().__setattr__(key, value)

    def __repr__(self):
        """
        Get the string representation of the underlying __dict__.

        Returns:
        : str
            The the string representation of the underlying __dict__.
        """

        return str(self.__dict__)


########################################################################
# Attributes Class
########################################################################


class Attributes:
    """
    A structure that allows attributes to have multiple unique values
    which can be designated as valid or invalid. Accessing an attribute
    returns a list of valid values for the attribute. Attributes can be
    thought of as a dictionary of dictionaries, where attributes are
    keys in the top level dictionary, and the possible values for each
    attribute are keys in second level dictionaries.

    Consider the following example for "structure" with two attributes
    "attribute_a" and "attribute_b". "attribute_a" can have three
    possible values, "a_value_1", "a_value_2", and "a_value_3".
    "attribute_b" can have three possible values, "b_value_1",
    "b_value_2", and "b_value_3". For "attribute_a", "a_value_1" and
    "a_value_3" are valid. For "attribute_b", "b_value_2" is the only
    valid value.

    structure
    ├── attribute_a
    │   ├── a_value_1, True
    │   ├── a_value_2, False
    │   └── a_value_3, True
    └── attribute_b
        ├── b_value_1, False
        ├── b_value_2, True
        └── b_value_3, False

    Create an instance of Attributes named "structure".

        from structures import Attributes
        structure = Attributes('structure')

    Set valid values as True; set invalid values as False.

        structure.attribute_a = 'a_value_1', True
        > Set structure attribute a................... a_value_1 (True)
        structure.attribute_a = 'a_value_2', False
        > Set structure attribute a................... a_value_2 (False)
        structure.attribute_a = 'a_value_3', True
        > Set structure attribute a................... a_value_3 (True)

        structure.attribute_b = 'b_value_1', False
        > Set structure attribute b................... b_value_1 (False)
        structure.attribute_b = 'b_value_2', True
        > Set structure attribute b................... b_value_2 (True)
        structure.attribute_b = 'b_value_3', False
        > Set structure attribute b................... b_value_3 (False)

    Print the string representation of "structure".
        structure
        > {'name': 'structure', 'attribute_a': {'a_value_1': True, 'a_value_2': False, 'a_value_3': True}, 'attribute_b': {'b_value_1': False, 'b_value_2': True, 'b_value_3': False}}

    Only a_value_1 and a_value_3, are valid for attribute_a, so
    accessing "attribute_a" will only list these values.

        structure.attribute_a
        > ['a_value_1', 'a_value_3']

    Only b_value_2 is valid for attribute_b, so accessing "attribute_b"
    will only list this values.

        structure.attribute_b
        > ['b_value_2']

    Get a list of all attributes.

        structure.attributes()
        > ['attribute_a', 'attribute_b']

    Get a dict of all attributes with their values.

        structure.items()
        > {'attribute_a': {'a_value_1': True, 'a_value_2': False, 'a_value_3': True}, 'attribute_b': {'b_value_1': False, 'b_value_2': True, 'b_value_3': False}}

    Get a dict of all values for an attribute.

        structure.items('attribute_a')
        > {'a_value_1': True, 'a_value_2': False, 'a_value_3': True}

    Get a list of all values for an attribute.

        structure.values('attribute_a')
        > ['a_value_1', 'a_value_2', 'a_value_3']

    Here is the internal dictionary for the "structure" object.
        > structure.__dict__
        {'name': 'structure', 'attribute_a': {'a_value_1': True, 'a_value_2': False, 'a_value_3': True}, 'attribute_b': {'b_value_1': False, 'b_value_2': True, 'b_value_3': False}}
    """

    def __init__(self, name):
        """
        Create a new instance of Attributes with the specified name.

        Arguments:
        self : Attributes
            The Attributes class.
        name : str
            The name of the new Attributes structure. All underscore "_"
            characters will be replaced with space " " characters and
            leading and trailing spaces will be removed to facilitate
            printing the log in a readable format.

        Returns:
        : Attributes
            A new instance of Attributes with the specified name.
        """

        super().__setattr__('name', name.replace('_', ' ').strip())

    def __getattribute__(self, attribute):
        """
        Override the get operation to return:
        1) The last valid value in the list of valid values for the
           specified attribute
        2) All valid values for the specified attribute, if the
           attribute name is suffixed with "_as_list".

        Arguments:
        attribute : str
            The name of the attribute.

        Returns:
        : list(str)
            A list containing valid keys for the specified attribute, or
            an empty list if there are no valid keys.
        """

        as_list = attribute.endswith('_as_list')
        # The function str.removesuffix() is only available in Python 3.9.
        # See: https://docs.python.org/3/library/stdtypes.html#str.removesuffix
        # attribute = attribute.removesuffix('_as_list')
        if as_list: attribute = attribute[:-8]

        if attribute.startswith('_'):
            return super().__getattribute__(attribute)
        elif callable(super().__getattribute__(attribute)):
            return super().__getattribute__(attribute)
        elif isinstance(self.__dict__[attribute], dict):
            if as_list:
                items = self.__dict__[attribute].items()
                return [value for value, is_valid in items if is_valid]
            else:
                items = self.__dict__[attribute].items()
                values = [value for value, is_valid in items if is_valid]
                return values[-1] if values else ''
        else:
            return self.__dict__[attribute]

    def __setattr__(self, attribute, value):
        """
        Override the assignment operation. For the specified attribute,
        add or update the specified value as valid or invalid. The
        specified attribute may store multiple unique values. Optionally
        print a log output whenever a value is set.

        The log output has the format:
        "Set <structure name> <attribute>... <key>... <value>".

        Arguments:
        attribute : str
            The name of the attribute being set. The attribute name can
            be any accepted Python variable name, with the following
            restrictions:
            - "name" is reserved and may not be used
            - may not start with an underscore "_" character
            - may not end in "_as_list". See __getattribute__().
            Leading and trailing spaces will be removed from the
            attribute name, and the attribute will be logged with all
            underscore "_" characters replaced with space " "
            characters.

        value : tuple
            A tuple containing two or three items:
            (value, is_valid, is_log)
            1) value:
            The first item is the name of a possible value. If value is
            a string, leading and trailing spaces will be removed.
            2) is_valid:
            The second item indicates whether or not the value is valid.
            It must evaluate to True or False.
            3) is_log:
            The third item is optional. It turns off logging if False.
            It is True by default (i.e. logging is on).
        """

        if value == None:
            is_log = True
            is_valid = False
            value = None
        elif len(value) == 2 and value[0] == None:
            is_log = value[1]
            is_valid = False
            value = value[0]  # None
        elif len(value) == 2 and value[0] != None:
            is_log = True
            is_valid = value[1]
            value = value[0]
        elif len(value) == 3:
            is_log = value[2]
            is_valid = value[1]
            value = value[0]
        else:
            # TODO: Throw exception.
            pass

        if isinstance(value, str):
            value = str(value).strip()
        if isinstance(is_valid, str):
            is_valid = str(is_valid).strip()

        if attribute not in self.__dict__:
            self.__dict__[attribute] = {}

        display_attribute = str(attribute).replace('_', ' ')
        if not value:
            # If no value was specified, set all values to False.
            # For example structure.attribute_a = None is equivalent to:
            # - structure.attribute_a = a_value_1, False
            # - structure.attribute_a = a_value_2, False
            # - structure.attribute_a = a_value_3, False
            values = self.__dict__[attribute].keys()
            for value in values:
                if is_log:
                    # print(f'Set {self.name} {display_attribute}...\t {value} ({is_valid})')
                    # logger.log_value(f'Set {self.name} {display_attribute}', f'{value} ({is_valid})')
                    logger.log_value(f'Set {display_attribute}', f'{value} ({is_valid})')
                self.__dict__[attribute][value] = is_valid
        else:
            # If the value was specified, set it accordingly.
            if is_log:
                # print(f'Set {self.name} {display_attribute}...\t {value} ({is_valid})')
                # logger.log_value(f'Set {self.name} {display_attribute}', f'{value} ({is_valid})')
                logger.log_value(f'Set {display_attribute}', f'{value} ({is_valid})')
            self.__dict__[attribute][value] = is_valid

    def set(self, attribute, *value):
        """
        Store multiple values for the specified attribute. Optionally
        print a log output whenever a value is set.
        """

        self.__setattr__(attribute, value)

    def set_attribute_values(self, attribute, values, is_valid=True, is_log=True):
        """
        Store multiple values for the specified attribute. Optionally
        print a log output whenever a value is set.
        """
        display_attribute = str(attribute).replace('_', ' ')
        for value in values:
            if is_log:
                # print(f'Set {self.name} {display_attribute}...\t {value} ({is_valid})')
                # logger.log_value(f'Set {self.name} {display_attribute}', f'{value} ({is_valid})')
                logger.log_value(f'Set {display_attribute}', f'{value} ({is_valid})')
            self.__dict__[attribute][value] = is_valid

    def attributes(self):
        """
        Get a list of all attributes.

        Arguments:
        self : Attributes
            The Attributes class.

        Returns:
        : list(str)
            A new list of attributes.
        """

        return list(self.__dict__)[1:]

    def values(self, attribute, is_valid_only=False):
        """
        Get a list of values for the specified attribute. If
        is_valid_only is True, only return values that are valid,
        otherwise return all values (valid and invalid).

        Arguments:
        self : Attributes
            The Attributes class.
        attribute : str
            The name of the attribute.
        is_valid_only : bool
            Only return values that are valid.
        
        Returns:
        : list(str)
            A new list of values.
        """
        if is_valid_only:
            items = self.__dict__[attribute].items()
            return [value for value, is_valid in items if is_valid]
        else:
            return list(self.__dict__[attribute])

    def dictionary(self, attribute=None):
        """
        Get a dict of all possible values for the attribute, if
        specified. Get a dict of all attributes and all possible values,
        if an attribute is not specified.

        Arguments:
        self : Attributes
            The Attributes class.
        attribute : str
            The optional name of an attribute. If an attribute is not
            specified, then the top level dictionary will be returned.

        Returns:
        : dict
            A new dict of keys and values.
        """

        if not attribute:
            dictionary = dict(self.__dict__)
            dictionary.pop('name')
            return dictionary
        else:
            return dict(self.__dict__[attribute])

    def reset(self, is_valid=False):
        """
        Reset all existing attributes as invalid (False).

        Arguments:
        self : Attributes
            The Attributes class.
        is_valid : bool (or any type interpretable as True or False)
            Optional value to reset all values to. The default is False.
        """
        '''
        for attribute in self.attributes():
            for value in self.values(attribute):
                self.__dict__[attribute][value] = False
        '''

        for attribute, values in self.__dict__.items():
            if attribute != 'name':
                for value in values.keys():
                    values[value] = is_valid

    def print(self):
        """
        Print the attributes in a readable format.
        """

        for attribute, values in self.__dict__.items():
            if attribute == 'name':
                print(f'  {attribute}: {values}')
            else:
                print(f'  • {attribute}:')
                for value, is_valid in values.items():
                    print(f'        {value} ({is_valid})')

    def __repr__(self):
        """
        Get the string representation of the underlying __dict__.

        Returns:
        : str
            The the string representation of the underlying __dict__.
        """

        return str(self.__dict__)


########################################################################
# Iso Field Class
########################################################################


class IsoField:
    """
    If appending a new field in IsoFields, update both references to the
    last field in the __setattr__() method. This ensures the validators
    are not invoked during the __init__() method. Currently the last
    field is "update_os_release". When instantiating IsoField,
    *never* use "name" as a key.
    """

    def __init__(self, value, iso_fields):
        """
        Create a new IsoField object.

        Arguments:
        self : IsoField
            The IsoField class.
        value : str
            Either a string that represents the name of the new
            IsoField, or an IsoField object that will be copied into the
            new IsoField object. If value is a string, the new IsoField
            object's values will be initialized to default values. If
            value is an existing IsoField object, then the new object
            will have the same name as the original object, and its
            values will be the same as the values of the original
            object.
        iso_fields : IsoFields
            The IsoFields container for the new IsoField.
        """

        # Ensure self.__dict__ contains all required keys. This
        # simplifies, the __setattr__() implementation because checking
        # hasattr(self, key) becomes unnecessary when adding new keys.
        # Note that self.__setattr__() will not be invoked below, so
        # values will not be converted to displayable format when they
        # are stored. Python 3.7+ guarantees that dict will sort keys
        # using insertion order, so this is also useful for the
        # __repr__() method.
        super().__setattr__('name', None)
        super().__setattr__('value', None)
        super().__setattr__('is_valid', None)
        super().__setattr__('status', None)
        super().__setattr__('message', None)
        super().__setattr__('validator', None)
        super().__setattr__('iso_fields', None)

        # Ensure that self.__setattr__() is called, so that the values
        # are converted to displayable format, as necessary, before they
        # are stored.
        if isinstance(value, IsoField):
            # self.name = value.name
            super().__setattr__('name', value.name)
            # The iso_fields reference must be set prior to setting the
            # value or the validator. This is because the validate()
            # callback function, which is executed each time a new value
            # is set or when a new validator is set, requires this
            # parameter as an argument.
            self.iso_fields = iso_fields, False  # Reference to container object.
            self.value = value.value, False  # Converted to a string.
            self.is_valid = value.is_valid, False  # Converted to a boolean.
            self.status = value.status, False  # Converted to an integer.
            self.message = value.message, False  # Converted to a string.
            self.validator = value.validator, False
        elif isinstance(value, str):
            name = value.replace('_', ' ')
            # self.name = name
            super().__setattr__('name', name)
            self.iso_fields = iso_fields, False  # Reference to container object.
            self.value = None, False  # Converted to an empty string.
            self.is_valid = None, False  # Converted to False.
            self.status = None, False  # Converted to a 0.
            self.message = None, False  # Converted to an empty string.
            self.validator = None, False
        else:
            raise TypeError('Argument must be a string or IsoField')

    def __eq__(self, field):
        """
        Compare this object's value with another object's value.
        """

        if field:
            return self.value == field.value
        else:
            return False

    def __setattr__(self, key, value):
        """
        Set iso_fields, if they have changed, converting to displayable
        format, as necessary, before storing:
        • value is stored as a string or empty string if None
        • is_valid is stored as a boolean or False if None
        • status is stored as an integer or O if None
        • message is stored as a string or empty string if None
        • other iso_fields are stored as-is
        """

        # Check if an additional parameter was supplied, and set is_log.
        if isinstance(value, tuple):
            value, is_log = value
        else:
            is_log = True

        if key == 'name':
            if value:
                value = str(value).strip()
            if not value:
                value = ''
            if self.name != value:
                # if is_log:
                #     logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                super().__setattr__(key, value)
        elif key == 'value':
            if value:
                value = str(value).strip()
            if value is None:
                # Check if value is None to retain boolean False values.
                # (Do not use "if not value:").
                value = ''
            if self.value != value:
                if is_log:
                    logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                super().__setattr__(key, value)
                # If a new value was set, validate it.
                # In order to ensure that the validator is not invoked
                # during IsoField.__init__() using an incomplete
                # IsoFields object, check if the last value,
                # update_os_release, has been assigned.
                if self.validator and self.iso_fields.update_os_release:
                    # If a validator is available, validate the fields.
                    is_valid, status, message = self.validator(self.iso_fields)
                    self.is_valid = is_valid
                    self.status = status
                    self.message = message
        elif key == 'is_valid':
            value = bool(value)
            if self.is_valid != value:
                if is_log:
                    logger.log_value(f'Is {self.iso_fields.name} {self.name} valid?', value)
                super().__setattr__(key, value)
        elif key == 'status':
            value = 0 if not value else int(value)
            if self.status != value:
                # if is_log:
                #     logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                super().__setattr__(key, value)
        elif key == 'message':
            if value:
                value = str(value).strip()
            if not value:
                value = ''
            if self.message != value:
                # if is_log:
                #     logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                super().__setattr__(key, value)
        elif key == 'validator':
            if self.validator != value:
                super().__setattr__(key, value)
                # If a new validator was set, validate the value.
                # In order to ensure that the validator is not invoked
                # during IsoField.__init__() using an incomplete
                # IsoFields object, check if the last value,
                # update_os_release, has been assigned.
                if self.validator and self.iso_fields.update_os_release:
                    # if is_log:
                    #     logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                    is_valid, status, message = self.validator(self.iso_fields)
                    self.is_valid = is_valid
                    self.status = status
                    self.message = message
        elif key == 'iso_fields':
            if self.iso_fields != value:
                # if is_log:
                #     logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                super().__setattr__(key, value)
        else:
            # TODO: Consider ignoring or raising an exception.
            if self.key != value:
                if is_log:
                    logger.log_value(f'Set {self.iso_fields.name} {self.name} {key}', value)
                super().__setattr__(key, value)

    def __repr__(self):
        """
        Return the string representation of the underlying __dict__.
        """

        return str(self.__dict__)


########################################################################
# Iso Fields Class
########################################################################


class IsoFields:
    """
    When instantiating IsoFields, *never* use "name" as a key.
    """

    # TODO: Copy the name of the IsoField, if one is supplied.
    #       Use value instead of name and iso_fields. Then check value
    #       using isinstance(value, str).
    def __init__(self, name, iso_fields=None):

        super().__setattr__('name', name.replace('_', ' ').strip())

        if iso_fields:
            super().__setattr__('iso_version_number', IsoField(iso_fields.iso_version_number, self))
            super().__setattr__('iso_file_name', IsoField(iso_fields.iso_file_name, self))
            super().__setattr__('iso_directory', IsoField(iso_fields.iso_directory, self))
            super().__setattr__('iso_volume_id', IsoField(iso_fields.iso_volume_id, self))
            super().__setattr__('iso_release_name', IsoField(iso_fields.iso_release_name, self))
            super().__setattr__('iso_disk_name', IsoField(iso_fields.iso_disk_name, self))
            super().__setattr__('iso_release_notes_url', IsoField(iso_fields.iso_release_notes_url, self))
            super().__setattr__('update_os_release', IsoField(iso_fields.update_os_release, self))
        else:
            super().__setattr__('iso_version_number', IsoField('iso_version_number', self))
            super().__setattr__('iso_file_name', IsoField('iso_file_name', self))
            super().__setattr__('iso_directory', IsoField('iso_directory', self))
            super().__setattr__('iso_volume_id', IsoField('iso_volume_id', self))
            super().__setattr__('iso_release_name', IsoField('iso_release_name', self))
            super().__setattr__('iso_disk_name', IsoField('iso_disk_name', self))
            super().__setattr__('iso_release_notes_url', IsoField('iso_release_notes_url', self))
            super().__setattr__('update_os_release', IsoField('update_os_release', self))

    def __eq__(self, iso_fields):
        """
        Return True if the value property of each IsoField of this
        object is equal to the value property of each corresponding
        IsoField of iso_fields. Otherwise, return False.
        • iso_version_number.value
        • iso_file_name.value
        • iso_directory.value
        • iso_volume_id.value
        • iso_release_name.value
        • iso_disk_name.value
        • iso_release_notes_url.value
        • update_os_release
        """

        return (
            iso_fields                                                               \
            and self.iso_version_number == iso_fields.iso_version_number             \
            and self.iso_file_name == iso_fields.iso_file_name                       \
            and self.iso_directory == iso_fields.iso_directory                       \
            and self.iso_volume_id == iso_fields.iso_volume_id                       \
            and self.iso_release_name == iso_fields.iso_release_name                 \
            and self.iso_disk_name == iso_fields.iso_disk_name                       \
            and self.iso_release_notes_url == iso_fields.iso_release_notes_url       \
            and self.update_os_release == iso_fields.update_os_release)

    def __getattr__(self, key):
        """
        Add attribute for is_valid.
        """

        if key == 'is_valid':
            return (
                self.iso_version_number.is_valid          \
                and self.iso_file_name.is_valid           \
                and self.iso_directory.is_valid           \
                and self.iso_volume_id.is_valid           \
                and self.iso_release_name.is_valid        \
                and self.iso_disk_name.is_valid           \
                and self.iso_release_notes_url.is_valid   \
                and self.update_os_release.is_valid)

    def __repr__(self):
        """
        Return the string representation of the internal dictionary.
        """

        return str(self.__dict__)


########################################################################
# Iso Fields History Class
########################################################################


class IsoFieldsHistory:

    def __init__(self):

        # The index of the currently selected item in the history.
        self.selected = -1

        # The history.
        self.history = []

    def reset(self):

        self.history.clear()
        self.selected = -1

    def clear(self, iso_fields):
        """
        Remove all subsequent values after the current value.
        """

        del self.history[self.selected + 1:]

    def insert(self, iso_fields):

        self.selected = self.selected + 1
        del self.history[self.selected:]
        new_iso_fields = IsoFields(iso_fields.name, iso_fields)
        self.history.append(new_iso_fields)

    def get_first(self):

        return self.history[0]

    def get(self, selected):

        return self.history[selected]

    def current(self):

        if self.selected > -1 and self.selected < len(self.history):
            iso_fields = self.history[self.selected]
            new_iso_fields = IsoFields(iso_fields.name, iso_fields)
            return new_iso_fields
        else:
            return None

    def previous(self):

        self.selected = self.selected - 1
        iso_fields = self.history[self.selected]
        new_iso_fields = IsoFields(iso_fields.name, iso_fields)
        return new_iso_fields

    def next(self):

        self.selected = self.selected + 1
        iso_fields = self.history[self.selected]
        new_iso_fields = IsoFields(iso_fields.name, iso_fields)
        return new_iso_fields

    def has_history(self):
        """
        Indicate of there is at least one item in the history.

        Arguments:
        self : IsoFieldsHistory
            This object.

        Returns:
        : bool
            True if there are one or more items in the history to the
            left of the current item. False if there are zero items in
            the history to the left of the current item.
        """
        return len(self.history) > 0

    def has_undo(self):
        """
        Indicate of there is at least one item in the history to the
        "left" of the currently selected item.

        Arguments:
        self : IsoFieldsHistory
            This object.

        Returns:
        : bool
            True if there are one or more items in the history to the
            left of the current item. False if there are zero items in
            the history to the left of the current item.
        """
        return self.selected > 0

    def has_redo(self):

        return self.selected < len(self.history) - 1

    def print_iso_fields(self, iso_fields, message):

        print()
        print('-' * 80)
        print(message)
        print(f'The self.selected index is "{self.selected}"')
        print(f'The id is "{id(iso_fields)}"')
        print('Custom ISO fields are...')
        print(iso_fields)
        print('Custom ISO fields is valid...')
        print(iso_fields.is_valid)
        print('- ' * 40)
        print(f'The custom ISO fields list has  "{len(self.history)}" items.')
        print(f'The custom ISO fields has undo? "{self.has_undo()}"')

        for i, c in enumerate(self.history):
            print(f'The self.selected item is "{i}"')
            print(f'The id is "{id(c)}"')
            print('The ISO fields are...')
            print(c)
            print()
        print('-' * 80)
        print()
