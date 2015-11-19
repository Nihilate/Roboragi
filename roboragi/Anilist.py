'''
Anilist.py
Handles all of the connections to Anilist.
'''

import requests
import difflib
import traceback
import pprint

ANICLIENT = ''
ANISECRET = ''

try:
    import Config
    ANICLIENT = Config.aniclient
    ANISECRET = Config.anisecret
except ImportError:
    pass

access_token = ''

escape_table = {
     "&": " ",
     "\'": "\\'",
     '\"': '\\"',
     '/': ' ',
     '-': ' ',
     '!': '\!'
     }

#Anilist's database doesn't like weird symbols when searching it, so you have to escape or replace a bunch of stuff.
def escape(text):
     return "".join(escape_table.get(c,c) for c in text)

#Sets up the connection to Anilist. You need a token to get stuff from them, which expires every hour.
def setup():
    try:
        request = requests.post('https://anilist.co/api/auth/access_token', params={'grant_type':'client_credentials', 'client_id':ANICLIENT, 'client_secret':ANISECRET})

        global access_token
        access_token = request.json()['access_token']
    except Exception as e:
        print('Error getting Anilist token')

#Returns the closest anime (as a Json-like object) it can find using the given searchtext
def getAnimeDetails(searchText):
    try:
        htmlSearchText = escape(searchText)
        
        request = requests.get("https://anilist.co/api/anime/search/" + htmlSearchText, params={'access_token':access_token})
        
        if request.status_code == 401:
            setup()
            request = requests.get("https://anilist.co/api/anime/search/" + htmlSearchText, params={'access_token':access_token})

        #Of the given list of shows, we try to find the one we think is closest to our search term
        closestAnime = getClosestAnime(searchText, request.json())

        if (closestAnime is not None):
            return closestAnime
        else:
            return None
            
    except Exception as e:
        #traceback.print_exc()
        return None

#Gets the "full" anime details (which aren't displayed when we search using the basic function). Gives us cool data like time until the next episode is aired.
def getFullAnimeDetails(animeID):
     try:
        request = requests.get("https://anilist.co/api/anime/" + str(animeID), params={'access_token':access_token})

        if request.status_code == 401:
            setup()
            request = requests.get("https://anilist.co/api/anime/" + str(animeID), params={'access_token':access_token})
        
        if request.status_code == 200:
            return request.json()
        else:
            return None
     except Exception as e:
          #traceback.print_exc()
          return None

#Given a list, it finds the closest anime series it can.
def getClosestAnime(searchText, animeList):
    try:
        animeNameList = []
        animeNameListNoSyn = []

        #For each anime series, add all the titles/synonyms to an array and do a fuzzy string search to find the one closest to our search text.
        #We also fill out an array that doesn't contain the synonyms. This is to protect against shows with multiple adaptations and similar synonyms (e.g. Haiyore Nyaruko-San)
        for anime in animeList:
            animeNameList.append(anime['title_english'].lower())
            animeNameList.append(anime['title_romaji'].lower())

            animeNameListNoSyn.append(anime['title_english'].lower())
            animeNameListNoSyn.append(anime['title_romaji'].lower())

            for synonym in anime['synonyms']:
                 animeNameList.append(synonym.lower())
        
        closestNameFromList = difflib.get_close_matches(searchText.lower(), animeNameList, 1, 0.95)[0]
        
        for anime in animeList:
            if (anime['title_english'].lower() == closestNameFromList.lower()) or (anime['title_romaji'].lower() == closestNameFromList.lower()):
                return anime
            else:
                for synonym in anime['synonyms']:
                    if (synonym.lower() == closestNameFromList.lower()) and (synonym.lower() not in animeNameListNoSyn):
                        return anime

        return None
    except:
        #traceback.print_exc()
        return None

#Makes a search for a manga series using a specific author
def getMangaWithAuthor(searchText, authorName):
    try:
        htmlSearchText = escape(searchText)
        
        request = requests.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token})
        
        if request.status_code == 401:
            setup()
            request = requests.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token})
        
        closestManga = getListOfCloseManga(searchText, request.json())
        fullMangaList = []

        for manga in closestManga:
            try:
                fullManga = requests.get("https://anilist.co/api/manga/" + str(manga['id']) + "/staff", params={'access_token':access_token})

                if fullManga.status_code == 401:
                    setup()
                    fullManga = requests.get("https://anilist.co/api/manga/" + str(manga['id']) + "/staff", params={'access_token':access_token})

                fullMangaList.append(fullManga.json())
            except:
                pass

        potentialHits = []
        for manga in fullMangaList:
            for staff in manga['staff']:
                isRightName = True
                fullStaffName = staff['name_first'] + ' ' + staff['name_last']
                authorNamesSplit = authorName.split(' ')

                for name in authorNamesSplit:
                    if not (name.lower() in fullStaffName.lower()):
                        isRightName = False

                if isRightName:
                    potentialHits.append(manga)

        if potentialHits:
            return getClosestManga(searchText, potentialHits)

        return None
        
    except Exception as e:
        traceback.print_exc()
        return None

#Returns the closest manga series given a specific search term
def getMangaDetails(searchText):
    try:
        htmlSearchText = escape(searchText)
        
        request = requests.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token})
        
        if request.status_code == 401:
            setup()
            request = requests.get("https://anilist.co/api/manga/search/" + htmlSearchText, params={'access_token':access_token})
        
        closestManga = getClosestManga(searchText, request.json())

        if (closestManga is not None):
            return requests.get("https://anilist.co/api/manga/" + str(closestManga['id']), params={'access_token':access_token}).json()
        else:
            return None
        
    except Exception as e:
        #traceback.print_exc()
        return None

#Used to determine the closest manga to a given search term in a list
def getListOfCloseManga(searchText, mangaList):
    try:
        ratio = 0.90
        returnList = []
        
        for manga in mangaList:
            alreadyExists = False
            for thing in returnList:
                if int(manga['id']) == int(thing['id']):
                    alreadyExists = True
                    break
            if (alreadyExists):
                continue
            
            if round(difflib.SequenceMatcher(lambda x: x == "", manga['title_english'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                returnList.append(manga)
            elif round(difflib.SequenceMatcher(lambda x: x == "", manga['title_romaji'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                returnList.append(manga)
            elif not (manga['synonyms'] is None):
                for synonym in manga['synonyms']:
                    if round(difflib.SequenceMatcher(lambda x: x == "", synonym.lower(), searchText.lower()).ratio(), 3) >= ratio:
                        returnList.append(manga)
                        break
        return returnList
    except Exception as e:
        traceback.print_exc()
        return None

#Used to determine the closest manga to a given search term in a list
def getClosestManga(searchText, mangaList):
    try:
        mangaNameList = []
        
        for manga in mangaList:
            mangaNameList.append(manga['title_english'].lower())
            mangaNameList.append(manga['title_romaji'].lower())

            for synonym in manga['synonyms']:
                 mangaNameList.append(synonym.lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), mangaNameList, 1, 0.95)[0]
        
        for manga in mangaList:
            if not ('one shot' in manga['type'].lower()):
                if (manga['title_english'].lower() == closestNameFromList.lower()) or (manga['title_romaji'].lower() == closestNameFromList.lower()):
                    return manga

        for manga in mangaList:                
            for synonym in manga['synonyms']:
                if synonym.lower() == closestNameFromList.lower():
                    return manga

        return None
    except Exception as e:
        #traceback.print_exc()
        return None

setup()
