#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import models
import parsers
import util

class HandlerBase(webapp.RequestHandler):
    def writeNotFound(self):
        self.error(404)
        self.response.out.write(util.dumpsJSON({}))

    def getFeed(self, feedId):
        return models.FeedModel.get_by_id(long(feedId))

    def getEntry(self, feedId, entryId):
        feed = self.getFeed(feedId)
        if not feed:
            return None

        return models.EntryModel.get_by_key_name(entryId, parent=feed)

class FeedCollectionHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in models.FeedModel.all():
            feeds.append(feed.toDict())

        self.response.out.write(util.dumpsJSON({'feeds': feeds}))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        feed = models.FeedModel()
        feed.fromDict(util.loadsJSON(self.request.body))
        feed.put()
        feed.updateEntries()

        self.response.out.write(util.dumpsJSON(feed.toDict()))

class FeedImportHandler(HandlerBase):
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        dom = util.parseXmlString(util.decodeByteString(self.request.body))
        document = dom.documentElement
        opml = parsers.OpmlParser.create(document)

        feeds = []
        for feedDict in opml.feeds():
            feed = models.FeedModel()
            feed.fromDict(feedDict)
            feed.put()
            feed.updateEntries()
            feeds.append(feed.toDict())

        self.response.out.write(util.dumpsJSON({'feeds': feeds}))

class FeedUpdateHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in models.FeedModel.all():
            feed.updateEntries()
            feeds.append(feed.toDict())

        self.response.out.write(util.dumpsJSON({'feeds': feeds}))

class FeedHandler(HandlerBase):
    def get(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = self.getFeed(feedId)
        if not feed:
            self.writeNotFound()
            return

        entries = []
        for entry in models.EntryModel.gql("WHERE ANCESTOR IS :1", feed):
            entries.append(entry.toDict())

        self.response.out.write(util.dumpsJSON(
            {'feed': feed.toDict(),
             'entries': entries}))

    def post(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = self.getFeed(feedId)
        if not feed:
            self.writeNotFound()
            return

        if feed.fromDict(util.loadsJSON(self.request.body)):
            feed.put()

        entries = []
        for entry in feed.updateEntries():
            entries.append(entry.toDict())

        self.response.out.write(util.dumpsJSON(
            {'feed': feed.toDict(),
             'entries': entries}))

class ReadUnreadHandler(HandlerBase):
    def post(self, feedId, entryId, action):
        self.response.headers['Content-Type'] = 'application/json'

        feed = self.getEntry(feedId, entryId)
        if not feed:
            self.writeNotFound()
            return

        if action == 'read':
            feed.read = True
        elif action == 'unread':
            feed.read = False

        feed.put()

application = webapp.WSGIApplication(
    [('/api/feeds/?', FeedCollectionHandler),
     ('/api/feeds/import', FeedImportHandler),
     ('/api/feeds/update', FeedUpdateHandler),
     ('/api/feeds/(\d+)/?', FeedHandler),
     ('/api/feeds/(\d+)/entries/(entry-[a-z0-9]+)/(read|unread)', ReadUnreadHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
