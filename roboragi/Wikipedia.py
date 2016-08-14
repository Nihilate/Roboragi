import requests
import difflib
import pprint
from urllib.parse import quote

BASE_RESULT_URL = 'https://en.wikipedia.org/wiki/'
BASE_API_URL = 'https://en.wikipedia.org/w/api.php?'

wiki = requests.Session()
wiki.headers.update({'User-Agent': 'Roboragi - An Anime/Manga Reddit Bot - Contact /u/Nihilate on Reddit'})

def getAnimeURL(searchText):
    return getThingURL(searchText, 'Anime')

def getMangaURL(searchText):
    return getThingURL(searchText, 'Manga')

def getThingURL(searchText, searchType=None):
    try:
        request = wiki.get(BASE_API_URL + 'action=query&format=json&list=search&utf8=1&srsearch=' + searchText, timeout=10)
    except:
        return None

    result = request.json()

    pprint.pprint(result)
    
    thingTitles = []

    for thing in result['query']['search']:
        #bloody disambiguation
        if 'can refer to' in thing['snippet']:
            continue
        
        if searchType:
            if searchType.lower() in thing['snippet']:
                thingTitles.append(thing['title'])
        else:
            thingTitles.append(thing['title'])

    print(thingTitles)

    closestThings = difflib.get_close_matches(searchText.lower(), [title.lower() for title in thingTitles], 1, 0.90)    
    
    if closestThings:
        for title in thingTitles:
            if closestThings[0].lower() in title.lower():
                return BASE_RESULT_URL + quote(title)
    else:
        if thingTitles:
            for thing in result['query']['search']:
                if thing['title'].lower() in thingTitles[0].lower():
                    if (searchText.lower() in thing['snippet'].lower()):
                        return BASE_RESULT_URL + quote(thingTitles[0])
                    break

        return None

def getThingURLById(thingId):
    return BASE_RESULT_URL + quote(thingId)

print(getAnimeURL('monogatari series'))
