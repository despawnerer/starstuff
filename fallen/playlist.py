# -*- coding: utf-8 -*-

import xmmsclient
from gi.repository import GObject

from fallen.library import Library, Track
from fallen.connections import connection_property, result_handler


class Playlist(GObject.GObject):

    __gsignals__ = {
        'entries-list': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, []),
        'position-change': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                            [GObject.TYPE_INT]),
        'clear': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, []),
        'entry-remove': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                         [GObject.TYPE_INT]),
        'entry-insert': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                         [GObject.TYPE_PYOBJECT, GObject.TYPE_INT]),
        'entry-move': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                       [GObject.TYPE_INT, GObject.TYPE_INT]),
    }

    server = connection_property('player')

    def __new__(cls, name):
        library = Library()
        if name not in library.playlists:
            playlist = GObject.GObject.__new__(cls) # temporary strong ref
            playlist.setup(name)
            library.playlists[name] = playlist
        return library.playlists[name]

    def __init__(self, name):
        GObject.GObject.__init__(self)

    def setup(self, name):
        self.name = name
        self.entries = []
        self.position = 0
        self.server.playlist_list_entries(name, self.__handle_list_entries)
        self.server.playlist_current_pos(name, self.__handle_current_pos)

    # -------------------------------------------------------------------------

    @result_handler
    def __handle_list_entries(self, entries):
        del self.entries[:]
        for id in entries:
            self.entries.append(Track(id))
        self.emit('entries-list')

    # -------------------------------------------------------------------------

    @result_handler
    def __handle_current_pos(self, data):
        position = data['position']
        self.emit('position-change', position)

    def do_position_change(self, position):
        self.position = position

    # -------------------------------------------------------------------------

    def _change(self, data):
        assert data['name'] == self.name
        action = data['type']
        if action == xmmsclient.PLAYLIST_CHANGED_CLEAR:
            self.emit('clear')
        elif action == xmmsclient.PLAYLIST_CHANGED_REMOVE:
            position = data['position']
            self.emit('entry-remove', position)
        elif action in [xmmsclient.PLAYLIST_CHANGED_INSERT,
                        xmmsclient.PLAYLIST_CHANGED_ADD]:
            position = data['position']
            id = data['id']
            track = Track(id)
            self.emit('entry-insert', track, position)
        elif action == xmmsclient.PLAYLIST_CHANGED_MOVE:
            position = data['position']
            newposition = data['newposition']
            self.emit('entry-move', position, newposition)

    def do_clear(self):
        del self.entries[:]

    def do_entry_remove(self, position):
        del self.entries[position]

    def do_entry_insert(self, track, position):
        self.entries.insert(position, track)

    def do_entry_move(self, position, newposition):
        track = self.entries.pop(position)
        self.entries.insert(newposition, track)

