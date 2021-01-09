# -*- coding: utf-8 -*-

from .abstract import ContentProvider
from .theaudiodb import TheAudioDB
from .fanarttv import FanartTV
from .duckgo import DuckGo
from .local import Local

__all__ = ['ContentProvider', 'TheAudioDB', 'FanartTV', 'DuckGo', 'Local']
