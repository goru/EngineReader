#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from api import utils
from api.feeds import parsers

class FeedManager(object):
    @classmethod
    def createFeed(cls, dic):
        feed = FeedModel()
        feed.fromDict(dic)
        feed.put()

        cls.updateEntries(feed)

        return feed

    @classmethod
    def getFeeds(cls):
        return FeedModel.all()

    @classmethod
    def getFeedById(cls, feedId):
        return FeedModel.get_by_id(long(feedId))

    @classmethod
    def getEntries(cls, pagingKey):
        return EntryModel.gql('WHERE pagingKey < :1 ORDER BY pagingKey DESC LIMIT 100', float(pagingKey))

    @classmethod
    def getUnreadEntries(cls, pagingKey):
        return EntryModel.gql('WHERE pagingKey < :1 AND read = :2 ORDER BY pagingKey DESC LIMIT 100', float(pagingKey), False)

    @classmethod
    def getEntriesByFeed(cls, feed, pagingKey):
        return EntryModel.gql('WHERE ANCESTOR IS :1 AND pagingKey < :2 ORDER BY pagingKey DESC LIMIT 100', feed, float(pagingKey))

    @classmethod
    def getUnreadEntriesByFeed(cls, feed, pagingKey):
        return EntryModel.gql('WHERE ANCESTOR IS :1 AND pagingKey < :2 AND read = :3 ORDER BY pagingKey DESC LIMIT 100', feed, float(pagingKey), False)

    @classmethod
    def getEntryById(cls, feedId, entryId):
        feed = cls.getFeedById(feedId)
        if not feed:
            return None

        return EntryModel.get_by_key_name(entryId, parent=feed)

    @classmethod
    def setEntryStatus(cls, entry, status):
        entry.read = status
        entry.put()

        if entry.read:
            entry.feed.unread -= 1
        else:
            entry.feed.unread += 1
        entry.feed.put()

    @classmethod
    def updateEntries(cls, feed):
        xml = utils.openUrl(feed.url)
        if not xml:
            return

        dom = utils.parseXmlString(xml)
        parser = parsers.FeedParserFactory.create(dom)

        pagingKey = 0
        for entryDict in parser.entries():
            key = entryDict['key']

            entry = EntryModel.get_by_key_name(key, parent=feed)
            if not entry:
                entry = EntryModel(parent=feed, key_name=key)
                entry.feed = feed

                feed.total += 1

            if entry.fromDict(entryDict):
                entry.read = False
                entry.setPagingKey(pagingKey)
                entry.put()

                pagingKey += 1

                feed.unread += 1

        if pagingKey > 0:
            feed.put()

class ModelBase(db.Model):
    def updateAttrFromDict(self, keys, dic):
        updateRequired = False

        for key in keys:
            if getattr(self, key) != dic[key]:
                if key == 'title':
                    value = dic[key].replace('\n', '').replace('\r', '')
                else:
                    value = dic[key]
                setattr(self, key, value)
                updateRequired = True

        return updateRequired

class FeedModel(ModelBase):
    title = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    total = db.IntegerProperty(default=0)
    unread = db.IntegerProperty(default=0)

    def fromDict(self, dic):
        return self.updateAttrFromDict(['title', 'url'], dic)

    def toDict(self):
        return {'title': self.title,
                'url': self.url,
                'created': utils.dateTimeToUnix(self.created),
                'modified': utils.dateTimeToUnix(self.modified),
                'total': self.total,
                'unread': self.unread,
                'id': self.key().id()}

class EntryModel(ModelBase):
    feed = db.ReferenceProperty(FeedModel)
    title = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    description = db.TextProperty()
    read = db.BooleanProperty(default=False)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    pagingKey = db.FloatProperty()

    def setPagingKey(self, key):
        left = float(utils.currentUnix())
        right = float(key) / 1000000
        self.pagingKey = left + right

    def fromDict(self, dic):
        return self.updateAttrFromDict(['title', 'url', 'description'], dic)

    def toDict(self):
        return {'title': self.title,
                'url': self.url,
                'description': self.description,
                'read': self.read,
                'created': utils.dateTimeToUnix(self.created),
                'modified': utils.dateTimeToUnix(self.modified),
                'pagingKey': self.pagingKey,
                'id': self.key().name(),
                'feedId': self.feed.key().id()}
