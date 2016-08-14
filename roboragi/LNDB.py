'''
LNDB.py
Handles all LNDB information
'''

from pyquery import PyQuery as pq
import requests
import difflib
import traceback
import pprint
import collections

req = requests.Session()

def getLightNovelURL(searchText):
    try:
        searchText = searchText.replace(' ', '+')
        html = req.get('http://lndb.info/search?text=' + searchText, timeout=10)
        req.close()

        lndb = pq(html.text)

        lnList = []

        for thing in lndb.find('#bodylightnovelscontentid table tr'):
            title = pq(thing).find('a').text()
            url = pq(thing).find('a').attr('href')

            if title:
                data = { 'title': title,
                        'url': url }
                lnList.append(data)

        closest = findClosestLightNovel(searchText, lnList)
        return closest['url']
    
    except Exception as e:
        req.close()
        return None

def findClosestLightNovel(searchText, lnList):
    try:
        nameList = []

        for ln in lnList:
            nameList.append(ln['title'].lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), nameList, 1, 0.80)

        for ln in lnList:
            if ln['title'].lower() == closestNameFromList[0].lower():
                return ln

        return None
    except:
        return None

def getLightNovelById(lnId):
    return 'http://lndb.info/light_novel/' + str(lnId)
