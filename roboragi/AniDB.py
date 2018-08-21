'''
AniDB.py
Handles all AniDB information
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

req = requests.Session()

def getAnimeURL(searchText):
    try:
        html = req.get('http://anisearch.outrance.pl/?task=search&query=' + searchText, timeout=10)
        req.close()
        anidb = pq(html.content)    
    except:
        req.close()
        return None
        
    animeList = []
    
    for anime in anidb('animetitles anime'):
        titles = []
        for title in pq(anime).find('title').items():
            titleInfo = {}
            titleInfo['title'] = title.text()
            titleInfo['lang'] = title.attr['lang']
            titles.append(titleInfo)

        url = 'http://anidb.net/a' + anime.attrib['aid']
        
        if titles:
            data = { 'titles': titles,
                     'url': url
                     }

            animeList.append(data)

    closest = getClosestAnime(searchText, animeList)
    
    if closest:
        return closest['url']
    else:
        return None

def getAnimeURLById(animeId):
    return 'http://anidb.net/a' + str(animeId)

def getClosestAnime(searchText, animeList):
    nameList = []
    
    trustedNames = [] #i.e. English/default names
    untrustedNames = [] #everything else (French, Italian etc)

    for anime in animeList:
        for title in anime['titles']:
            if title['lang'].lower() in ['x-jat', 'en']:
                trustedNames.append(title['title'].lower())
            else:
                untrustedNames.append(title['title'].lower())

    closestNameFromList = difflib.get_close_matches(searchText.lower(), trustedNames, 1, 0.85)

    if closestNameFromList:
        for anime in animeList:
            for title in anime['titles']:
                if closestNameFromList[0].lower() == title['title'].lower() and title['lang'].lower() in ['x-jat', 'en']:
                    return anime
    else:
        closestNameFromList = difflib.get_close_matches(searchText.lower(), untrustedNames, 1, 0.85)

        if closestNameFromList:
            for anime in animeList:
                for title in anime['titles']:
                    if closestNameFromList[0].lower() == title['title'].lower() and title['lang'].lower() not in ['x-jat', 'en']:
                        return anime

    return None
