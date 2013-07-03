#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import parsers
import util

class ModelBase(db.Model):
    def updateAttrFromDict(self, keys, dic):
        requireUpdate = False

        for key in keys:
            if getattr(self, key) != dic[key]:
                requireUpdate = True

            setattr(self, key, dic[key])

        return requireUpdate

class FeedModel(ModelBase):
    name = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def fromDict(self, dic):
        return self.updateAttrFromDict(['name', 'url'], dic)

    def updateEntries(self):
        xml = util.openUrl(self.url)

        entries = []
        parser = parsers.FeedParserFactory.create(xml)
        for entryDict in parser.entries():
            key = entryDict['key']

            entry = EntryModel.get_by_key_name(key, parent=self)
            if not entry:
                entry = EntryModel(parent=self, key_name=key)
                entry.feed = self
                entry.read = False

            if entry.fromDict(entryDict):
                entry.put()

            entries.append(entry)

        return entries

    def toDict(self):
        return {'name': self.name,
                'url': self.url,
                'created': util.dateTimeToUnix(self.created),
                'modified': util.dateTimeToUnix(self.modified),
                'id': self.key().id()}

class EntryModel(ModelBase):
    feed = db.ReferenceProperty(FeedModel)
    title = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    description = db.TextProperty()
    read = db.BooleanProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def fromDict(self, dic):
        return self.updateAttrFromDict(['title', 'url', 'description'], dic)

    def toDict(self):
        return {'title': self.title,
                'url': self.url,
                'description': self.description,
                'read': self.read,
                'created': util.dateTimeToUnix(self.created),
                'modified': util.dateTimeToUnix(self.modified),
                'id': self.key().name()}

class HandlerBase(webapp.RequestHandler):
    def writeNotFound(self):
        self.error(404)
        self.response.out.write(util.dumpsJSON({}))

    def getFeed(self, feedId):
        return FeedModel.get_by_id(long(feedId))

    def getEntry(self, feedId, entryId):
        feed = self.getFeed(feedId)
        if not feed:
            return None

        return EntryModel.get_by_key_name(entryId, parent=feed)

class FeedCollectionHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in FeedModel.all():
            feeds.append(feed.toDict())

        self.response.out.write(util.dumpsJSON({'feeds': feeds}))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        feed = FeedModel()
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
            feed = FeedModel()
            feed.fromDict(feedDict)
            feed.put()
            feed.updateEntries()
            feeds.append(feed.toDict())

        self.response.out.write(util.dumpsJSON({'feeds': feeds}))

class FeedUpdateHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in FeedModel.all():
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
        for entry in EntryModel.gql("WHERE ANCESTOR IS :1", feed):
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
    [('/feeds/?', FeedCollectionHandler),
     ('/feeds/import', FeedImportHandler),
     ('/feeds/update', FeedUpdateHandler),
     ('/feeds/(\d+)/?', FeedHandler),
     ('/feeds/(\d+)/(entry-[a-z0-9]+)/(read|unread)', ReadUnreadHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
