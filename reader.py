#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import time

import models
import parsers
import utils

class HandlerBase(webapp.RequestHandler):
    def writeNotFound(self):
        self.error(404)
        self.response.out.write(utils.dumpsJSON({}))

class FeedCollectionHandler(HandlerBase):
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

class FeedImportHandler(HandlerBase):
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        dom = utils.parseXmlString(utils.decodeByteString(self.request.body))
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
            entryQuery = models.FeedManager.getEntries(feed, pagingKey)
        elif action == 'unread':
            entryQuery = models.FeedManager.getUnreadEntries(feed, pagingKey)

        entries = []
        for entry in entryQuery:
            entries.append(entry.toDict())

        feedDict = feed.toDict()
        feedDict['entries'] = entries

        self.response.out.write(utils.dumpsJSON(feedDict))

class EntryReadUnreadHandler(HandlerBase):
    def post(self, feedId, entryId, action):
        self.response.headers['Content-Type'] = 'application/json'

        entry = models.FeedManager.getEntryById(feedId, entryId)
        if not entry:
            self.writeNotFound()
            return

        stat = True if action == 'read' else False
        models.FeedManager.setEntryStatus(entry, stat)

application = webapp.WSGIApplication(
    [('/api/feeds/?', FeedCollectionHandler),
     ('/api/feeds/import', FeedImportHandler),
     ('/api/feeds/update', FeedUpdateHandler),
     ('/api/feeds/(\d+)/?', FeedHandler),
     ('/api/feeds/(\d+)/(all|unread)/?', FeedEntryHandler),
     ('/api/feeds/(\d+)/(all|unread)/([0-9.]+)/?', FeedEntryHandler),
     ('/api/feeds/(\d+)/(entry-[a-z0-9]+)/(read|unread)', EntryReadUnreadHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
