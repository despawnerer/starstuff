# -*- coding: utf-8 -*-

import gobject
import xmmsclient
from Fallen import library
from Fallen.connections import connection_property, result_handler

class Playlist(gobject.GObject):

    __gsignals__ = {
        'entries-list': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'position-change': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        'clear': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
        'entry-remove': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
    }

    server = connection_property('player')
    entries = []
    position = 0

    def __new__(cls, name):
        lib = library.Library()
        if name not in lib.playlists:
            obj = gobject.GObject.__new__(cls) # temporary strong ref
            obj.server.playlist_list_entries(name, obj._handle_list_entries)
            obj.server.playlist_current_pos(name, obj._handle_current_pos)
            lib.playlists[name] = obj
        return lib.playlists[name]

    def __init__(self, name):
        gobject.GObject.__init__(self)
        self.name = name

    @result_handler
    def _handle_list_entries(self, entries):
        del self.entries[:]
        for id in entries:
            self.entries.append(library.Track(id))
        self.emit('entries-list')

    @result_handler
    def _handle_current_pos(self, data):
        position = data['position']
        self._change_position(position)

    def _change_position(self, position):
        self.emit('position-change', position)
        self.position = position

    def _change(self, data):
        assert data['name'] == self.name
        action = data['type']
        if action == xmmsclient.PLAYLIST_CHANGED_CLEAR:
            self.emit('clear')
            del self.entries[:]
            return
        elif action == xmmsclient.PLAYLIST_CHANGED_REMOVE:
            position = data['position']
            self.emit('entry-remove', position)
            del self.entries[position]

