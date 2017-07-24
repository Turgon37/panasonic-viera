
import logging
import re

def getLogger():
    """Helper for retrieve the logger object
    """
    return logging.getLogger(__name__)

def parseXMLInformations(element):
    data = dict()
    for elm in element:
        name = re.sub('\{.*\}', '', elm.tag)
        if len(elm) > 0:
            data[name] = parseXMLInformations(elm)
        else:
            data[name] = elm.text
    return data
