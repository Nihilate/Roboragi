'''
NovelUpdates.py
Handles all NovelUpdates information
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
        html = requests.get('http://www.novelupdates.com/?s=' + searchText, timeout=10)
        req.close()

        nu = pq(html.text)

        lnList = []

        for thing in nu.find('.w-blog-entry'):
            title = pq(thing).find('.w-blog-entry-title').text()
            url = pq(thing).find('.w-blog-entry-link').attr('href')

            if title:
                data = { 'title': title,
                        'url': url }
                lnList.append(data)

        closest = findClosestLightNovel(searchText, lnList)
        return closest['url']
    
    except:
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
    return 'http://www.novelupdates.com/series/' + str(lnId)
