import os
import urllib.parse

from flask import Flask, render_template, request, redirect
from google.appengine.api import users, wrap_wsgi_app
from google.cloud import ndb

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
client = ndb.Client()

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    return ndb.Key('Guestbook', guestbook_name)

class Author(ndb.Model):
    identity = ndb.StringProperty()
    email = ndb.StringProperty()

class Greeting(ndb.Model):
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

@app.route('/')
def main_page():
    guestbook_name = request.args.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
    
    with client.context():
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

    user = users.get_current_user()
    if user:
        url = users.create_logout_url(request.url)
        url_linktext = 'Logout'
    else:
        url = users.create_login_url(request.url)
        url_linktext = 'Login'

    template_values = {
        'user': user,
        'greetings': greetings,
        'guestbook_name': urllib.parse.quote_plus(guestbook_name),
        'url': url,
        'url_linktext': url_linktext,
    }

    return render_template('index.html', **template_values)

@app.route('/sign', methods=['POST'])
def sign_guestbook():
    guestbook_name = request.args.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
    
    with client.context():
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        user = users.get_current_user()
        if user:
            greeting.author = Author(
                identity=user.user_id(),
                email=user.email())

        greeting.content = request.form.get('content')
        greeting.put()

    return redirect('/?' + urllib.parse.urlencode({'guestbook_name': guestbook_name}))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
