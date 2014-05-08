from google.appengine.api import users

import webapp2


class MainPage(webapp2.RequestHandler):

    def get(self):
        # [START get_current_user]
        # Checks for active Google account session
        user = users.get_current_user()
        # [END get_current_user]

        # [START if_user]
        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.write('Hello, ' + user.nickname())
        # [END if_user]
        # [START if_not_user]
        else:
            self.redirect(users.create_login_url(self.request.uri))
        # [END if_not_user]


application = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)
