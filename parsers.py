#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import hashlib

import util

class XmlParser(object):
    document = None

    @classmethod
    def create(cls, document):
        xml = XmlParser()
        xml.document = document

        return xml

    def getNodeData(self, elm):
        for node in elm.childNodes:
            if node.nodeType == node.CDATA_SECTION_NODE:
                return node.data

        for node in elm.childNodes:
            if node.nodeType == node.TEXT_NODE:
                return node.data

        return None

class OpmlParser(XmlParser):
    @classmethod
    def create(cls, document):
        if document.tagName == 'opml' and document.getAttribute('version') == '1.0':
            opml = OpmlParser()
            opml.document = document

            return opml

        return None

    def feeds(self):
        feeds = []
        for outline in self.document.getElementsByTagName('outline'):
            if outline.getAttribute('type') != 'rss':
                continue

            title = outline.getAttribute('title')
            url = outline.getAttribute('xmlUrl')
            feeds.append({'title': title,
                          'url': url})

        return feeds

class FeedParserFactory(object):
    @classmethod
    def create(cls, xml):
        dom = util.parseXmlString(xml)
        document = dom.documentElement

        parsers = [AtomParser, Rss1Parser, Rss2Parser]
        for parser in parsers:
            feedParser = parser.create(document)
            if feedParser:
                return feedParser

        return None

class FeedParser(XmlParser):
    def entries(self):
        return []

    def createEntryDict(self, title, url, desc):
        return {'title': title,
                'url': url,
                'description': desc,
                'key': 'entry-' + hashlib.md5(url).hexdigest()}

class AtomParser(FeedParser):
    @classmethod
    def create(cls, document):
        if document.tagName == 'feed' and document.getAttribute('xmlns') == 'http://www.w3.org/2005/Atom':
            feed = AtomParser()
            feed.document = document

            return feed

        return None

    def entries(self):
        entries = []
        for child in self.document.childNodes:
            if child.nodeType != child.ELEMENT_NODE or child.nodeName != 'entry':
                continue

            title = self.getNodeData(child.getElementsByTagName('title')[0])
            url = child.getElementsByTagName('link')[0].getAttribute('href')

            desc = ''
            content = child.getElementsByTagName('content')
            summary = child.getElementsByTagName('summary')
            if content.length > 0:
                desc = self.getNodeData(content[0])
            elif summary.length > 0:
                desc = self.getNodeData(summary[0])

            entries.append(self.createEntryDict(title, url, desc))

        return entries

class Rss1Parser(FeedParser):
    @classmethod
    def create(cls, document):
        if document.tagName == 'rdf:RDF' and document.getAttribute('xmlns') == 'http://purl.org/rss/1.0/':
            feed = Rss1Parser()
            feed.document = document

            return feed

        return None

    def entries(self):
        entries = []
        for child in self.document.childNodes:
            if child.nodeType != child.ELEMENT_NODE or child.nodeName != 'item':
                continue

            title = self.getNodeData(child.getElementsByTagName('title')[0])
            url = self.getNodeData(child.getElementsByTagName('link')[0])

            desc = ''
            if child.getElementsByTagName('description').length > 0:
                desc = self.getNodeData(child.getElementsByTagName('description')[0])

            entries.append(self.createEntryDict(title, url, desc))

        return entries

class Rss2Parser(FeedParser):
    @classmethod
    def create(cls, document):
        if document.tagName == 'rss' and document.getAttribute('version') == '2.0':
            feed = Rss2Parser()
            feed.document = document

            return feed

        return None

    def entries(self):
        entries = []
        channel = self.document.getElementsByTagName('channel')[0]
        for child in channel.childNodes:
            if child.nodeType != child.ELEMENT_NODE or child.nodeName != 'item':
                continue

            title = self.getNodeData(child.getElementsByTagName('title')[0])
            url = self.getNodeData(child.getElementsByTagName('link')[0])

            desc = ''
            if child.getElementsByTagName('description').length > 0:
                desc = self.getNodeData(child.getElementsByTagName('description')[0])

            entries.append(self.createEntryDict(title, url, desc))

        return entries
