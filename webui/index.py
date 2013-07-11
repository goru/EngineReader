#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class WebUIHandler(webapp.RequestHandler):
    def get(self):
        self.redirect('/index.html')

application = webapp.WSGIApplication(
    [('/', WebUIHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
