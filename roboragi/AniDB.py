'''
AniDB.py
Handles all AniDB information
'''

from pyquery import PyQuery as pq
import requests
import difflib
import traceback
import pprint

def getAnimeURL(searchText):
    try:
        html = requests.get('http://anisearch.outrance.pl/?task=search&query=' + searchText)
        anidb = pq(html.content)    
    except:
        return None
        
    animeList = []
    
    for anime in anidb('animetitles anime'):
        titles = []
        for title in pq(anime).find('title').items():
            titles.append(title.text())

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

def getClosestAnime(searchText, animeList):
    nameList = []

    for anime in animeList:
        for title in anime['titles']:
            nameList.append(title.lower())

    closestNameFromList = difflib.get_close_matches(searchText.lower(), nameList, 1, 0.85)

    if closestNameFromList:
        for anime in animeList:
            if closestNameFromList[0].lower() in [x.lower() for x in anime['titles']]:
                return anime

    return None
