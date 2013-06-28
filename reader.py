from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import encodings
import json
import time
import urllib2

from feed import *

def decode(s):
    for e in encodings.aliases.aliases.values():
        try:
            return s.decode(e)
        except:
            pass
    return s

class FeedModel(db.Model):
    name = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)
    created = db.DateTimeProperty(auto_now_add = True)
    modified = db.DateTimeProperty(auto_now = True)
    body = db.TextProperty()

    def fromDict(self, dic):
        self.name = dic['name']
        self.url = dic['url']
        self.updateEntries()

    def updateEntries(self):
        self.body = decode(urllib2.urlopen(self.url).read())

        entries = []
        parser = FeedParserBuilder.build(self.body)
        for entry in parser.entries():
            

    def toDict(self):
        return {'name': self.name,
                 'url': self.url,
             'created': int(time.mktime(self.created.timetuple())),
            'modified': int(time.mktime(self.modified.timetuple())),
                #'body': self.body,
                  'id': self.key().id()}

class EntryModel(db.Model):
    feed = db.ReferenceProperty(FeedModel)
    title = db.StringProperty(multiline=False)
    url = db.StringProperty(multiline=False)

class HandlerBase(webapp.RequestHandler):
    def dumpsJSON(self, obj):
        return json.dumps(obj, indent=2, sort_keys=True)

    def loadsJSON(self, text):
        return json.loads(text)

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

        self.response.out.write(self.dumpsJSON(feed.toDict()))

class FeedHandler(HandlerBase):
    def getFeed(self, feedId):
        feed = FeedModel.get_by_id(long(feedId))
        if feed == None:
            self.error(404)
            self.response.out.write(self.dumpsJSON({}))
        return feed

    def get(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = self.getFeed(feedId)
        if feed != None:
            self.response.out.write(self.dumpsJSON(feed.toDict()))

    def post(self, feedId):
        self.response.headers['Content-Type'] = 'application/json'

        feed = self.getFeed(feedId)
        if feed != None:
            feed.fromDict(self.loadsJSON(self.request.body))
            feed.put()
            self.response.out.write(self.dumpsJSON(feed.toDict()))

application = webapp.WSGIApplication(
    [('/feed/?', FeedCollectionHandler),
    ('/feed/(\d+)/?', FeedHandler)],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
