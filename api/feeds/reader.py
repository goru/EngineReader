#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import time

from api import utils
from api.feeds import models, parsers

class HandlerBase(webapp.RequestHandler):
    def writeJsonResponse(self, obj):
        self.response.clear()
        self.response.set_status(200)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(utils.dumpsJSON(obj))

    def writeNoContentResponse(self):
        self.response.clear()
        self.response.set_status(204)

    def writeNotFoundResponse(self):
        self.response.clear()
        self.response.set_status(404)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(utils.dumpsJSON({}))

class FeedsHandler(HandlerBase):
    def get(self):
        feeds = []
        for feed in models.FeedManager.getFeeds():
            feeds.append(feed.toDict())

        self.writeJsonResponse({'feeds': feeds})

    def post(self):
        dic = utils.loadsJSON(utils.decodeByteString(self.request.body))
        feed = models.FeedManager.createFeed(dic)

        self.writeJsonResponse(feed.toDict())

class FeedsEntryHandler(HandlerBase):
    def get(self, action, pagingKey=None):
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

        self.writeJsonResponse({'entries': entries})

class FeedImportHandler(HandlerBase):
    def post(self):
        fileBody = self.request.get('opml')
        dom = utils.parseXmlString(utils.decodeByteString(fileBody))
        opml = parsers.OpmlParser.create(dom)

        feeds = []
        for feedDict in opml.feeds():
            feed = models.FeedManager.createFeed(feedDict)
            feeds.append(feed.toDict())

        self.writeJsonResponse({'feeds': feeds})

class FeedUpdateHandler(HandlerBase):
    def get(self):
        feeds = []
        for feed in models.FeedManager.getFeeds():
            models.FeedManager.updateEntries(feed)
            feeds.append(feed.toDict())

        self.writeJsonResponse({'feeds': feeds})

class FeedHandler(HandlerBase):
    def get(self, feedId):
        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFoundResponse()
            return

        self.writeJsonResponse(feed.toDict())

    def post(self, feedId):
        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFoundResponse()
            return

        feedDict = utils.loadsJSON(utils.decodeByteString(self.request.body))
        if feed.fromDict(feedDict):
            feed.put()

        self.writeJsonResponse(feed.toDict())

    def delete(self, feedId):
        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFoundResponse()
            return

        feeds = models.FeedManager.getAllEntriesByFeed(feed)
        if not feeds:
            self.writeNotFoundResponse()
            return

        db.delete(feeds)
            feed.delete()

        self.writeNoContentResponse()

class FeedEntryHandler(HandlerBase):
    def get(self, feedId, action, pagingKey=None):
        feed = models.FeedManager.getFeedById(feedId)
        if not feed:
            self.writeNotFoundResponse()
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

        self.writeJsonResponse({'entries': entries})

class EntryHandler(HandlerBase):
    def get(self, feedId, entryId):
        entry = models.FeedManager.getEntryById(feedId, entryId)
        if not entry:
            self.writeNotFoundResponse()
            return

        self.writeJsonResponse(entry.toDict())

    def delete(self, feedId, entryId):
        entry = models.FeedManager.getEntryById(feedId, entryId)
        if not entry:
            self.writeNotFoundResponse()
            return

        entry.delete()

        self.writeNoContentResponse()

class EntryReadUnreadHandler(HandlerBase):
    def post(self, feedId, entryId, action):
        entry = models.FeedManager.getEntryById(feedId, entryId)
        if not entry:
            self.writeNotFoundResponse()
            return

        stat = True if action == 'read' else False
        models.FeedManager.setEntryStatus(entry, stat)

        self.writeJsonResponse(entry.toDict())

application = webapp.WSGIApplication(
    [('/api/feeds/?', FeedsHandler),
     ('/api/feeds/(all|unread)/?', FeedsEntryHandler),
     ('/api/feeds/(all|unread)/([0-9.]+)/?', FeedsEntryHandler),
     ('/api/feeds/import', FeedImportHandler),
     ('/api/feeds/update', FeedUpdateHandler),
     ('/api/feeds/(\d+)/?', FeedHandler),
     ('/api/feeds/(\d+)/(all|unread)/?', FeedEntryHandler),
     ('/api/feeds/(\d+)/(all|unread)/([0-9.]+)/?', FeedEntryHandler),
     ('/api/feeds/(\d+)/(entry-[a-z0-9]+)/?', EntryHandler),
     ('/api/feeds/(\d+)/(entry-[a-z0-9]+)/(read|unread)', EntryReadUnreadHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
