#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import encodings
import urllib2
import xml.dom.minidom
import time
import json

def decodeByteString(bstr):
    try:
        return bstr.decode('utf8')
    except:
        for enc in encodings.aliases.aliases.values():
            try:
                return bstr.decode(enc)
            except:
                pass

    return None

def parseXmlString(ustr):
    return xml.dom.minidom.parseString(ustr.encode('ascii', 'xmlcharrefreplace'))

def openUrl(url):
    try:
        return decodeByteString(urllib2.urlopen(url).read())
    except:
        return None

def dateTimeToUnix(dateTime):
    return int(time.mktime(dateTime.timetuple()))

def dumpsJSON(obj):
    return json.dumps(obj, indent=2, sort_keys=True)

def loadsJSON(ustr):
    return json.loads(ustr)
