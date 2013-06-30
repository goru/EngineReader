from xml.dom import minidom
import hashlib

class FeedParserBuilder(object):
    @classmethod
    def build(cls, text):
        dom = minidom.parseString(text)

        parsers = [AtomParser, Rss1Parser, Rss2Parser]
        for parser in parsers:
            feedParser = parser.parse(dom)
            if feedParser:
                return feedParser

        return None

class FeedParser(object):
    document = None

    @classmethod
    def parse(cls, dom):
        return None

    def getNodeData(self, elm):
        for node in elm.childNodes:
            if node.nodeType == node.TEXT_NODE:
                return node.data

        for node in elm.childNodes:
            if node.nodeType == node.CDATA_SECTION_NODE:
                return node.data

        return None

    def getEntryKey(self, url):
        return 'entry-' + hashlib.md5(url).hexdigest()

class AtomParser(FeedParser):
    @classmethod
    def parse(cls, dom):
        document = dom.documentElement
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

            description = ''
            content = child.getElementsByTagName('content')
            summary = child.getElementsByTagName('summary')
            if content.length > 0:
                desc = self.getNodeData(content[0])
            elif summary.length > 0:
                desc = self.getNodeData(summary[0])

            entry = {'title': title,
                     'url': url,
                     'description': desc,
                     'key': self.getEntryKey(url)}
            entries.append(entry)

        return entries

class Rss1Parser(FeedParser):
    @classmethod
    def parse(cls, dom):
        document = dom.documentElement
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

            entry = {'title': title,
                     'url': url,
                     'description': desc,
                     'key': self.getEntryKey(url)}
            entries.append(entry)

        return entries

class Rss2Parser(FeedParser):
    @classmethod
    def parse(cls, dom):
        document = dom.documentElement
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

            entry = {'title': title,
                     'url': url,
                     'description': desc,
                     'key': self.getEntryKey(url)}
            entries.append(entry)

        return entries
