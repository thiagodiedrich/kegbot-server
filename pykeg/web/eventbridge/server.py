# Copyright 2014 Bevbot LLC, All Rights Reserved
#
# This file is part of the Pykeg package of the Kegbot project.
# For more information on Pykeg or Kegbot, see http://kegbot.org/
#
# Pykeg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Pykeg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pykeg.  If not, see <http://www.gnu.org/licenses/>.

from pykeg.core import importhacks
from pykeg.web.eventbridge.common import *

import tornado.ioloop
import tornado.web
import sockjs.tornado
import tornadoredis
import tornadoredis.pubsub
import gflags

gflags.DEFINE_integer('eventbridge_port', 4041,
    'Server port for Eventbridge.')

FLAGS = gflags.FLAGS

subscriber = tornadoredis.pubsub.SockJSSubscriber(tornadoredis.Client())

class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('index.html')


class ClientHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the chatroom page"""
    def get(self):
        self.render('static/client.html')


class KegbotSocketConnection(sockjs.tornado.SockJSConnection):
    """Chat connection implementation"""
    # Class level variable
    participants = set()

    def on_open(self, info):
        self.participants.add(self)
        subscriber.subscribe(FLAGS.eventbridge_channel_name, self)

    def on_message(self, message):
        # Ignore it, for now.
        pass

    def on_close(self):
        self.participants.remove(self)
        subscriber.unsubscribe(FLAGS.eventbridge_channel_name, self)


if __name__ == "__main__":
    import logging
    logging.getLogger().setLevel(logging.DEBUG)

    # 1. Create chat router
    ChatRouter = sockjs.tornado.SockJSRouter(KegbotSocketConnection, '/events')

    # 2. Create Tornado application
    app = tornado.web.Application(
            [(r"/client", ClientHandler)] +
            ChatRouter.urls
    )

    # 3. Make Tornado app listen on port 8080
    app.listen(FLAGS.eventbridge_port)

    # 4. Start IOLoop
    tornado.ioloop.IOLoop.instance().start()
