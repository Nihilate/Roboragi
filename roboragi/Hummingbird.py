'''
Hummingbird.py
Handles all of the connections to Hummingbird.
'''

import difflib
import requests
import traceback
import pprint

req = requests.Session()

def getSynonyms(request):
    synonyms = []

    synonyms.append(request['title']) if request['title'] else None
    synonyms.append(request['alternate_title']) if request['alternate_title'] else None

    return synonyms

#Returns the closest anime (as a Json-like object) it can find using the given searchtext
def getAnimeDetails(searchText):
    try:
        request = req.get('https://hummingbird.me/api/v1/search/anime?query=' + searchText.lower(), timeout=10)
        req.close()
        
        closestAnime = getClosestAnime(searchText, request.json())

        if not (closestAnime is None):
            return closestAnime
        else:
            return None
            
    except Exception as e:
        req.close()
        return None

#Returns the closest anime by id
def getAnimeDetailsById(animeId):
    try:
        response = req.get('http://hummingbird.me/api/v1/anime/' + str(animeId), timeout=10)
        req.close()
        return response.json()
    except Exception as e:
        req.close()
        return None

#Sometimes the "right" anime isn't at the top of the list, so we get the titles
#of everything and do some fuzzy string searching against the search text
def getClosestAnime(searchText, animeList):
    try:
        animeNameList = []
        
        for anime in animeList:            
            animeNameList.append(anime['title'].lower())

            if anime['alternate_title'] is not None:
                animeNameList.append(anime['alternate_title'].lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), animeNameList, 1, 0.95)[0]
        

        for anime in animeList:
            if anime['title'].lower() == closestNameFromList.lower():
                return anime
            elif anime['alternate_title'] is not None:
                if anime['alternate_title'].lower() == closestNameFromList.lower():
                    return anime

        return None
    except:
        return None
