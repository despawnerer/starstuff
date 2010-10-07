# -*- coding: utf-8 -*-

import xmmsclient
from gi.repository import GObject

from fallen import library
from fallen.playlist import Playlist
from fallen.connections import Connections, connection_property, result_handler


class Player(GObject.GObject):

    __gsignals__ = {
        'status-change': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                          [GObject.TYPE_INT]),
        'track-change': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                         [GObject.TYPE_PYOBJECT]),
        'playlist-change': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                            [GObject.TYPE_PYOBJECT]),
        'playtime': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                     [GObject.TYPE_INT]),
    }

    instance = None
    server = connection_property('player')

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = GObject.GObject.__new__(cls, *args, **kwargs)
            cls.instance.setup()
        return cls.instance

    # -------------------------------------------------------------------------

    def setup(self):
        # set initial values
        self.status = None
        self.track = None
        self.playlist = None
        manager = Connections()
        manager.connect('connected', self._handle_connected)
        manager.connect('disconnected', self._handle_disconnected)
        if self.server:
            self._handle_connected(manager)

    def _handle_connected(self, manager):
        self.server.playback_current_id(self._handle_current_id)
        self.server.playback_status(self._handle_status)
        self.server.playback_playtime(self._handle_playtime)
        self.server.playlist_current_active(self._handle_playlist_loaded)
        self.server.broadcast_playback_current_id(self._handle_current_id)
        self.server.broadcast_playback_status(self._handle_status)
        self.server.signal_playback_playtime(self._handle_playtime)
        self.server.broadcast_playlist_loaded(self._handle_playlist_loaded)

    def _handle_disconnected(self, manager):
        pass

    # -------------------------------------------------------------------------

    @result_handler
    def _handle_playtime(self, time):
        self.emit('playtime', time)

    @result_handler
    def _handle_status(self, status):
        if status == self.status:
            return
        self.emit('status-change', status)

    def do_status_change(self, status):
        if not status:
            self.track = None
        self.status = status

    @result_handler
    def _handle_current_id(self, id):
        track = library.Track(id)
        self.emit('track-change', track)

    def do_track_change(self, track):
        if self.track:
            if self.track.id == id:
                return
            self.track = None
        self.track = track

    @result_handler
    def _handle_playlist_loaded(self, name):
        playlist = Playlist(name)
        self.emit('playlist-change', playlist)

    def do_playlist_change(self, playlist):
        self.playlist = playlist

    # -------------------------------------------------------------------------

    def play(self):
        self.server.playback_start()

    def pause(self):
        self.server.playback_pause()

    def stop(self):
        self.server.playback_stop()

    def jump(self, position):
        if self.status == xmmsclient.PLAYBACK_STATUS_PAUSE:
            self.play()
        self.server.playlist_set_next(position)
        self.server.playback_tickle()
        if self.status == xmmsclient.PLAYBACK_STATUS_STOP:
            self.play()

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

