#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import random
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import simplejson
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('Guestbook', guestbook_name)


# [START greeting]
class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
# [END greeting]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        random.seed(os.urandom(8))
        nonce = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for i in range(8))
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'user': user,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
            'nonce': nonce,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.headers.add("Content-Security-Policy","script-src 'nonce-%s'; object-src 'none'"%nonce)
        self.response.headers.add("Set-Cookie","__isolatedScript-foo=1;httpOnly;secure")
        self.response.write(template.render(template_values))
# [END main_page]

# [START guestbook]
class Guestbook(webapp2.RequestHandler):
    def get(self):
        if not self.request.cookies.get('__isolatedScript-foo'):
            return
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)
        self.response.write(simplejson.dumps(list({"content": g.content} for g in greetings),
                                             cls=simplejson.encoder.JSONEncoderForHTML))

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))
# [END guestbook]


# [START purge]
class Purge(webapp2.RequestHandler):
    def post(self):
        greetings_query = Greeting.query().fetch(1000, keys_only=True)
        ndb.delete_multi(list(greetings_query))
            
# [END purge]


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/guestbook', Guestbook),
    # Tasks
    ('/tasks/purge', Purge),
], debug=True)
# [END app]
