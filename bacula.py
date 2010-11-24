#!/usr/bin/env python
#
# Copyright 2009 Facebook
# Copyright 2010 Wireless Generation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.database

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="bacula database host")
define("mysql_database", default="bacula", help="bacula database name")
define("mysql_user", default="bacula", help="bacula database user")
define("mysql_password", default="", help="bacula database password")

class Bacula(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", HomeHandler)]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                ui_modules={"MediaModule": MediaModule},
                xsrf_cookies=True,
                cookie_secret="11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo="
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        
        # Have one global connection to the blog DB across all handlers
        self.db = tornado.database.Connection(host=options.mysql_host, database=options.mysql_database, user=options.mysql_user, password=options.mysql_password)

#
# Model
#
class Media(object):
    def __init__(self, name, status, last_written):
        self.name = name
        self.status = status
        self.last_written = last_written

class Tape(Media):
    def __init__(self, name, status, last_written, inchanger, slot):
        Media.__init__(self, name, status, last_written)
        assert inchanger in (True, False)
        self.inchanger = inchanger
        assert slot >= 0
        self.slot = slot

#
# UI Modules
#
class MediaModule(tornado.web.UIModule):
    def render(self, media):
        """
        """
        return self.render_string("module-media.html", media=media)

#
# Handlers
#
class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

class HomeHandler(BaseHandler):
    def get(self):
        media = [Tape(x["VolumeName"], x["VolStatus"], x["LastWritten"], x["InChanger"], x["Slot"]) \
            for x in self.db.query("select VolumeName, VolStatus, LastWritten, InChanger, Slot from Media where LastWritten < date_sub(current_date(), interval 90 day)")]
        self.render("home.html", title="Home", media=media)

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(Bacula())
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
