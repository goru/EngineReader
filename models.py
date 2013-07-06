#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import parsers
import util

class ModelBase(db.Model):
    def updateAttrFromDict(self, keys, dic):
        updateRequired = False

        for key in keys:
            if getattr(self, key) != dic[key]:
                setattr(self, key, dic[key])
                updateRequired = True

        return updateRequired

class FeedModel(ModelBase):
    title = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def fromDict(self, dic):
        return self.updateAttrFromDict(['title', 'url'], dic)

    def updateEntries(self):
        xml = util.openUrl(self.url)
        if not xml:
            return []

        entries = []
        parser = parsers.FeedParserFactory.create(xml)
        for entryDict in parser.entries():
            key = entryDict['key']

            entry = EntryModel.get_by_key_name(key, parent=self)
            if not entry:
                entry = EntryModel(parent=self, key_name=key)
                entry.feed = self

            if entry.fromDict(entryDict):
                entry.read = False
                entry.put()

            entries.append(entry)

        return entries

    def toDict(self):
        return {'title': self.title,
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
