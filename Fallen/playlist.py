# -*- coding: utf-8 -*-

import gobject
from Fallen import library
from Fallen.connections import connection_property, result_handler

class Playlist(gobject.GObject):

    __gsignals__ = {
        'entries-list': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, []),
    }

    server = connection_property('player')

    def __init__(self, name):
        gobject.GObject.__init__(self)
        self.name = name
        self.entries = []
        self.server.playlist_list_entries(name, self._handle_list_entries)

    @result_handler
    def _handle_list_entries(self, entries):
        del self.entries[:]
        for id in entries:
            self.entries.append(library.Track(id))
        self.emit('entries-list')

