'''
NovelUpdates.py
Handles all NovelUpdates information
'''

# Copyright (C) 2018  Nihilate
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        nameListWithoutWN = []

        for ln in lnList:
            nameList.append(ln['title'].lower())

            if '(wn)' not in ln['title'].lower():
                nameListWithoutWN.append(ln['title'].lower())

        closestNameFromListWithoutWN = difflib.get_close_matches(searchText.lower(), nameListWithoutWN, 1, 0.80)
        closestNameFromListWithWN = difflib.get_close_matches(searchText.lower(), nameList, 1, 0.80)

        if closestNameFromListWithoutWN:
            nameToUse = closestNameFromListWithoutWN[0].lower()
        else:
            nameToUse = closestNameFromListWithWN[0].lower()

        for ln in lnList:
            if ln['title'].lower() == nameToUse:
                return ln

        return None
    except:
        return None

def getLightNovelById(lnId):
    return 'http://www.novelupdates.com/series/' + str(lnId)
