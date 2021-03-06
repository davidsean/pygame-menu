# coding=utf-8
"""
pygame-menu
https://github.com/ppizarror/pygame-menu

TEXT INPUT
Text input class, this widget lets user to write text.

License:
-------------------------------------------------------------------------------
The MIT License (MIT)
Copyright 2017-2019 Pablo Pizarro R. @ppizarror

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-------------------------------------------------------------------------------
"""

import pygame as _pygame
from pygameMenu import config_controls as _ctrl
from pygameMenu import locals as _locals
from pygameMenu.widgets.widget import Widget

try:
    from pyperclip import copy, paste
except ImportError:
    # noinspection PyUnusedLocal
    def copy(text):
        """
        Copy method.

        :return: None
        """
        pass


    def paste():
        """
        Paste method.

        :return: Empty string
        :rtype: basestring
        """
        return ''


class TextInput(Widget):
    """
    Text input widget.
    """

    def __init__(self,
                 label='',
                 default='',
                 textinput_id='',
                 input_type=_locals.PYGAME_INPUT_TEXT,
                 cursor_color=(0, 0, 1),
                 history=50,
                 maxchar=0,
                 maxwidth=0,
                 onchange=None,
                 onreturn=None,
                 repeat_keys_initial_ms=400,
                 repeat_keys_interval_ms=25,
                 repeat_mouse_interval_ms=50,
                 text_ellipsis='...',
                 **kwargs
                 ):
        """
        Description of the specific paramaters (see Widget class for generic ones):

        :param label: Input label text
        :type label: basestring
        :param default: Initial text to be displayed
        :type default: basestring
        :param textinput_id: ID of the text input
        :type textinput_id: basestring
        :param input_type: Type of data
        :type input_type: basestring
        :param cursor_color: Color of cursor
        :type cursor_color: tuple
        :param history: Maximum number of editions stored
        :type history: int
        :param maxchar: Maximum length of input
        :type maxchar: int
        :param maxwidth: Maximum size of the text to be displayed (overflow)
        :type maxwidth: int
        :param onchange: Callback when changing the selector
        :type onchange: function, NoneType
        :param onreturn: Callback when pressing return button
        :type onreturn: function, NoneType
        :param repeat_keys_initial_ms: Time in ms before keys are repeated when held
        :type repeat_keys_initial_ms: float, int
        :param repeat_keys_interval_ms: Interval between key press repetition when held
        :type repeat_keys_interval_ms: float, int
        :param repeat_mouse_interval_ms: Interval between mouse events when held
        :type repeat_mouse_interval_ms: float, int
        :param text_ellipsis: Ellipsis text when overflow occurs
        :type text_ellipsis: basestring
        :param kwargs: Optional keyword-arguments for callbacks
        """
        super(TextInput, self).__init__(widget_id=textinput_id, onchange=onchange,
                                        onreturn=onreturn, kwargs=kwargs)
        if maxchar < 0:
            raise ValueError('maxchar must be equal or greater than zero')
        if maxwidth < 0:
            raise ValueError('maxwidth must be equal or greater than zero')
        assert isinstance(history, int)
        if history < 0:
            raise ValueError('history must be equal or greater than zero')

        self._input_string = ''  # Inputted text
        self._ignore_keys = (_ctrl.MENU_CTRL_UP, _ctrl.MENU_CTRL_DOWN,
                             _pygame.K_LCTRL, _pygame.K_RCTRL,
                             _pygame.K_LSHIFT, _pygame.K_RSHIFT,
                             _pygame.K_NUMLOCK, _pygame.K_CAPSLOCK,
                             _pygame.K_TAB, _pygame.K_RETURN, _pygame.K_ESCAPE)

        # Vars to make keydowns repeat after user pressed a key for some time:
        self._block_copy_paste = False  # Blocks event
        self._key_is_pressed = False
        self._keyrepeat_counters = {}  # {event.key: (counter_int, event.unicode)} (look for "***")
        self._keyrepeat_initial_interval_ms = repeat_keys_initial_ms
        self._keyrepeat_interval_ms = repeat_keys_interval_ms
        self._last_key = 0

        # Mouse handling
        self._keyrepeat_mouse_ms = 0
        self._keyrepeat_mouse_interval_ms = repeat_mouse_interval_ms
        self._mouse_is_pressed = False

        # Render box (overflow)
        self._ellipsis = text_ellipsis
        self._ellipsis_size = 0
        self._renderbox = [0, 0, 0]  # Left/Right/Inner

        # Things cursor:
        self._clock = _pygame.time.Clock()
        self._cursor_color = cursor_color
        self._cursor_ms_counter = 0
        self._cursor_position = 0  # Inside text
        self._cursor_render = True  # If true cursor must be rendered
        self._cursor_surface = None
        self._cursor_surface_pos = [0, 0]  # Position (x,y) of surface
        self._cursor_switch_ms = 500  # /|\
        self._cursor_visible = False  # Switches every self._cursor_switch_ms ms

        # Public attributs
        self.label = label

        # History of editions
        self._history = []
        self._history_cursor = []
        self._history_renderbox = []
        self._history_index = 0  # Index at which the new editions are added
        self._max_history = history

        # Other
        self._input_type = input_type
        self._label_size = 0
        self._maxchar = maxchar
        self._maxwidth = maxwidth

        # Set default value
        if self._check_input_type(default):
            default = str(default)
            self._input_string = default
            for i in range(len(default) + 1):
                self._move_cursor_right()
            self._update_input_string(default)
        else:
            raise ValueError('default value "{0}" type is not correct according to input_type'.format(default))

    def _apply_font(self):
        """
        See upper class doc.
        """
        self._ellipsis_size = self._font.size(self._ellipsis)[0]
        self._label_size = self._font.size(self.label)[0]

    def clear(self):
        """
        Clear the current text.

        :return: None
        """
        self._input_string = ''
        self._cursor_position = 0

    def get_value(self):
        """
        See upper class doc.
        """
        value = ''
        if self._input_type == _locals.PYGAME_INPUT_TEXT:
            value = self._input_string
        elif self._input_type == _locals.PYGAME_INPUT_FLOAT:
            try:
                value = float(self._input_string)
            except ValueError:
                value = 0
        elif self._input_type == _locals.PYGAME_INPUT_INT:
            try:
                value = int(self._input_string)
            except ValueError:
                value = 0
        return value

    def draw(self, surface):
        """
        See upper class doc.
        """
        self._clock.tick()
        self._render()

        # Draw string
        surface.blit(self._surface, (self._rect.x, self._rect.y))

        # Draw cursor
        if self.selected and (self._cursor_visible or (self._mouse_is_pressed or self._key_is_pressed)):
            surface.blit(self._cursor_surface, (self._rect.x + self._cursor_surface_pos[0],
                                                self._rect.y + self._cursor_surface_pos[1]))

    def _render(self):
        """
        See upper class doc.
        """
        string = self.label + self._get_input_string()
        if self.selected:
            color = self._font_selected_color
        else:
            color = self._font_color
        self._surface = self.render_string(string, color)
        self._render_cursor()

    def _render_cursor(self):
        """
        Cursor is rendered and stored.

        :return: None
        """
        # Cursor should not be rendered
        if not self._cursor_render:
            return

        # Cursor surface does not exist
        if self._cursor_surface is None:
            if self._rect.height == 0:  # If menu has not been initialized this error can occur
                return
            self._cursor_surface = _pygame.Surface((int(self._font_size / 20 + 1), self._rect.height - 2))
            self._cursor_surface.fill(self._cursor_color)

        # Calculate x position
        if self._maxwidth == 0 or len(self._input_string) <= self._maxwidth:  # If no limit is provided
            cursor_x_pos = 2 + self._font.size(self.label + self._input_string[:self._cursor_position])[0]
        else:  # Calculate position depending on renderbox
            sstring = self._input_string
            sstring = sstring[self._renderbox[0]:(self._renderbox[0] + self._renderbox[2])]
            cursor_x_pos = 2 + self._font.size(self.label + sstring)[0]

            # Add ellipsis
            delta = self._ellipsis_size
            if self._renderbox[0] != 0 and \
                    self._renderbox[1] != len(self._input_string):  # If Left+Right ellipsis
                delta *= 1
            elif self._renderbox[1] != len(self._input_string):  # Right ellipsis
                delta *= 0
            elif self._renderbox[0] != 0:  # Left ellipsis
                delta *= 1
            else:
                delta *= 0
            cursor_x_pos += delta
        if self._cursor_position > 0 or (self.label and self._cursor_position == 0):
            # Without this, the cursor is invisible when self._cursor_position > 0:
            cursor_x_pos -= self._cursor_surface.get_width()

        # Calculate y position
        cursor_y_pos = 1

        # Store position
        self._cursor_surface_pos[0] = cursor_x_pos
        self._cursor_surface_pos[1] = cursor_y_pos
        self._cursor_render = False

    def _get_input_string(self):
        """
        Return input string, apply overflow if enabled.

        :return: String
        """
        if self._maxwidth != 0 and len(self._input_string) > self._maxwidth:
            text = self._input_string[self._renderbox[0]:self._renderbox[1]]
            if self._renderbox[1] != len(self._input_string):  # Right ellipsis
                text += self._ellipsis
            if self._renderbox[0] != 0:  # Left ellipsis
                text = self._ellipsis + text
            return text
        else:
            return self._input_string

    def _update_renderbox(self, left=0, right=0, addition=False, end=False, start=False):
        """
        Update renderbox position.

        :param left: Left update
        :param right: Right update
        :param addition: Update if text addition/deletion
        :param end: Move cursor to end
        :param start: Move cursor to start
        :type left: int
        :type right: int
        :type addition: bool
        :type end: bool
        :type start: bool
        :return: None
        """
        self._cursor_render = True
        if self._maxwidth == 0:
            return
        ls = len(self._input_string)

        # Move cursor to end
        if end:
            self._renderbox[0] = max(0, ls - self._maxwidth)
            self._renderbox[1] = ls
            self._renderbox[2] = min(ls, self._maxwidth)
            return

        # Move cursor to start
        if start:
            self._renderbox[0] = 0
            self._renderbox[1] = min(ls, self._maxwidth)
            self._renderbox[2] = 0
            return

        # Check limits
        if left < 0 and ls == 0:
            return

        # If no overflow
        if ls <= self._maxwidth:
            if right < 0 and self._renderbox[2] == ls:  # If del at the end of string
                return
            self._renderbox[0] = 0  # To catch unexpected errors
            if addition:  # left/right are ignored
                if left < 0:
                    self._renderbox[1] += left
                self._renderbox[1] += right
                if right < 0:
                    self._renderbox[2] -= right

            # If text is typed increase inner position
            self._renderbox[2] += left
            self._renderbox[2] += right
        else:
            if addition:  # If text is added
                if right < 0 and self._renderbox[2] == self._maxwidth:  # If del at the end of string
                    return
                if left < 0 and self._renderbox[2] == 0:  # If backspace at begining of string
                    return

                # If user deletes something and it is in the end
                if right < 0:  # del
                    if self._renderbox[0] != 0:
                        if (self._renderbox[1] - 1) == ls:  # At the end
                            self._renderbox[2] -= right

                # If the user writes, move renderbox
                if right > 0:
                    if self._renderbox[2] == self._maxwidth:  # If cursor is at the end push box
                        self._renderbox[0] += right
                        self._renderbox[1] += right
                    self._renderbox[2] += right

                if left < 0:
                    if self._renderbox[0] == 0:
                        self._renderbox[2] += left
                    self._renderbox[0] += left
                    self._renderbox[1] += left

            if not addition:  # Move inner (left/right)
                self._renderbox[2] += right
                self._renderbox[2] += left

                # If user pushes after limit the renderbox moves
                if self._renderbox[2] < 0:
                    self._renderbox[0] += left
                    self._renderbox[1] += left
                if self._renderbox[2] > self._maxwidth:
                    self._renderbox[0] += right
                    self._renderbox[1] += right

            # Apply string limits
            self._renderbox[1] = max(self._maxwidth, min(self._renderbox[1], ls))
            self._renderbox[0] = self._renderbox[1] - self._maxwidth

        # Apply limits
        self._renderbox[0] = max(0, self._renderbox[0])
        self._renderbox[1] = max(0, self._renderbox[1])
        self._renderbox[2] = max(0, min(self._renderbox[2], min(self._maxwidth, ls)))

    def _update_cursor_mouse(self, mousex):
        """
        Updates cursor position after mouse click in text.

        :param mousex: Mouse distance relative to surface
        :type mousex: int
        :return: None
        """
        string = self._get_input_string()
        if string == '':  # If string is empty cursor is not updated
            return

        # Calculate size of each character
        string_size = []
        string_total_size = 0
        for i in range(len(string)):
            cs = self._font.size(string[i])[0]  # Char size
            string_size.append(cs)
            string_total_size += cs

        # Find the accumulated char size that gives the position of cursor
        size_sum = 0
        cursor_pos = len(string)
        for i in range(len(string)):
            size_sum += string_size[i] / 2
            if self._label_size + size_sum >= mousex:
                cursor_pos = i
                break
            size_sum += string_size[i] / 2

        # If text have ellipsis
        if self._maxwidth != 0 and len(self._input_string) > self._maxwidth:
            if self._renderbox[0] != 0:  # Left ellipsis
                cursor_pos -= 3

            # Check if user clicked on ellipsis
            if cursor_pos < 0 or cursor_pos > self._maxwidth:
                if cursor_pos < 0:
                    self._renderbox[2] = 0
                    self._move_cursor_left()
                if cursor_pos > self._maxwidth:
                    self._renderbox[2] = self._maxwidth
                    self._move_cursor_right()
                return

            # User clicked on text, update cursor
            cursor_pos = max(0, min(self._maxwidth, cursor_pos))
            self._cursor_position = self._renderbox[0] + cursor_pos
            self._renderbox[2] = cursor_pos

        # Text does not have ellipsis, infered position is correct
        else:
            self._cursor_position = cursor_pos
        self._cursor_render = True

    def _check_mouse_collide_input(self, pos):
        """
        Check mouse collision, if true update cursor.

        :param pos: Position
        :type pos: tuple
        :return: None
        """
        if self._rect.collidepoint(*pos):
            # Check if mouse collides left or right as percentage, use only X coordinate
            mousex, _ = pos
            topleft, _ = self._rect.topleft
            self._update_cursor_mouse(mousex - topleft)
            return True  # Prevents double click

    def set_value(self, text):
        """
        See upper class doc.
        """
        self._input_string = text

    def _check_input_size(self):
        """
        Check input size.

        :return: True if the input must be limited
        :rtype: bool
        """
        if self._maxchar == 0:
            return False
        return self._maxchar < len(self._input_string)

    def _check_input_type(self, string):
        """
        Check if input type is valid.

        :param string: String to validate
        :type string: basestring
        :return: True if the input type is valid
        :rtype: bool
        """
        if string == '':  # Empty is valid
            return True

        if self._input_type == _locals.PYGAME_INPUT_TEXT:
            return True

        conv = None
        if self._input_type == _locals.PYGAME_INPUT_FLOAT:
            conv = int
        elif self._input_type == _locals.PYGAME_INPUT_INT:
            conv = float

        if string == '-':
            return True

        if conv is None:
            return False

        try:
            conv(string)
            return True
        except ValueError:
            return False

    def _move_cursor_left(self):
        """
        Move cursor to left position.

        :return: None
        """
        # Subtract one from cursor_pos, but do not go below zero:
        self._cursor_position = max(self._cursor_position - 1, 0)
        self._update_renderbox(left=-1)

    def _move_cursor_right(self):
        """
        Move cursor to right position.

        :return: None
        """
        # Add one to cursor_pos, but do not exceed len(input_string)
        self._cursor_position = min(self._cursor_position + 1, len(self._input_string))
        self._update_renderbox(right=1)

    def _blur(self):
        """
        See upper class doc.
        """
        # self._key_is_pressed = False
        self._mouse_is_pressed = False
        self._keyrepeat_mouse_ms = 0
        self._cursor_render = True
        self._cursor_visible = False
        # self._history_index = len(self._history) - 1

    def _update_input_string(self, new_string):
        """
        Update input string with a new string, store changes into history.

        :param new_string: New string of text input
        :type new_string: basestring
        :return: None
        """
        l_history = len(self._history)

        # If last edition is different than the new one updates the history
        if ((l_history > 0 and self._history[l_history - 1] != new_string) or l_history == 0) and self._max_history > 0:

            # If index is not at last add the current status as new
            if self._history_index != l_history:
                last_string = self._history[self._history_index]
                self._history_index = len(self._history)
                self._update_input_string(last_string)

            # Add new status to history
            self._history.insert(self._history_index, new_string)
            self._history_cursor.insert(self._history_index, self._cursor_position)
            self._history_renderbox.insert(self._history_index,
                                           [self._renderbox[0], self._renderbox[1], self._renderbox[2]])

            if len(self._history) > self._max_history:
                self._history.pop(0)
                self._history_cursor.pop(0)
                self._history_renderbox.pop(0)
            self._history_index = len(self._history)  # This can be changed with undo/redo

        # Updates string
        self._input_string = new_string

    def _copy(self):
        """
        Copy text from clipboard.

        :return: None
        """
        if self._block_copy_paste:  # Prevents multiple executions of event
            return False

        # Copy all text
        copy(self._input_string)

        self._block_copy_paste = True
        return True

    def _cut(self):
        """
        Cut operation.

        :return:
        """
        self._copy()
        self._cursor_position = 0
        self._renderbox[0] = 0
        self._renderbox[1] = 0
        self._renderbox[2] = 0
        self._update_input_string('')
        self._cursor_render = True  # Due to manually updating renderbox

    def _paste(self):
        """
        Paste text from clipboard.

        :return: None
        """
        if self._block_copy_paste:  # Prevents multiple executions of event
            return False

        # Paste text in cursor
        text = paste().strip()
        for i in ['\n', '\r']:
            text = text.replace(i, '')

        # Delete escape chars
        escapes = ''.join([chr(char) for char in range(1, 32)])
        text = text.translate(escapes)
        if text == '':
            return False

        # Cut string (if limit exists)
        text_end = len(text)
        if self._maxchar != 0:
            char_limit = self._maxchar - len(self._input_string) + 1
            text_end = min(char_limit, text_end)
            if text_end <= 0:  # If there's not more space, returns
                self.sound.play_event_error()
                return False

        new_string = self._input_string[0:self._cursor_position] + \
                     text[0:text_end] + \
                     self._input_string[self._cursor_position:len(self._input_string)]

        # If string is valid
        if self._check_input_type(new_string):
            self.sound.play_key_add()
            self._input_string = new_string  # For a purpose of computing render_box
            for i in range(len(text) + 1):  # Move cursor
                self._move_cursor_right()
            self._update_input_string(new_string)
            self.change()
            self._block_copy_paste = True
        else:
            self.sound.play_event_error()
            return False

        return True

    def _update_from_history(self):
        """
        Update all from history.

        :return: None
        """
        self._input_string = self._history[self._history_index]
        self._renderbox[0] = self._history_renderbox[self._history_index][0]
        self._renderbox[1] = self._history_renderbox[self._history_index][1]
        self._renderbox[2] = self._history_renderbox[self._history_index][2]
        self._cursor_position = self._history_cursor[self._history_index]
        self._cursor_render = True

    def _undo(self):
        """
        Undo operation.

        :return: None
        """
        if self._history_index == 0:  # There's no back history
            return False
        if self._history_index == len(self._history):  # If the actual is the last
            self._history_index -= 1
        self._history_index = max(0, self._history_index - 1)
        self._update_from_history()
        return True

    def _redo(self):
        """
        Redo operation.

        :return: None
        """
        if self._history_index == len(self._history) - 1:  # There's no forward history
            return False
        self._history_index = min(len(self._history) - 1, self._history_index + 1)
        self._update_from_history()
        return True

    def update(self, events):
        """
        See upper class doc.
        """
        updated = False

        for event in events:
            if event.type == _pygame.KEYDOWN:

                # Check if any key is pressed, if True the event is invalid
                if not self.check_key_pressed_valid(event):
                    continue

                self._cursor_visible = True  # So the user sees where he writes
                self._key_is_pressed = True
                self._last_key = event.key

                # If none exist, create counter for that key:
                if event.key not in self._keyrepeat_counters and event.key not in self._ignore_keys:
                    self._keyrepeat_counters[event.key] = [0, event.unicode]

                # User press ctrl+something
                if _pygame.key.get_mods() & _pygame.KMOD_CTRL:

                    # Ctrl+C copy
                    if event.key == _pygame.K_c:
                        return self._copy()

                    # Ctrl+V paste
                    elif event.key == _pygame.K_v:
                        return self._paste()

                    # Ctrl+Z undo
                    elif event.key == _pygame.K_z:
                        self.sound.play_key_del()
                        return self._undo()

                    # Ctrl+Y redo
                    elif event.key == _pygame.K_y:
                        self.sound.play_key_add()
                        return self._redo()

                    # Ctrl+X cut
                    elif event.key == _pygame.K_x:
                        self.sound.play_key_del()
                        return self._cut()

                    # Command not found, returns
                    else:
                        return False

                if event.key == _pygame.K_BACKSPACE:
                    if self._cursor_position == 0:
                        self.sound.play_event_error()
                    else:
                        self.sound.play_key_del()
                    new_string = (
                            self._input_string[:max(self._cursor_position - 1, 0)]
                            + self._input_string[self._cursor_position:]
                    )
                    self._update_input_string(new_string)
                    self._update_renderbox(left=-1, addition=True)
                    self.change()

                    # Subtract one from cursor_pos, but do not go below zero:
                    self._cursor_position = max(self._cursor_position - 1, 0)
                    updated = True

                elif event.key == _pygame.K_DELETE:
                    if self._cursor_position == len(self._input_string):
                        self.sound.play_event_error()
                    else:
                        self.sound.play_key_del()
                    new_string = (
                            self._input_string[:self._cursor_position]
                            + self._input_string[self._cursor_position + 1:]
                    )
                    self._update_input_string(new_string)
                    self._update_renderbox(right=-1, addition=True)
                    self.change()
                    updated = True

                elif event.key == _pygame.K_RIGHT:
                    if self._cursor_position == len(self._input_string):
                        self.sound.play_event_error()
                    else:
                        self.sound.play_key_add()
                    self._move_cursor_right()
                    updated = True

                elif event.key == _pygame.K_LEFT:
                    if self._cursor_position == 0:
                        self.sound.play_event_error()
                    else:
                        self.sound.play_key_add()
                    self._move_cursor_left()
                    updated = True

                elif event.key == _pygame.K_END:
                    self.sound.play_key_add()
                    self._cursor_position = len(self._input_string)
                    self._update_renderbox(end=True)
                    updated = True

                elif event.key == _pygame.K_HOME:
                    self.sound.play_key_add()
                    self._cursor_position = 0
                    self._update_renderbox(start=True)
                    updated = True

                elif event.key == _ctrl.MENU_CTRL_ENTER:
                    self.sound.play_open_menu()
                    self.apply()
                    updated = True

                elif event.key not in self._ignore_keys:

                    # Check input exceeded the limit returns
                    if self._check_input_size():
                        self.sound.play_event_error()
                        break

                    # If no special key is pressed, add unicode of key to input_string
                    new_string = (
                            self._input_string[:self._cursor_position]
                            + event.unicode
                            + self._input_string[self._cursor_position:]
                    )

                    # If unwanted escape sequences
                    event_escaped = repr(event.unicode)
                    if '\\x' in event_escaped or '\\r' in event_escaped:
                        _pygame.event.pump()  # Sync events
                        return False

                    # If data is valid
                    if self._check_input_type(new_string):
                        lkey = len(event.unicode)
                        if lkey > 0:
                            self.sound.play_key_add()
                            self._cursor_position += 1  # Some are empty, e.g. K_UP
                            self._input_string = new_string  # Only here this is changed (due to renderbox update)
                            self._update_renderbox(right=1, addition=True)
                            self._update_input_string(new_string)
                            self.change()
                            updated = True
                    else:
                        self.sound.play_event_error()

            elif event.type == _pygame.KEYUP:
                # *** Because KEYUP doesn't include event.unicode, this dict is stored in such a weird way
                if event.key in self._keyrepeat_counters:
                    del self._keyrepeat_counters[event.key]

                # Release inputs
                self._block_copy_paste = False
                self._key_is_pressed = False

            elif self.mouse_enabled and event.type == _pygame.MOUSEBUTTONUP:
                self._check_mouse_collide_input(event.pos)

        # Get time clock
        time_clock = self._clock.get_time()
        self._keyrepeat_mouse_ms += time_clock

        # Check mouse pressed
        mouse_left, mouse_middle, mouse_right = _pygame.mouse.get_pressed()
        self._mouse_is_pressed = mouse_left or mouse_right or mouse_middle

        if self._keyrepeat_mouse_ms > self._keyrepeat_mouse_interval_ms:
            self._keyrepeat_mouse_ms = 0
            if mouse_left:
                self._check_mouse_collide_input(_pygame.mouse.get_pos())

        # Update key counters:
        for key in self._keyrepeat_counters:
            self._keyrepeat_counters[key][0] += time_clock  # Update clock

            # Generate new key events if enough time has passed:
            if self._keyrepeat_counters[key][0] >= self._keyrepeat_initial_interval_ms:
                self._keyrepeat_counters[key][0] = self._keyrepeat_initial_interval_ms - self._keyrepeat_interval_ms

                event_key, event_unicode = key, self._keyrepeat_counters[key][1]
                # noinspection PyArgumentList
                _pygame.event.post(_pygame.event.Event(_pygame.KEYDOWN,
                                                       key=event_key,
                                                       unicode=event_unicode)
                                   )

        # Update self._cursor_visible
        self._cursor_ms_counter += time_clock
        if self._cursor_ms_counter >= self._cursor_switch_ms:
            self._cursor_ms_counter %= self._cursor_switch_ms
            self._cursor_visible = not self._cursor_visible

        return updated
