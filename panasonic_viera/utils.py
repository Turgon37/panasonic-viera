
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

def fillComputedValues(tv):
    """Add some computed values into 'computed' key of the given tv dict
    """
    if 'computed' not in tv:
        tv['computed'] = dict()
    fillUUIDFromDiscoverResponse(tv)
    fillNameFromDiscoverResponse(tv)

def fillUUIDFromDiscoverResponse(tv):
    """Try to find the UUID of the TV in headers
    """
    if 'discovery' in tv and 'USN' in tv['discovery']:
        usn = tv['discovery']['USN'].lower()
        match = re.search('[a-f0-9]{8}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{4}\-[a-f0-9]{12}', usn)
        if match:
            tv['computed']['uuid'] = match.group(0)

def fillNameFromDiscoverResponse(tv):
    """Try to find the friendly name of the TV in informations
    """
    if ('informations' in tv and
        'general' in tv['informations'] and
        'device' in tv['informations']['general'] and
        'friendlyName' in tv['informations']['general']['device']):
        tv['computed']['name'] = tv['informations']['general']['device']['friendlyName']
