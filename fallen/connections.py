# -*- coding: utf-8 -*-

from xmmsclient import XMMS
from gi.repository import GObject


def result_handler(proc):
    def wrapper(obj, result):
        result = result.value()
        proc(obj, result)
    return wrapper


def connection_property(name):
    def getter(obj):
        manager = Connections()
        return manager[name]
    return property(getter)


class Connections(GObject.GObject):
    
    __gsignals__ = {
        'connected': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, []),
        'disconnected': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [])
    }
    
    instance = None
    up = False
    connections = dict()

    path = None
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = GObject.GObject.__new__(cls, *args, **kwargs)
        return cls.instance
        
    def __getitem__(self, handle):
        if not self.up:
            return None
        if not handle in self.connections:
            self.__connect(handle)
        return self.connections[handle]
        
    def __connect(self, handle):
        c = Connection()
        c.connect(self.path)
        self.connections[handle] = c
        
    def __disconnect(self, handle):
        c = self.connections[handle]
        c.disconnect()
        self.connections[handle] = None        
       
    def bring_up(self):
        for handle in self.connections:
            self.__connect(handle)
        self.up = True
        self.emit('connected')
            
    def bring_down(self):
        for handle in self.connections:
            self.__disconnect(handle)
        self.up = False
        self.emit('disconnected')
        

class Connection(XMMS):

    def connect(self, *args, **kwargs):
        XMMS.connect(self, *args, **kwargs)
        self.set_need_out_fun(self.__need_out)
        self.__fd = self.get_fd()
        self.__has_out = False
        self.__out = 0
        self.__in = GObject.io_add_watch(self.__fd, GObject.IO_IN,
                                         self.__handle_in)
                                         
    def disconnect(self):
        # FIXME: Doesn't work due to a refcount bug in xmms2 bindings
        if self.__in: GObject.source_remove(self.__in)
        if self.__out: GObject.source_remove(self.__out)
        self.set_need_out_fun(None)
        del self.__out, self.__in, self.__has_out, self.__fd

    # -------------------------------------------------------------------------
                                                                                 
    def __need_out(self, need):
        if self.want_ioout() and not self.__has_out:
            self.__has_out = True
            self.__out = GObject.io_add_watch(self.__fd, GObject.IO_OUT,
                                              self.__handle_out)

    def __handle_in(self, source, condition):
        if condition == GObject.IO_IN:
            self.ioin()
        return True

    def __handle_out(self, source, condition):
        if condition == GObject.IO_OUT:
            self.ioout()
        self.__has_out = self.want_ioout()
        return self.__has_out

