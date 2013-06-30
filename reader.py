from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import encodings
import json
import time
import urllib2
from xml.dom import minidom

from feed import *

def decode(string):
    try:
        return string.decode('utf8')
    except:
        for enc in encodings.aliases.aliases.values():
            try:
                return string.decode(enc)
            except:
                pass

    return string

class FeedModel(db.Model):
    name = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def fromDict(self, dic):
        self.name = dic['name']
        self.url = dic['url']

    def updateEntries(self):
        xml = decode(urllib2.urlopen(self.url).read())

        entries = []
        parser = FeedParserBuilder.build(xml)
        for entryDict in parser.entries():
            key = entryDict['key']

            entry = EntryModel.get_by_key_name(key, parent=self)
            if not entry:
                entry = EntryModel(parent=self, key_name=key)
                entry.read = False

            entry.fromDict(entryDict)
            entry.put()
            entries.append(entry)

        return entries

    def toDict(self):
        return {'name': self.name,
                'url': self.url,
                'created': int(time.mktime(self.created.timetuple())),
                'modified': int(time.mktime(self.modified.timetuple())),
                'id': self.key().id()}

class EntryModel(db.Model):
    feed = db.ReferenceProperty(FeedModel)
    title = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    desc = db.TextProperty()
    read = db.BooleanProperty()
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def fromDict(self, dic):
        self.title = dic['title']
        self.url = dic['url']
        self.desc = dic['description']

    def toDict(self):
        return {'title': self.title,
                'url': self.url,
                'description': self.desc,
                'read': self.read,
                'created': int(time.mktime(self.created.timetuple())),
                'modified': int(time.mktime(self.modified.timetuple())),
                'id': self.key().name()}

class HandlerBase(webapp.RequestHandler):
    def dumpsJSON(self, obj):
        return json.dumps(obj, indent=2, sort_keys=True)

    def loadsJSON(self, text):
        return json.loads(text)

    def writeNotFound(self):
        self.error(404)
        self.response.out.write(self.dumpsJSON({}))

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

        self.response.out.write(self.dumpsJSON({'feeds': feeds}))

    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        feed = FeedModel()
        feed.fromDict(self.loadsJSON(self.request.body))
        feed.put()
        feed.updateEntries()

        self.response.out.write(self.dumpsJSON(feed.toDict()))

class FeedImportHandler(HandlerBase):
    def post(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        dom = minidom.parseString(self.request.body)
        for outline in dom.documentElement.getElementsByTagName('outline'):
            if outline.getAttribute('type') != 'rss':
                continue

            title = outline.getAttribute('title')
            url = outline.getAttribute('xmlUrl')

            feed = FeedModel()
            feed.name = title
            feed.url = url
            feed.put()
            feed.updateEntries()
            feeds.append(feed.toDict())

        self.response.out.write(self.dumpsJSON({'feeds': feeds}))

class FeedUpdateHandler(HandlerBase):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        feeds = []
        for feed in FeedModel.all():
            feed.put()
            feed.updateEntries()
            feeds.append(feed.toDict())

        self.response.out.write(self.dumpsJSON({'feeds': feeds}))

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

        self.response.out.write(self.dumpsJSON(
            {'feed': feed.toDict(),
             'entries': entries}))

    def post(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = self.getFeed(feedId)
        if not feed:
            self.writeNotFound()
            return

        feed.fromDict(self.loadsJSON(self.request.body))
        feed.put()

        entries = []
        for entry in feed.updateEntries():
            entries.append(entry.toDict())

        self.response.out.write(self.dumpsJSON(
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
    [('/feed', FeedCollectionHandler),
     ('/feed/import', FeedImportHandler),
     ('/feed/update', FeedUpdateHandler),
     ('/feed/(\d+)', FeedHandler),
     ('/feed/(\d+)/(entry-[a-z0-9]+)/(read|unread)', ReadUnreadHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
