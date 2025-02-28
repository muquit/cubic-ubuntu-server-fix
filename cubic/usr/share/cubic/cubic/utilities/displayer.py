#!/usr/bin/python3

########################################################################
#                                                                      #
# displayer.py                                                         #
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

import gi

gi.require_version('Gdk', '3.0')
gi.require_version('GLib', '2.0')
gi.require_version('Gtk', '3.0')

try:
    gi.require_version('GtkSource', '4')
except ValueError:
    gi.require_version('GtkSource', '3.0')

# The following is necessary to avoid the error: "Gtk-ERROR **: failed
# to add UI: source_view.ui:39:1 Invalid object type 'GtkSourceView'"
from gi.repository.GtkSource import View

from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk
from gi.repository import GtkSource
from gi.repository import Pango

from cubic.constants import OK, ERROR, BULLET, PROCESSING, BLANK
from cubic.utilities import logger
from cubic.utilities import model

logger.log_value('Using GtkSource version', GtkSource._version)

########################################################################
# Global Variables & Constants
########################################################################

# Status icons may be referenced using the constants:
# OK, ERROR, OPTIONAL, BULLET, PROCESSING, BLANK
icons = ['cubic-ok-symbolic', 'cubic-error-symbolic', 'cubic-optional-symbolic', 'cubic-bullet-symbolic', 'cubic-blank-symbolic', 'cubic-blank-symbolic']

# Get the system mono-spaced font.
settings = Gio.Settings.new('org.gnome.desktop.interface')
font_name = settings.get_string('monospace-font-name')
MONOSPACE_FONT = Pango.FontDescription(font_name)

# Get the source view language for ini files.
language_name = 'ini'
language_name_manager = GtkSource.LanguageManager()
SOURCE_LANGUAGE = language_name_manager.get_language(language_name)

# Get the source view style for Tango.
scheme_name = 'tango'
style_scheme_manager = GtkSource.StyleSchemeManager()
SOURCE_STYLE_SCHEME = style_scheme_manager.get_scheme(scheme_name)

# Transition Effects
SLIDE_NONE = Gtk.StackTransitionType.NONE
SLIDE_LEFT = Gtk.StackTransitionType.SLIDE_LEFT
SLIDE_RIGHT = Gtk.StackTransitionType.SLIDE_RIGHT
SLIDE_UP = Gtk.StackTransitionType.SLIDE_UP
SLIDE_DOWN = Gtk.StackTransitionType.SLIDE_DOWN
CROSS_FADE = Gtk.StackTransitionType.CROSSFADE

########################################################################
# General Functions
########################################################################


def idle_add(callback):
    """
    The Project page uses this function to block and unblock handlers.
    Note that the console module calls GLib.idle_add() directly.

    Arguments:
    callback : str
        A callback function that does not take any arguments.
    """

    GLib.idle_add(callback)


########################################################################
# Page Functions
########################################################################


def main_quit():
    """
    Quit the GUI application.
    """

    GLib.idle_add(Gtk.main_quit)


def transition(old_page, new_page, effect=SLIDE_NONE):
    """
    Transition the to a new page in the Gtk.Stack using the specified
    Gtk.StackTransitionType effect. All pages must have the 'visible'
    property set to True in the *.ui file.

    Arguments:
    old_page : str
        The page to transition from.
    new_page : str
        The page to transition to.
    effect : str
        An optional effect to use for the transition.
    """

    logger.log_label('Transition pages')

    if old_page != new_page:
        # Get the Gtk.Stack.
        pages = model.builder.get_object('pages')
        if old_page:
            # Print a message.
            logger.log_value('Hide old page', old_page.name.replace('_', ' '))
        if new_page:
            # Show the next page
            logger.log_value('Show new page', new_page.name.replace('_', ' '))
            GLib.idle_add(Gtk.Stack.set_visible_child_full, pages, new_page.name, effect)
    else:
        # Stay on the current page.
        logger.log_value('Stay on page', old_page.name.replace('_', ' '))


########################################################################
# Navigation Button Functions
########################################################################


def reset_buttons(
        back_button_label=None,
        back_action=None,
        back_button_style=None,
        is_back_sensitive=None,
        is_back_visible=None,
        next_button_label=None,
        next_action=None,
        next_button_style=None,
        is_next_sensitive=None,
        is_next_visible=None):
    """
    Reset the label, action, style, sensitivity, and visibility of the
    Back button and the Next button. Valid button styles are
     "text-button", "suggested-action", and "destructive-action".

    Arguments:
    back_button_label : str
        Optional new Back button label, or None to leave it unchanged.
        The default is None.
    back_button_action : str
        Optional new Back button action, or None to leave it unchanged.
        The default is None.
    back_button_style : str
        Optional new Back button style, or None to leave it unchanged.
        The default is None.
    is_back_sensitive : bool
        Optional new Back button sensitivity. True to set the Back
        button sensitive, False to set it insensitive, or None to leave
        it unchanged. The default is None.
    is_back_visible : bool
        Optional new Back button visibility. True to set the Back
        button visible, False to set it invisible, or None to leave it
        unchanged. The default is None.
    next_button_label : str
        Optional new Next button label, or None to leave it unchanged.
        The default is None.
    next_button_action : str
        Optional new Next button action, or None to leave it unchanged.
        The default is None.
    next_button_style : str
        Optional new Next button style, or None to leave it unchanged.
        The default is None.
    is_next_sensitive : bool
        Optional new Next button sensitivity. True to set the Next
        button sensitive, False to set it insensitive, or None to leave
        it unchanged. The default is None.
    is_next_visible : bool
        Optional new Next button visibility. True to set the Next
        button visible, False to set it invisible, or None to leave it
        unchanged. The default is None.
    """

    # Unicode characters for various arrows:
    #
    # 25C1 = ◁
    # 25B7 = ▷
    #
    # 25C3 = ◃ Back
    # 25B9 = ▹ Next
    #
    # 261C = ☜ Back
    # 261E = ☞ Next
    #
    # 276C = ❬ Back
    # 276D = ❭ Next
    #
    # 21E6 = ⇦ Back
    # 21E8 = ⇨ Next
    #
    # 2190 = ← Back
    # 2192 = → Next

    set_button('back_button', back_button_label, back_action, back_button_style, is_back_sensitive, is_back_visible)
    set_button('next_button', next_button_label, next_action, next_button_style, is_next_sensitive, is_next_visible)


def set_button(name, label, action, style, is_sensitive, is_visible):
    """
    Update the label, action, style, sensitivity, and visibility of the
    button.

    Arguments:
    label : str
        The new button label, or None to leave it unchanged.
    action : str
        The new button action, or None to leave it unchanged.
    style : str
        The new button style, or None to leave it unchanged.
    sensitive : bool
        True to set the button sensitive, False to set it insensitive,
        or None to leave it unchanged.
    visible : bool
        True to set the button visible, False to set it invisible, or
        None to leave it unchanged.
    """

    button = model.builder.get_object(name)
    if is_visible is not None:
        GLib.idle_add(Gtk.Button.set_visible, button, is_visible)
    if action is not None:
        button.action = action
    if label is not None:
        GLib.idle_add(Gtk.Button.set_label, button, label)
    if style is not None:
        update_button_style(name, style)
    if is_sensitive is not None:
        GLib.idle_add(Gtk.Button.set_sensitive, button, is_sensitive)


def update_button_style(name, style):
    """
    Update the button style to the specified style, and remove the
    current style from the button. The default style, "text-button", is
    never removed. Valid button styles are "text-button",
    "suggested-action", and "destructive-action". If style is None, the
    current style will be removed from the button, and a new style will
    not be set.

    Arguments:
    name : str
        The name of the button to update.
    style : str
        The new button style, or None to remove the current style.
    """

    button = model.builder.get_object(name)
    context = button.get_style_context()
    if style != 'suggested-action':
        if context.has_class('suggested-action'):
            GLib.idle_add(Gtk.StyleContext.remove_class, context, 'suggested-action')
    elif style == 'suggested-action':
        if not context.has_class('suggested-action'):
            GLib.idle_add(Gtk.StyleContext.add_class, context, 'suggested-action')
    if style != 'destructive-action':
        if context.has_class('destructive-action'):
            GLib.idle_add(Gtk.StyleContext.remove_class, context, 'destructive-action')
    elif style == 'destructive-action':
        if not context.has_class('destructive-action'):
            GLib.idle_add(Gtk.StyleContext.add_class, context, 'destructive-action')
    # The default style, 'text-button', is never removed.
    # if style != 'text-button':
    #     if context.has_class('text-button'):
    #         GLib.idle_add(Gtk.StyleContext.remove_class, context, 'text-button')
    # elif style == 'text-button':
    #     if not context.has_class('text-button'):
    #         GLib.idle_add(Gtk.StyleContext.add_class, context, 'text-button')


########################################################################
# Container Functions
########################################################################


def attach(grid, widget, x, y, width, height):
    """
    Add the widget to the grid.

    Arguments:
    widget : Gtk.Widget
        The widget to add.
    x : int
        The x coordinate of the new widget.
    y : int
        The y coordinate of the new widget.
    width : int
        The width of the new widget.
    height : int
        The height of the new widget.
    """

    GLib.idle_add(Gtk.Grid.attach, grid, widget, x, y, width, height)


def add_named(stack, page, name):
    """
    Add the page to the stack with the specified name.

    Arguments:
    stack : Gtk.Stack
        The stack to add the page to.
    page : Gtk.Grid
        The page to add to the stack.
    name : str
        The name of the page.
    """

    GLib.idle_add(Gtk.Stack.add_named, stack, page, name)


def set_visible_child(stack, page):
    """
    Make the page on the stack visible. If page is different from the
    currently visible page, animate the transition using the current
    transition type.

    Arguments:
    stack : Gtk.Stack
        The stack that the page belongs to.
    page : Gtk.Grid
        The page to make visible.
    """

    GLib.idle_add(Gtk.Stack.set_visible_child, stack, page)


########################################################################
# Show / Hide Functions
########################################################################


def show(widget_name):
    """
    Show the widget.

    Arguments:
    widget_name : str
        The name of the widget.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.show, widget)


def hide(widget_name):
    """
    Hide the widget.

    Arguments:
    widget_name : str
        The name of the widget.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.hide, widget)


def show_all(widget_name):
    """
    Recursively show the widget and any child widgets (if the widget is
    a container).

    Arguments:
    widget_name : str
        The name of the widget.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.show_all, widget)


def set_visible(widget_name, is_visible):
    """
    Make the widget visible or invisible.

    Arguments:
    widget_name : str
        The name of the widget.
    is_visible : bool
        True to set the widget visible. False to set it invisible.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.set_visible, widget, is_visible)


def set_solid(widget_name, is_solid):
    """
    Set the opacity of the widget to 1.0 or 0.00. If is_solid is True
    the opacity will be set to 1.00. If is_solid is False the opacity
    will be set to 0.00.

    Arguments:
    widget_name : str
        The name of the widget.
    is_solid : bool
        True to set the widget opaque. False to set it transparent.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.set_opacity, widget, is_solid)


def set_opacity(widget_name, opacity):
    """
    Set the opacity of the widget.

    Arguments:
    widget_name : str
        The name of the widget.
    opacity : float
        The opacity to set. The value must be 0.00 to 1.00.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.set_opacity, widget, opacity)


def set_sensitive(widget_name, is_sensitive):
    """
    Set the sensitivity of the widget.

    Arguments:
    widget_name : str
        The name of the widget.
    is_sensitive : bool
        True to set the widget sensitive. False to set it insensitive.
    """

    widget = model.builder.get_object(widget_name)
    GLib.idle_add(Gtk.Widget.set_sensitive, widget, is_sensitive)


def show_popover(popover_name):
    """
    show the popover using a transition.

    Arguments:
    popover_name : str
        The name of the popover.
    """

    popover = model.builder.get_object(popover_name)
    GLib.idle_add(Gtk.Popover.popup, popover)


def hide_popover(popover_name):
    """
    Hide the popover using a transition.

    Arguments:
    popover_name : str
        The name of the popover.
    """

    popover = model.builder.get_object(popover_name)
    GLib.idle_add(Gtk.Popover.popdown, popover)


########################################################################
# Label Functions
########################################################################


def update_label(label_name, text, is_error=None):
    """
    Update the label text. If specified, add or remove the "error" style
    context for the label.

    Arguments:
    label_name : str
        The name of the label.
    text : str
        The text to display.
    is_error : bool or None
        None to not change the style context. The style context will
        retain its previous value ("error" or no "error"). None is the
        default.
        True to set the "error" style context.
        False to remove the "error" style context.
    """
    # logger.log_value(f'Update label {label_name}', text)

    # Set the label with markup enabled.
    label = model.builder.get_object(label_name)
    GLib.idle_add(Gtk.Label.set_markup, label, text)

    # Add or remove the "error" style context.
    if is_error is not None:
        context = label.get_style_context()
        if is_error:
            GLib.idle_add(Gtk.StyleContext.add_class, context, 'error')
        else:
            GLib.idle_add(Gtk.StyleContext.remove_class, context, 'error')


def update_label_ORIGINAL(label_name, text):
    """
    Update the label text.

    Arguments:
    label_name : str
        The name of the label.
    text : str
        The text to display.
    """

    # logger.log_value(f'Update label {label_name}', text)
    label = model.builder.get_object(label_name)
    GLib.idle_add(Gtk.Label.set_markup, label, text)


def set_label_error(label_name, is_error):
    """
    Set or remove the "error" style context for the label.

    Arguments:
    label_name : str
        The name of the label.
    is_error : bool
        True to set an "error" style context. False to remove the
        "error" style context.
    """

    # logger.log_value(f'Set error for label {label_name}', is_error)
    label = model.builder.get_object(label_name)
    context = label.get_style_context()
    if is_error:
        GLib.idle_add(Gtk.StyleContext.add_class, context, 'error')
    else:
        GLib.idle_add(Gtk.StyleContext.remove_class, context, 'error')


########################################################################
# Entry Functions
########################################################################


def update_entry(entry_name, text):
    """
    Update the entry text.

    Arguments:
    entry_name : str
        The name of the entry.
    text : str
        The text to display.
    """

    # logger.log_value(f'Update text for entry {entry_name}', text)
    entry = model.builder.get_object(entry_name)
    GLib.idle_add(Gtk.Entry.set_text, entry, text)


def set_entry_error(entry_name, is_error):
    """
    Set or remove the "error" style context for the entry.

    Arguments:
    entry_name : str
        The name of the entry.
    is_error : bool
        True to set an "error" style context. False to remove the
        "error" style context.
    """

    # logger.log_value(f'Set error for entry {entry_name}', is_error)
    entry = model.builder.get_object(entry_name)
    context = entry.get_style_context()
    if is_error:
        GLib.idle_add(Gtk.StyleContext.add_class, context, 'error')
    else:
        GLib.idle_add(Gtk.StyleContext.remove_class, context, 'error')


def set_entry_editable(entry_name, is_editable):
    """
    Make the entry editable or non-editable.

    Arguments:
    entry_name : str
        The name of the entry.
    is_editable : bool
        True to set the entry editable. False to set it not editable.
    """

    # logger.log_value(f'Set is editable for entry {entry_name}', is_editable)
    entry = model.builder.get_object(entry_name)
    # entry.set_editable(is_editable)
    GLib.idle_add(Gtk.Entry.set_editable, entry, is_editable)


########################################################################
# Combo Box Text Functions
########################################################################


def append_combo_box_text(combo_box_name, text):
    """
    Add text to the end of the specified combo box text.

    Arguments:
    combo_box_name : str
        The name of the combo box.
    text : str
        The text to add.
    """

    # logger.log_value(f'Append combo box text {combo_box_name}', text)
    combo_box_text = model.builder.get_object(combo_box_name)
    GLib.idle_add(Gtk.ComboBoxText.append_text, combo_box_text, text)


def prepend_combo_box_text(combo_box_name, text):
    """
    Add text to the beginning of the specified combo box text.

    Arguments:
    combo_box_name : str
        The name of the combo box.
    text : str
        The text to add.
    """

    # logger.log_value(f'Prepend combo box text {combo_box_name}', text)
    combo_box_text = model.builder.get_object(combo_box_name)
    GLib.idle_add(Gtk.ComboBoxText.prepend_text, combo_box_text, text)


def remove_all_combo_box_text(combo_box_name):
    """
    Remove all text from the the specified combo box.

    Arguments:
    combo_box_name : str
        The name of the combo box.
    """

    # logger.log_value('Remove all text from combo box text', combo_box_name)
    combo_box_text = model.builder.get_object(combo_box_name)
    GLib.idle_add(Gtk.ComboBoxText.remove_all, combo_box_text)


########################################################################
# File Chooser Functions
########################################################################


def show_file_chooser(file_chooser_name, file_path, *button_names):
    """
    Show the file chooser, select the file path, and set buttons
    sensitive if file path is selected.

    Arguments:
    file_chooser : str
        The name of the file chooser.
    file_path : str
        A file path.
    button_names : tuple
        An optional list of button names.
    """

    file_chooser = model.builder.get_object(file_chooser_name)
    GLib.idle_add(_show_file_chooser, file_chooser, file_path, button_names)


def _show_file_chooser(file_chooser, file_path, button_names):
    """
    This function must be invoked using GLib.idle_add().

    Show the file chooser, select the file path, and set buttons
    sensitive if file path is selected.

    Arguments:
    file_chooser : str
        The name of the file chooser.
    file_path : str
        A file path.
    button_names : tuple
        A tuple of button names. May be empty.
    """

    # set_filename() opens the file's parent folder and selects the
    # file in the list. If the file does not exist, no file is selected.
    # select_filename() selects a file name. If the file name isn't in
    # the current folder, then the current folder will be changed to the
    # folder containing filename.
    # See https://lazka.github.io/pgi-docs/Gtk-3.0/classes/FileChooser.html#Gtk.FileChooser.set_filename

    file_chooser.set_filename(file_path)
    is_selected = bool(file_chooser.get_filename())
    for button_name in button_names:
        button = model.builder.get_object(button_name)
        button.set_sensitive(is_selected)
    file_chooser.show_all()


########################################################################
# Status Functions
########################################################################


def update_status(prefix, status):
    """
    Update the status by displaying a status icon (OK, ERROR, OPTIONAL,
    BULLET) or by displaying an active spinner. The proper naming
    convention must be used for widgets names:
    • Widgets names must end in "_status" or "_spinner".
    • Widgets names ending in "_status" are always images.
    • Widgets names ending in "_spinner" are always spinners.

    Arguments:
    prefix : str
        The prefix portion of widget names that end in "_status" or
        "_spinner".
    status : int
        A status value from the constants module: OK, ERROR, OPTIONAL,
        BULLET, PROCESSING, or BLANK.
    """

    # logger.log_value(f'Set status for entry {prefix}_status', status)

    # Valid icon sizes are:
    #
    #   0 = Gtk.IconSize.INVALID
    #   1 = Gtk.IconSize.MENU
    #   2 = Gtk.IconSize.SMALL_TOOLBAR
    #   3 = Gtk.IconSize.LARGE_TOOLBAR
    #   4 = Gtk.IconSize.BUTTON
    #   5 = Gtk.IconSize.DND (Drag and Drop)
    #   6 = Gtk.IconSize.DIALOG

    image = model.builder.get_object(f'{prefix}_status')
    GLib.idle_add(Gtk.Image.set_from_icon_name, image, icons[status], Gtk.IconSize.BUTTON)
    spinner = model.builder.get_object(f'{prefix}_spinner')
    if spinner:
        if status == PROCESSING:
            GLib.idle_add(Gtk.Spinner.set_visible, spinner, True)
            # GLib.idle_add(Gtk.Spinner.set_opacity, spinner, True)
            GLib.idle_add(Gtk.Spinner.start, spinner)
        else:
            GLib.idle_add(Gtk.Spinner.set_visible, spinner, False)
            # GLib.idle_add(Gtk.Spinner.set_opacity, spinner, False)
            GLib.idle_add(Gtk.Spinner.stop, spinner)


def update_status_image(name, status):
    """
    This function is used on the Terminal page.

    Update the status by displaying a status icon (OK, ERROR, OPTIONAL,
    BULLET). The proper naming convention must be used for widgets names:
    • Widgets names must end in "_status" or "_spinner".
    • Widgets names ending in "_status" are always images.
    • Widgets names ending in "_spinner" are always spinners.

    Arguments:
    prefix : str
        The prefix portion of widget names that end in "_status" or
        "_spinner".
    status : int
        A status value from the constants module: OK, ERROR, OPTIONAL,
        BULLET, or BLANK.
    """

    image = model.builder.get_object(name)
    GLib.idle_add(Gtk.Image.set_from_icon_name, image, icons[status], Gtk.IconSize.BUTTON)


########################################################################
# Progress Bar Functions
########################################################################


def update_progress_bar_percent(progress_bar_name, percent):
    """
    Update the progress bar percent.

    Arguments:
    progress_bar_name : str
        The name of the progress bar.
    percent : float
        The percent complete. The value must be 0.00% to 100.00%.
    """

    progress_bar = model.builder.get_object(progress_bar_name)
    GLib.idle_add(Gtk.ProgressBar.set_fraction, progress_bar, float(percent) / 100.00)


def update_progress_bar_text(progress_bar_name, text):
    """
    Update the progress bar text. In order to show text in the progress
    bar, the progress bar's "show-text" property must be True in the
    corresponding *.ui file, and the value of text must be either a
    space character " " or the non-empty text string to be displayed. If
    text is an empty string "" or None, a percent ("0 %") will be
    displayed instead.

    Arguments:
    progress_bar_name : str
        The name of the progress bar.
    text : str
        The text to display or " " (space character), not None.
    """

    progress_bar = model.builder.get_object(progress_bar_name)
    GLib.idle_add(Gtk.ProgressBar.set_text, progress_bar, text)


########################################################################
# Button Functions
########################################################################


def set_button_label(button_name, label):
    """
    Set the button label.

    Arguments:
    button_name : str
        The name of a Gtk.Button or Gtk.ModelButton.
    label : str
        The label text to display.
    """

    button = model.builder.get_object(button_name)
    if isinstance(button, Gtk.ModelButton):
        GLib.idle_add(Gtk.ModelButton.set_property, button, 'text', label)
    else:
        GLib.idle_add(Gtk.Button.set_label, button, label)


def activate_toggle_button(toggle_button_name, is_active):
    """
    This function is used on the Options page.

    Activate or deactivate the toggle button.

    Arguments:
    toggle_button_name : str
        The name of the toggle button.
    is_active : bool
        True to set the toggle button active. False to set it inactive.
    """

    toggle_button = model.builder.get_object(toggle_button_name)
    GLib.idle_add(Gtk.ToggleButton.set_active, toggle_button, is_active)


def activate_check_button(check_button_name, is_active):
    """
    This function is used on the Delete page and Finish page.

    Activate or deactivate the check button.

    Arguments:
    check_button_name : str
        The name of the check button.
    is_active : bool
        True to set the check button active. False to set it inactive.
    """

    check_button = model.builder.get_object(check_button_name)
    GLib.idle_add(Gtk.CheckButton.set_active, check_button, is_active)


def activate_switch(switch_name, is_active):
    """
    This function is used on the Packages page.

    Activate or deactivate the switch.

    Arguments:
    switch_name : str
        The name of the switch.
    is_active : bool
        True to set the switch active. False to set it inactive.
    """

    switch = model.builder.get_object(switch_name)
    GLib.idle_add(Gtk.Switch.set_active, switch, is_active)


def update_check_button_label(check_button_name, label):
    """
    This function is used on the Delete page.

    Update the check button label.

    Arguments:
    check_button_name : str
        The name of the check button.
    label : str
        The label text to display.
    """

    check_button = model.builder.get_object(check_button_name)
    GLib.idle_add(Gtk.CheckButton.set_label, check_button, label)


def activate_radio_button(radio_button_name, is_active):
    """
    Activate or deactivate the radio button.

    Arguments:
    radio_button_name : str
        The name of the radio button.
    is_active : bool
        True to set the radio button active. False to set it inactive.
    """

    radio_button = model.builder.get_object(radio_button_name)
    GLib.idle_add(Gtk.RadioButton.set_active, radio_button, is_active)


########################################################################
# Menu Functions
########################################################################


def update_menu_item(menu_item_name, text):
    """
    This function is used on the Terminal page.

    Update the menu item text.

    Arguments:
    menu_item_name : str
        The name of the menu item.
    text : str
        The text to display.
    """

    menu_item = model.builder.get_object(menu_item_name)
    GLib.idle_add(Gtk.MenuItem.set_label, menu_item, text)


########################################################################
# Box Functions (Prepare page and Generate page)
########################################################################


def empty_box(box_name):
    """
    Remove all items from the box.

    Arguments:
    box_name : str
        The name of the box.
    """

    box = model.builder.get_object(box_name)
    for child in box.get_children():
        # TODO: Do we need the logging here?
        if isinstance(child, Gtk.Label):
            logger.log_value('Removing label from box', child.get_text())
        elif isinstance(child, Gtk.Button):
            logger.log_value('Removing button from box', child.get_label())
        else:
            logger.log_value('Removing unknown type from box', child)
        GLib.idle_add(Gtk.Box.remove, box, child)
        GLib.idle_add(Gtk.Widget.destroy, child)


def insert_box_label(box_name, text, opacity=1.00, is_error=False):
    """
    Insert a label into the box.

    Arguments:
    box_name : str
        The name of the box.
    test : str
        The text for the label.
    opacity : float
        Optional opacity for the label. The value must be 0.00 to 1.00.
        The default is 1.00.
    is_error : bool
        Optional "error" style context for the label. True to set an
        "error" style context. False to not set an "error" style context.
        The default is False.
    """

    # Since label is not displayed, there is no need to call GLib.idle_add().
    label = Gtk.Label(text)
    label.set_halign(Gtk.Align.FILL)
    label.set_hexpand(False)
    label.set_xalign(0.00)
    label.set_visible(True)
    label.set_opacity(opacity)
    if is_error:
        context = label.get_style_context()
        context.add_class('error')
    label.set_justify(Gtk.Justification.LEFT)
    label.set_line_wrap(True)
    # label.set_max_width_chars(0)

    box = model.builder.get_object(box_name)
    GLib.idle_add(Gtk.Box.add, box, label)


def scroll_view_port_to_bottom(view_port_name):
    """
    Scroll the to the bottom of the view port.

    Arguments:
    view_port_name : str
        The name of the view port.
    """

    view_port = model.builder.get_object(view_port_name)
    adjustment = view_port.get_vadjustment()
    amount = adjustment.get_upper() - adjustment.get_page_size()
    GLib.idle_add(Gtk.Adjustment.set_value, adjustment, amount)


########################################################################
# Tree View Functions
########################################################################


def set_column_visible(tree_view_column_name, is_visible):
    """
    Make the tree view column visible or invisible.

    Arguments:
    tree_view_column_name : str
        The name of the tree view column.
    is_visible : bool
        True to set the tree view column visible. False to set it
        invisible.
    """

    tree_view_column = model.builder.get_object(tree_view_column_name)
    GLib.idle_add(Gtk.TreeViewColumn.set_visible, tree_view_column, is_visible)


def scroll_to_tree_view_row(tree_view_name, row_number):
    """
    Scroll the to the specified row of the tree view.

    Arguments:
    tree_view_name : str
        The name of the tree view.
    row_number : int
        The row number.
    """

    tree_view = model.builder.get_object(tree_view_name)
    tree_path = Gtk.TreePath.new_from_string(str(row_number))
    GLib.idle_add(Gtk.TreeView.scroll_to_cell, tree_view, tree_path, None, True, 0.5, 0.0)


def select_tree_view_row(tree_view_name, row_number):
    """
    Select the the specified row of the tree view.

    Arguments:
    tree_view_name : str
        The name of the tree view.
    row_number : int
        The row number.
    """

    tree_view = model.builder.get_object(tree_view_name)
    tree_path = Gtk.TreePath.new_from_string(str(row_number))
    GLib.idle_add(Gtk.TreeView.set_cursor, tree_view, tree_path, None, False)


########################################################################
# List Store Functions
########################################################################


def update_list_store(list_store_name, data_list):
    """
    Add the list of data to to the list store.

    Arguments:
    list_store_name : str
        The name of the list store.
    data_list : list
        The list of data. Each data in the list is also a list.
    """

    list_store = model.builder.get_object(list_store_name)
    GLib.idle_add(_update_list_store_rows, list_store, data_list)


def _update_list_store_rows(list_store, data_list):
    """
    This function must be invoked using GLib.idle_add().

    Add the list of data to to the list store.

    Arguments:
    list_store : Gtk.ListStore
        The list store.
    data_list : list
        The list of data. Each data in the list is also a list.
    """

    list_store.clear()
    for number, data in enumerate(data_list):
        # logger.log_value(f'{number+1}. Adding an item to the list', data)
        list_store.append(data)


def update_list_store_progress_bar_percent(list_store_name, row_number, percent):
    """
    Update progress bar percent for the specified row in the list store.
    The progress bar must be in the first column of the list store.

    Arguments:
    list_store_name : str
        The name of the list store.
    row_number : int
        The row number to update.
    percent : float
        The percent complete. The value must be 0.00% to 100.00%.
    """

    list_store = model.builder.get_object(list_store_name)
    GLib.idle_add(_update_list_store_progress_bar_percent, list_store, row_number, percent)


def _update_list_store_progress_bar_percent(list_store, row_number, percent):
    """
    This function must be invoked using GLib.idle_add().

    Update progress bar percent for the specified row in the list store.
    The progress bar must be in the first column of the list store.

    Arguments:
    list_store : Gtk.ListStore
        The list store.
    row_number : int
        The row number to update.
    percent : float
        The percent complete. The value must be 0.00% to 100.00%.
    """

    # The progress bar is at position 0 (i.e. the first column) in the
    # row list.
    list_store[row_number][0] = percent
