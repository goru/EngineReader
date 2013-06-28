from xml.dom import minidom
import hashlib

class FeedParserBuilder(object):
    @classmethod
    def build(cls, text):
        dom = minidom.parseString(text)

        parsers = [AtomParser]
        for parser in parsers:
            feedParser = parser.parse(dom)
            if feedParser:
                return feedParser

        return None


class FeedParser(object):
    doc = None

    @classmethod
    def parse(cls, dom):
        return None

    def getNodeData(self, elm):
        for node in elm.childNodes:
            if node.nodeType == node.TEXT_NODE:
                return node.data

        return None


class AtomParser(FeedParser):
    @classmethod
    def parse(cls, dom):
        doc = dom.documentElement
        if doc.tagName == 'feed' and doc.getAttribute('xmlns') == 'http://www.w3.org/2005/Atom':
            feed = AtomParser()
            feed.doc = doc
            return feed

        return None

    def entries(self):
        entries = []

        for child in self.doc.childNodes:
            if child.nodeType != child.ELEMENT_NODE or child.nodeName != 'entry':
                continue

            title = self.getNodeData(child.getElementsByTagName('title')[0])
            url = child.getElementsByTagName('link')[0].getAttribute('href')
            key = 'entry-' + hashlib.md5(title + url).hexdigest()

            entry = {'title': title,
                     'url': url,
                     'key': key}
            entries.append(entry)

        return entries
