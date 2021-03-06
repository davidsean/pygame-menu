# coding=utf-8
"""
pygame-menu
https://github.com/ppizarror/pygame-menu

SOUND
Sound class.

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

# Import pygame and base audio mixer
from pygame import mixer as _mixer
from pygame import error as _pygame_error

try:  # pygame<2.0.0 compatibility
    from pygame import AUDIO_ALLOW_CHANNELS_CHANGE as _AUDIO_ALLOW_CHANNELS_CHANGE
    from pygame import AUDIO_ALLOW_FREQUENCY_CHANGE as _AUDIO_ALLOW_FREQUENCY_CHANGE
except ImportError:
    _AUDIO_ALLOW_CHANNELS_CHANGE = False
    _AUDIO_ALLOW_FREQUENCY_CHANGE = False

# Get sounds folder
import time as _time
import os.path as _path

__actualpath = str(_path.abspath(_path.dirname(__file__))).replace('\\', '/')
__sounddir = '{0}/sounds/{1}.ogg'

# Sound types
SOUND_TYPE_CLICK_MOUSE = '__pygameMenu_sound_click_mouse__'
SOUND_TYPE_CLOSE_MENU = '__pygameMenu_sound_close_menu__'
SOUND_TYPE_ERROR = '__pygameMenu_sound_error__'
SOUND_TYPE_EVENT = '__pygameMenu_sound_event__'
SOUND_TYPE_EVENT_ERROR = '__pygameMenu_sound_event_error__'
SOUND_TYPE_KEY_ADDITION = '__pygameMenu_sound_key_addition__'
SOUND_TYPE_KEY_DELETION = '__pygameMenu_sound_key_deletion__'
SOUND_TYPE_OPEN_MENU = '__pygameMenu_sound_open_menu__'

# Sound examples
PYGAMEMENU_SOUND_EXAMPLE_CLICK_MOUSE = __sounddir.format(__actualpath, 'click_mouse')
PYGAMEMENU_SOUND_EXAMPLE_CLOSE_MENU = __sounddir.format(__actualpath, 'close_menu')
PYGAMEMENU_SOUND_EXAMPLE_ERROR = __sounddir.format(__actualpath, 'error')
PYGAMEMENU_SOUND_EXAMPLE_EVENT = __sounddir.format(__actualpath, 'event')
PYGAMEMENU_SOUND_EXAMPLE_EVENT_ERROR = __sounddir.format(__actualpath, 'event_error')
PYGAMEMENU_SOUND_EXAMPLE_KEY_ADDITION = __sounddir.format(__actualpath, 'key_add')
PYGAMEMENU_SOUND_EXAMPLE_KEY_DELETION = __sounddir.format(__actualpath, 'key_delete')
PYGAMEMENU_SOUND_EXAMPLE_OPEN_MENU = __sounddir.format(__actualpath, 'open_menu')


class Sound(object):
    """
    Sound class.
    """

    def __init__(self, uniquechannel=True, frequency=22050, size=-16, channels=2, buffer=4096, devicename=None,
                 allowedchanges=_AUDIO_ALLOW_CHANNELS_CHANGE | _AUDIO_ALLOW_FREQUENCY_CHANGE):
        """
        Constructor.

        :param uniquechannel: Force the channel to be unique, this is setted at the moment of creation of the object.
        :type uniquechannel: bool
        :param frequency: Frequency of sounds
        :type frequency: int
        :param size: Size of sample
        :type size: int
        :param channels: Number of channels by default
        :type channels: int
        :param buffer: Buffer size
        :type buffer: int
        :param devicename: Device name
        :type devicename: NoneType, basestring
        :param allowedchanges: Convert the samples at runtime
        :type allowedchanges: bool
        """
        assert isinstance(uniquechannel, bool)
        assert isinstance(frequency, int)
        assert isinstance(size, int)
        assert isinstance(channels, int)
        assert isinstance(buffer, int)
        assert isinstance(devicename, (type(None), str))
        assert isinstance(allowedchanges, int)
        assert frequency > 0, 'frequency must be greater than zero'
        assert channels > 0, 'channels must be greater than zero'
        assert buffer > 0, 'buffer size must be greater than zero'

        # Initialize sounds if not initialized
        if _mixer.get_init() is None:
            _mixer.init(frequency=frequency,
                        size=size,
                        channels=channels,
                        buffer=buffer,
                        devicename=devicename,
                        allowedchanges=allowedchanges)

        # Channel where a sound is played
        self._channel = None
        self._uniquechannel = uniquechannel

        # Sound dict
        self._type_sounds = [
            SOUND_TYPE_CLICK_MOUSE,
            SOUND_TYPE_CLOSE_MENU,
            SOUND_TYPE_ERROR,
            SOUND_TYPE_EVENT,
            SOUND_TYPE_EVENT_ERROR,
            SOUND_TYPE_KEY_ADDITION,
            SOUND_TYPE_KEY_DELETION,
            SOUND_TYPE_OPEN_MENU
        ]
        self._sound = {}
        for sound in self._type_sounds:
            self._sound[sound] = {}

        # Last played song
        self._last_play = 0
        self._last_time = 0

    def get_channel(self):
        """
        Get the current channel.

        :return: Channel
        :rtype: pygame.mixer.Channel
        """
        channel = _mixer.find_channel()
        if self._uniquechannel:  # If the channel is unique
            if self._channel is None:  # If the channel has not been setted
                self._channel = channel
        else:
            self._channel = channel  # Store the avaiable channel
        return self._channel

    def set_sound(self, sound, file, volume=0.5, loops=0, maxtime=0, fade_ms=0):
        """
        Set a particular sound.

        :param sound: Sound type.
        :type sound: basestring
        :param file: Sound file
        :type file: basestring, NoneType
        :param volume: Volume of the sound, (0-1)
        :type volume: float
        :param loops: Loops of the sound
        :type loops: int
        :param maxtime: Max playing time of the sound
        :type maxtime: int, float
        :param fade_ms: Fading ms
        :type fade_ms: int, float
        :return: None
        """
        assert isinstance(sound, str)
        assert isinstance(file, (str, type(None)))
        assert isinstance(loops, int)
        assert isinstance(maxtime, (int, float))
        assert isinstance(fade_ms, (int, float))
        assert loops >= 0, 'loops count must be equal or greater than zero'
        assert maxtime >= 0, 'maxtime must be equal or greater than zero'
        assert fade_ms >= 0, 'fade_ms must be equal or greater than zero'
        assert 1 >= volume >= 0, 'volume must be between 0 and 1'

        # Check sound type is correct
        if sound not in self._type_sounds:
            raise ValueError('sound type not valid, check the manual')

        # If file is none disable the sound
        if file is None:
            self._sound[sound] = {}
            return

        # Check the file exists
        if not _path.isfile(file):
            raise FileNotFoundError('sound file "{0}" does not exist'.format(file))

        # Load the sound
        try:
            sound_data = _mixer.Sound(file=file)
        except _pygame_error:
            print('The sound format is not valid, the sound has been disabled')
            self._sound[sound] = {}
            return

        # Configure the sound
        sound_data.set_volume(volume)

        # Store the sound
        self._sound[sound] = {
            'file': sound_data,
            'path': file,
            'type': sound,
            'length': sound_data.get_length(),
            'volume': volume,
            'loops': loops,
            'maxtime': maxtime,
            'fade_ms': fade_ms,
        }

    def load_example_sounds(self, volume=0.5):
        """
        Load example sounds.

        :param volume: Volume of the sound, (0-1)
        :type volume: float
        :return: None
        """
        # Must be in the same order of types
        examples = [
            PYGAMEMENU_SOUND_EXAMPLE_CLICK_MOUSE,
            PYGAMEMENU_SOUND_EXAMPLE_CLOSE_MENU,
            PYGAMEMENU_SOUND_EXAMPLE_ERROR,
            PYGAMEMENU_SOUND_EXAMPLE_EVENT,
            PYGAMEMENU_SOUND_EXAMPLE_EVENT_ERROR,
            PYGAMEMENU_SOUND_EXAMPLE_KEY_ADDITION,
            PYGAMEMENU_SOUND_EXAMPLE_KEY_DELETION,
            PYGAMEMENU_SOUND_EXAMPLE_OPEN_MENU
        ]
        for sound in range(len(self._type_sounds)):
            self.set_sound(self._type_sounds[sound], examples[sound], volume=volume)

    def _play_sound(self, sound):
        """
        Play a sound.

        :param sound: Sound to be played
        :type sound: pygame.mixer.Sound, NoneType
        :return: None
        """
        if not sound:
            self._channel = None
            return

        # Find an avaiable channel
        channel = self.get_channel()  # This will set the channel if it's None
        if channel is None:  # The sound can't be played because all channels are busy
            return

        # Play the sound
        time = _time.time()

        # If the previous sound is the same and has not ended (max 20% overlap)
        if sound['type'] != self._last_play or time - self._last_time >= 0.2 * sound['length'] or self._uniquechannel:
            if self._uniquechannel:  # Stop the current channel if it's unique
                channel.stop()
            channel.play(sound['file'],
                         loops=sound['loops'],
                         maxtime=sound['maxtime'],
                         fade_ms=sound['fade_ms']
                         )

        # Store last execution
        self._last_play = sound['type']
        self._last_time = time

    def play_click_mouse(self):
        """
        Play click mouse sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_CLICK_MOUSE])

    def play_error(self):
        """
        Play error sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_ERROR])

    def play_event(self):
        """
        Play event sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_EVENT])

    def play_event_error(self):
        """
        Play event error sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_EVENT_ERROR])

    def play_key_add(self):
        """
        Play key addition sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_KEY_ADDITION])

    def play_key_del(self):
        """
        Play key deletion sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_KEY_DELETION])

    def play_open_menu(self):
        """
        Play open menu sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_OPEN_MENU])

    def play_close_menu(self):
        """
        Play close menu sound.
        """
        self._play_sound(self._sound[SOUND_TYPE_CLOSE_MENU])
