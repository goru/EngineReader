#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import sys
import unittest
from xml.dom.minidom import parseString

sys.path.append(os.path.abspath('../'))

from api.feeds.parsers import XmlParser


class TestXmlParser(unittest.TestCase):

    def test_create(self):
        dom = parseString('<test>some test</test>')
        parser = XmlParser.create(dom)
        self.assertTrue(parser)

    def test_get_node_data(self):
        data = 'some test'
        dom = parseString('<test>{0}</test>'.format(data))
        doc = dom.documentElement
        parser = XmlParser.create(dom)
        self.assertEqual(data, parser.getNodeData(doc))


if __name__ == '__main__':
    unittest.main()
