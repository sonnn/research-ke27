import time
import json
import os.path
from crawler import Crawler
from gevent import monkey; monkey.patch_all()
from socketio.namespace import BaseNamespace
from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.mixins import RoomsMixin, BroadcastMixin
# init crawler
# crwl = Crawler(config_json)
# crwl.spawn_spidies()

CRWL_PORT = 8000

class CrwlNamespace(BaseNamespace):

    def on_connect(self):
        # Just have them join a default-named room
        self.join('main_room')

    def recv_disconnect(self):
        # Remove nickname from the list.
        self.disconnect(silent=True)

    def on_message(self, msg):
        self.emit_to_room('main_room', 'msg_to_room',
            self.socket.session, msg)

    def recv_message(self, message):
        print "PING!!!", message

class Application(object):
    def __init__(self):
        self.buffer = []
        self.request = {}

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/')

        if not path:
            start_response('200 OK', [('Content-Type', 'text/html')])
            return open('frontend/index.html', 'r').read()

        if path.startswith('frontend/'):
            try:
                data = open(path).read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            socketio_manage(environ, {'': CrwlNamespace}, self.request)
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


SocketIOServer(('0.0.0.0', CRWL_PORT), Application(),
    resource="socket.io", policy_server=False).serve_forever()
