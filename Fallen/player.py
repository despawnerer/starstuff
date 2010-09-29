# -*- coding: utf-8 -*-

import gobject
import xmmsclient
from Fallen import library
from Fallen.connections import Connections, connection_property, result_handler


class Player(gobject.GObject):

    __gsignals__ = {
        'status-change': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
        'track-changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'playlist-loaded': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_PYOBJECT]),
        'playtime': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, [gobject.TYPE_INT]),
    }

    instance = None

    current = None
    status = None

    server = connection_property('player')

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = gobject.GObject.__new__(cls, *args, **kwargs)
            cls.instance.setup()
        return cls.instance

    # ------------------------------------------------------------------

    def setup(self):
        manager = Connections()
        manager.connect('connected', self._handle_connected)
        manager.connect('disconnected', self._handle_disconnected)
        if self.server:
            self._handle_connected(manager)

    def _handle_connected(self, manager):
        self.server.playback_current_id(self._handle_current_id)
        self.server.playback_status(self._handle_status)
        self.server.playback_playtime(self._handle_playtime)
        self.server.broadcast_playback_current_id(self._handle_current_id)
        self.server.broadcast_playback_status(self._handle_status)
        self.server.signal_playback_playtime(self._handle_playtime)

    def _handle_disconnected(self, manager):
        pass

    # ------------------------------------------------------------------

    @result_handler
    def _handle_playtime(self, time):
        self.emit('playtime', time)

    @result_handler
    def _handle_status(self, status):
        if status == self.status:
            return
        if not status:
            self.current = None
        self.emit('status-change', status)
        self.status = status

    @result_handler
    def _handle_current_id(self, id):
        track = library.Track(id)
        self.emit('track-changed', track)
        if self.current:
            if self.current.id == id:
                return
            self.current = None
        self.current = track

    # ------------------------------------------------------------------

    def play(self):
        self.server.playback_start()

    def pause(self):
        self.server.playback_pause()

    def stop(self):
        self.server.playback_stop()

    def jump_rel(self, delta):
        if self.status == xmmsclient.PLAYBACK_STATUS_PAUSE:
            self.play()
        self.server.playlist_set_next_rel(delta)
        self.server.playback_tickle()
        if self.status == xmmsclient.PLAYBACK_STATUS_STOP:
            self.play()

    def next(self):
        self.jump_rel(1)

    def prev(self):
        self.jump_rel(-1)

