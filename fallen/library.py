# -*- coding: utf-8 -*-

from weakref import WeakValueDictionary

from xmmsclient import collections
from gi.repository import GObject

from fallen.connections import Connections, connection_property, result_handler


class Library(object):
    
    instance = None
    server = connection_property('library')

    tracks = WeakValueDictionary()
    playlists = WeakValueDictionary()

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
            cls.instance.setup()
        return cls.instance
        
    def setup(self):
        connections = Connections()
        connections.connect('connected', self.__handle_connect)
        connections.connect('disconnected', self.__handle_disconnect)
        if self.server:
            self.__handle_connect()

    def __handle_connect(self, *args):
        self.server.broadcast_medialib_entry_changed(self.__handle_entry_changed)
        self.server.broadcast_playlist_current_pos(self.__handle_playlist_pos)
        self.server.broadcast_playlist_changed(self.__handle_playlist_changed)

    def __handle_disconnect(self, *args):
        pass

    # -------------------------------------------------------------------------

    @result_handler
    def __handle_entry_changed(self, id):
        self.request_info(id)

    @result_handler
    def __handle_info(self, info):
        info = TrackInfo(info)
        id = info['id']
        if id in self.tracks:
            track = self.tracks[id]
            if track.info != info:
                track.emit('update', info)

    # -------------------------------------------------------------------------

    @result_handler
    def __handle_playlist_pos(self, data):
        name = data['name']
        position = data['position']
        if name in self.playlists:
            self.playlists[name].emit('position-change', position)

    @result_handler
    def __handle_playlist_changed(self, data):
        name = data['name']
        if name in self.playlists:
            self.playlists[name]._change(data)

    # -------------------------------------------------------------------------

    def request_info(self, id):
        self.server.medialib_get_info(id, self.__handle_info)


# -----------------------------------------------------------------------------


class Collectable(GObject.GObject):

    def __add__(self, y):
        if isinstance(y, Item):
            group = CollectableGroup([self, y])
            return group
        elif isinstance(y, CollectableGroup):
            if self in y:
                return y
            group = CollectableGroup([self])
            group += y
            return group
        else:
            raise TypeError

    def get_collection(self):
        raise NotImplemented


class CollectableGroup(Collectable):

    def __init__(self, items=None):
        self.__items = items if items else []

    def __getitem__(self, i):
        return self.__items[i]

    def __len__(self):
        return len(self.__items)

    def __add__(self, y):
        if isinstance(y, CollectableGroup):
            group = self.clone()
            for item in y:
                if item not in group:
                    group.append(item)
            return group
        elif isinstance(y, Item):
            group = self.clone()
            if item not in group:
                group.append(y)
            return group
        else:
            raise TypeError

    def clone(self):
        group = CollectableGroup()
        group.__dict__ = self.__dict__
        return group

    def append(self, x):
        if isinstance(x, Item):
            return self.__items.append(x)
        raise TypeError

    def get_collection(self):
        collection = None
        for item in self.__items:
            collection = collections.Union(collection, item.get_collection())
        return collection


# -----------------------------------------------------------------------------


class Item(Collectable):

    __gsignals__ = {
        'filled': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                   [GObject.TYPE_PYOBJECT])
    }

    server = connection_property('library')

    def __init__(self, **keys):
        GObject.GObject.__init__(self)
        self.keys = keys

    def __repr__(self):
        pairs = [ '%s="%s"' % (key, self.keys[key]) for key in self.keys ]
        desc = unicode(' && '.join(pairs)).encode('utf-8') # fuck yeah
        return "<Item %s>" % desc

    # -------------------------------------------------------------------------

    @result_handler
    def _handle_fill(self, infos):
        items = CollectableGroup([self.item(**info) for info in infos])
        self.emit('filled', items)

    # -------------------------------------------------------------------------

    def item(self, **keys):
        if 'id' not in keys:
            item = Item(**self.keys)
            item.keys.update(keys)
            return item
        else:
            return Track(keys['id'])

    def get_collection(self):
        collection = collections.Universe()
        for key in self.keys:
            value = self.keys[key]
            if value != None: # we shouldn't consider "" to be a missing value
                collection = collections.Equals(collection, field=key, value=value)
            else:    # handle the "unknown" case
                collection = collections.Complement(collections.Has(collection, field=key))
        return collection

    def fill(self, *fields):
        collection = self.get_collection()
        self.server.coll_query_infos(collection, list(fields), 0, 0, [], [], self._handle_fill)


# -----------------------------------------------------------------------------


class TrackInfo(dict):

    def __init__(self, info):
        dict.__init__(self)
        # sanitize the info xmms2 gives us
        for group, key in info:
            self[key] = info[key]

    def __getitem__(self, item): 
        return self.has_key(item) and dict.__getitem__(self, item) or "n/a"


class Track(Collectable):

    __gsignals__ = {
        'update': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE,
                   [GObject.TYPE_PYOBJECT]),
    }

    def __new__(cls, id):
        library = Library()
        if id not in library.tracks:
            track = GObject.GObject.__new__(cls) # temporary strong ref
            track.id = id
            track.info = None
            library.tracks[id] = track
            library.request_info(id)
        return library.tracks[id]

    def __init__(self, id):
        Collectable.__init__(self)

    def __repr__(self):
        return "<Track #%d>" % self.id

    # -------------------------------------------------------------------------

    def do_update(self, info):
        self.info = info

    # -------------------------------------------------------------------------

    def get_collection(self):
        return collections.Equals(collection, field="id", value=self.id)

