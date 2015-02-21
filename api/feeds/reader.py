#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import time

from api import utils
from api.feeds import models, parsers

class HandlerBase(webapp.RequestHandler):
    def writeNotFound(self):
        self.error(404)
        self.response.out.write(utils.dumpsJSON({}))

class FeedsHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in models.FeedManager.getFeeds():
            feeds.append(feed.toDict())

        self.response.out.write(utils.dumpsJSON({'feeds': feeds}))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        dic = utils.loadsJSON(utils.decodeByteString(self.request.body))
        feed = models.FeedManager.createFeed(dic)

        self.response.out.write(utils.dumpsJSON(feed.toDict()))

class FeedsEntryHandler(HandlerBase):
    def get(self, action, pagingKey=None):
        self.response.headers['Content-Type'] = 'application/json'

        if not pagingKey:
            pagingKey = utils.currentUnix()

        queryResult = []
        if action == 'all':
            queryResult = models.FeedManager.getEntries(pagingKey)
        elif action == 'unread':
            queryResult = models.FeedManager.getUnreadEntries(pagingKey)

        entries = []
        for entry in queryResult:
            entries.append(entry.toDict())

        self.response.out.write(utils.dumpsJSON({'entries': entries}))

class FeedImportHandler(HandlerBase):
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        fileBody = self.request.get('opml')
        dom = utils.parseXmlString(utils.decodeByteString(fileBody))
        opml = parsers.OpmlParser.create(dom)

        feeds = []
        for feedDict in opml.feeds():
            feed = models.FeedManager.createFeed(feedDict)
            feeds.append(feed.toDict())

        self.response.out.write(utils.dumpsJSON({'feeds': feeds}))

class FeedUpdateHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in models.FeedManager.getFeeds():
            models.FeedManager.updateEntries(feed)
            feeds.append(feed.toDict())

        self.response.out.write(utils.dumpsJSON({'feeds': feeds}))

class FeedHandler(HandlerBase):
    def get(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFound()
            return

        self.response.out.write(utils.dumpsJSON(feed.toDict()))

    def post(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFound()
            return

        feedDict = utils.loadsJSON(utils.decodeByteString(self.request.body))
        if feed.fromDict(feedDict):
            feed.put()

        self.response.out.write(utils.dumpsJSON(feed.toDict()))

class FeedEntryHandler(HandlerBase):
    def get(self, feedId, action, pagingKey=None):
        self.response.headers['Content-Type'] = 'application/json'

        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFound()
            return

        if not pagingKey:
            pagingKey = utils.currentUnix()

        entryQuery = []
        if action == 'all':
            entryQuery = models.FeedManager.getEntriesByFeed(feed, pagingKey)
        elif action == 'unread':
            entryQuery = models.FeedManager.getUnreadEntriesByFeed(feed, pagingKey)

        entries = []
        for entry in entryQuery:
            entries.append(entry.toDict())

        self.response.out.write(utils.dumpsJSON({'entries': entries}))

class EntryReadUnreadHandler(HandlerBase):
    def post(self, feedId, entryId, action):
        self.response.headers['Content-Type'] = 'application/json'

        entry = models.FeedManager.getEntryById(feedId, entryId)
        if not entry:
            self.writeNotFound()
            return

        stat = True if action == 'read' else False
        models.FeedManager.setEntryStatus(entry, stat)

        self.response.out.write(utils.dumpsJSON(entry.toDict()))

application = webapp.WSGIApplication(
    [('/api/feeds/?', FeedsHandler),
     ('/api/feeds/(all|unread)/?', FeedsEntryHandler),
     ('/api/feeds/(all|unread)/([0-9.]+)/?', FeedsEntryHandler),
     ('/api/feeds/import', FeedImportHandler),
     ('/api/feeds/update', FeedUpdateHandler),
     ('/api/feeds/(\d+)/?', FeedHandler),
     ('/api/feeds/(\d+)/(all|unread)/?', FeedEntryHandler),
     ('/api/feeds/(\d+)/(all|unread)/([0-9.]+)/?', FeedEntryHandler),
     ('/api/feeds/(\d+)/(entry-[a-z0-9]+)/(read|unread)', EntryReadUnreadHandler)],
    debug=False)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
