import sys

from gi.repository import GObject
from gi.repository import Gtk

from fallen.connections import Connections
from fallen.player import Player
from fallen import library


class Fallen:

    """
    Main Fallen application class
    """

    def __init__(self):

        # load the ui
        self.builder = Gtk.Builder()
        self.builder.add_from_file('Fallen/ui/main.ui')

        # set the window up
        window = self.builder.get_object('main-window')
        window.show_all()
        window.connect('destroy', self._handle_window_destroy)

        # player controls
        self.play = self.builder.get_object('play')
        self.play.connect('activate', self._handle_play)
        self.next = self.builder.get_object('next')
        self.next.connect('activate', lambda action: self.player.next());
        self.prev = self.builder.get_object('previous')
        self.prev.connect('activate', lambda action: self.player.prev());

        # track title label and timeline controls
        self.tracklabel = self.builder.get_object('track-name')
        self.playtime = self.builder.get_object('playtime')

        # playlist
        self.playliststatus = self.builder.get_object('playlist-status')
        self.playlistview = self.builder.get_object('playlist-view')
        self.playlistview.connect('row-activated',
                                  self._handle_playlistview_row_activated)
        self.playlist = self.builder.get_object('playlist')

        # our cool classes to handle xmms
        self.player = Player()
        self.connections = Connections()
        self.connections.bring_up()

        # handle player events from xmms
        self.player.connect('status-change', self._handle_status_change)
        self.player.connect('track-change', self._handle_track_change)
        self.player.connect('playlist-change', self._handle_playlist_change)
        self.player.connect('playtime', self._handle_playtime)

        # use gobject mainloop
        self.mainloop = GObject.MainLoop()

    # -------------------------------------------------------------------------

    def _handle_window_destroy(self, window):
        self.mainloop.quit()

    # Current track UI --------------------------------------------------------

    def _handle_play(self, action):
        self.player.play() if action.get_active() else self.player.pause()

    def _handle_status_change(self, player, status):
        self.play.handler_block_by_func(self._handle_play)
        self.play.set_active(status == 1) # if playing
        self.play.handler_unblock_by_func(self._handle_play)
        self.tracklabel.set_sensitive(status != 0) # if not stopped
        stocks = {
            0: 'gtk-media-stop',
            1: 'gtk-media-play',
            2: 'gtk-media-pause'
        }
        self.playliststatus.set_property('stock-id', stocks[status])
        self.playlistview.queue_draw() # FIXME: I don't like this
        if status == 0:
            self.tracklabel.set_text("Not playing")
            self.playtime.set_value(0)

    def _handle_playtime(self, player, time):
        self.playtime.set_value(int(time))

    def _handle_track_change(self, player, track):
        if track.info:
            self._handle_current_track_metadata(track)
        if self.player.track:
            self.player.track.disconnect_by_func(
                self._handle_current_track_metadata)
        track.connect('updated', self._handle_current_track_metadata)

    def _handle_current_track_metadata(self, track):
        label = '<b>%(title)s</b> by %(artist)s' % track.info
        self.tracklabel.set_markup(label.replace('&', '&amp;').encode('utf-8'))
        self.playtime.set_upper(int(track.info['duration']))

    # Playlist UI -------------------------------------------------------------

    def _handle_playlistview_row_activated(self, view, path, column):
        position = int(path.to_string()) # FIXME: not good, should use indices
        self.player.jump(position)

    def _handle_playlist_change(self, player, playlist):
        playlist.connect('entries-list', self._handle_playlist_entries_list)
        playlist.connect('position-change',
                         self._handle_playlist_position_change)
        playlist.connect('clear', self._handle_playlist_clear)
        playlist.connect('entry-remove', self._handle_playlist_entry_remove)
        playlist.connect('entry-insert', self._handle_playlist_entry_insert)
        playlist.connect('entry-move', self._handle_playlist_entry_move)

    def _handle_playlist_entries_list(self, playlist):
        self.playlist.clear()
        for index, track in enumerate(playlist.entries):
            row = self.playlist.append([False, None, None, None, None, None,
                                        None])
            if track.info:
                self._handle_playlist_track_metadata(track, row)
            track.connect('updated', self._handle_playlist_track_metadata, row)

    def _handle_playlist_track_metadata(self, track, row):
        for index, key in enumerate(('title', 'artist', 'date', 'genre',
                                     'publisher')):
            # metadata starts from the third row
            self.playlist.set_value(row, index + 2,
                                    track.info[key].encode('utf-8'))

    def _handle_playlist_position_change(self, playlist, position):
        valid, row = self.playlist.get_iter_from_string(str(playlist.position))
        if valid:
            self.playlist.set_value(row, 0, False) # "nowplaying" row
            self.playlist.set_value(row, 1, 400) # normal font weight
        valid, row = self.playlist.get_iter_from_string(str(position))
        if valid:
            self.playlist.set_value(row, 0, True)
            self.playlist.set_value(row, 1, 600) # bold

    def _handle_playlist_clear(self, playlist):
        self.playlist.clear()

    def _handle_playlist_entry_remove(self, playlist, position):
        res, row = self.playlist.get_iter_from_string(str(position))
        self.playlist.remove(row)

    def _handle_playlist_entry_insert(self, playlist, track, position):
        valid, row = self.playlist.get_iter_from_string(str(position))
        if valid:
            row = self.playlist.insert_before(row)
        else:
            row = self.playlist.append([False, None, None, None, None, None, None])
        if track.info:
            self._handle_playlist_track_metadata(track, row)
        track.connect('updated', self._handle_playlist_track_metadata, row)

    def _handle_playlist_entry_move(self, playlist, position, newposition):
        valid, row = self.playlist.get_iter_from_string(str(position))
        valid, newrow = self.playlist.get_iter_from_string(str(newposition))
        if position < newposition:
            self.playlist.move_after(row, newrow)
        else:
            self.playlist.move_before(row, newrow)

def main():
	fallen = Fallen()
	fallen.mainloop.run()

if __name__ == "__main__":
    main()
