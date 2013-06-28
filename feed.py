from xml.dom import minidom


class FeedParserBuilder(object):
    @classmethod
    def build(cls, text):
        dom = minidom.parseString(text)

        parsers = [AtomParser]
        for parser in parsers:
            f = parser.parse(dom)
            if (f):
                return f

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

            entry = {'title': self.getNodeData(child.getElementsByTagName('title')[0]),
                     'link': child.getElementsByTagName('link')[0].getAttribute('href')}
            entries.append(entry)

        return entries
