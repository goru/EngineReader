#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

import os

import utils

class MainPage(webapp.RequestHandler):
    def get(self):
        feedsBody = utils.openUrl('http://127.0.0.1:8080/api/feeds/')
        feedsObj = utils.loadsJSON(feedsBody)

        feeds = []
        for feedObj in feedsObj['feeds']:
            feedBody = utils.openUrl('http://127.0.0.1:8080/api/feeds/' + str(feedObj['id']) + '/unread')
            feeds.append(utils.loadsJSON(feedBody))

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {'feeds': feeds}))

application = webapp.WSGIApplication(
    [('/', MainPage)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
