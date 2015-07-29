'''
Hummingbird.py
Handles all of the connections to Hummingbird.
'''

import difflib
import requests
import traceback
import pprint

#Returns the closest anime (as a Json-like object) it can find using the given searchtext
def getAnimeDetails(searchText):
    try:
        request = requests.get('https://hummingbird.me/api/v1/search/anime?query=' + searchText.lower())
        
        closestAnime = getClosestAnime(searchText, request.json())

        if not (closestAnime is None):
            return closestAnime
        else:
            for anime in request.json():
                try:
                    if ('tv' in anime['show_type'].lower()):
                        nameList = []

                        nameList.append(anime['title'].lower())
                        nameList.append(anime['alternate_title'].lower())
                        
                        if not (difflib.get_close_matches(searchText.lower(), nameList, 1, 0.9)[0] is None):
                            return anime
                except Exception as e:
                    pass

            return request.json()[0]
            
    except Exception as e:
        return None

#Sometimes the "right" anime isn't at the top of the list, so we get the titles
#of everything and do some fuzzy string searching against the search text
def getClosestAnime(searchText, animeList):
    try:
        animeNameList = []
        
        for anime in animeList:
            
            if not ('ona' in anime['show_type'].lower()):
                animeNameList.append(anime['title'].lower())

                if anime['alternate_title'] is not None:
                    animeNameList.append(anime['alternate_title'].lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), animeNameList, 1, 0.95)[0]
        

        for anime in animeList:
            if not ('ona' in anime['show_type'].lower()):
                if anime['title'].lower() == closestNameFromList.lower():
                    return anime
                elif anime['alternate_title'] is not None:
                    if anime['alternate_title'].lower() == closestNameFromList.lower():
                        return anime

        return None
    except:
        return None
