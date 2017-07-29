
import logging
import re

def getLogger():
    """Helper for retrieve the logger object
    """
    return logging.getLogger(__name__)

def parseXMLInformations(element):
    is_list = False
    last_tag = None
    # detect list of items
    for elm in element:
        if last_tag is not None and last_tag == elm.tag:
            is_list = True
        last_tag = elm.tag

    if is_list:
        data = []
    else:
        data = dict()

    # parse the elements
    for elm in element:
        name = re.sub('\{.*\}', '', elm.tag)
        if len(elm) > 0:
            sub_item = parseXMLInformations(elm)
        else:
            sub_item = elm.text
        if is_list:
            data.append(dict({name:sub_item}))
        else:
            data[name] = sub_item
    return data

def fillComputedValues(tv):
    """Add some computed values into 'computed' key of the given tv dict
    """
    if 'computed' not in tv:
        tv['computed'] = dict()
    fillUUIDFromDiscoverResponse(tv)
    fillNameFromDiscoverResponse(tv)
    fillModelFromDiscoverResponse(tv)
    fillManufacturerFromDiscoverResponse(tv)

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

def fillModelFromDiscoverResponse(tv):
    """Try to find the model string of the TV in informations
    """
    if ('informations' in tv and
        'general' in tv['informations'] and
        'device' in tv['informations']['general'] and
        'modelNumber' in tv['informations']['general']['device']):
        tv['computed']['model_number'] = tv['informations']['general']['device']['modelNumber']
    if ('informations' in tv and
        'general' in tv['informations'] and
        'device' in tv['informations']['general'] and
        'modelName' in tv['informations']['general']['device']):
        tv['computed']['model_name'] = tv['informations']['general']['device']['modelName']

def fillManufacturerFromDiscoverResponse(tv):
    """Try to find the friendly name of the TV in informations
    """
    if ('informations' in tv and
        'general' in tv['informations'] and
        'device' in tv['informations']['general'] and
        'manufacturer' in tv['informations']['general']['device']):
        tv['computed']['manufacturer'] = tv['informations']['general']['device']['manufacturer']
