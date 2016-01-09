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
