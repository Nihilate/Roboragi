# -*- coding: utf-8 -*-

'''
Anilist.py
Handles all of the connections to Anilist.
'''

import xml.etree.cElementTree as ET
import requests
import traceback
import difflib
import codecs
import pprint

MALUSER = ''
MALPASSWORD = ''
MALUSERAGENT = ''
MALAUTH = ''

try:
    import Config
    MALUSER = Config.maluser
    MALPASSWORD = Config.malpassword
    MALUSERAGENT = Config.maluseragent
    MALAUTH = Config.malauth
except ImportError:
    pass

mal = requests.Session()

#Sets up the connection to MAL.
def setup():
    mal_payload = {'username':MALUSER, 'password':MALPASSWORD, 'cookie':1, 'sublogin':'Login'}
    mal.headers.update({'Authorization': MALAUTH, 'User-Agent':MALUSERAGENT})

#Returns the closest anime (as a Json-like object) it can find using the given searchtext. MAL returns XML (bleh) so we have to convert it ourselves.
def getAnimeDetails(searchText):
    try:
        try:
            request = mal.get('http://myanimelist.net/api/anime/search.xml?q=' + searchText.rstrip())
        except:
            setup()
            request = mal.get('http://myanimelist.net/api/anime/search.xml?q=' + searchText.rstrip())
            
        convertedRequest = convertShittyXML(request.text)
        rawList = ET.fromstring(convertedRequest)

        animeList = []
        
        for anime in rawList.findall('./entry'):
            animeID = anime.find('id').text
            title = anime.find('title').text
            title_english = anime.find('english').text

            synonyms = None
            if (anime.find('synonyms').text is not None):
                synonyms = (anime.find('synonyms').text).split(";")

            episodes = anime.find('episodes').text
            animeType = anime.find('type').text
            status = anime.find('status').text
            start_date = anime.find('start_date').text
            end_date = anime.find('end_date').text
            synopsis = anime.find('synopsis').text
            image = anime.find('image').text

            data = {'id': animeID,
                     'title': title,
                     'english': title_english,
                     'synonyms': synonyms,
                     'episodes': episodes,
                     'type': animeType,
                     'status': status,
                     'start_date': start_date,
                     'end_date': end_date,
                     'synopsis': synopsis,
                     'image': image }

            animeList.append(data)

        closestAnime = getClosestAnime(searchText, animeList)

        return closestAnime
        
    except Exception as e:
        #traceback.print_exc()
        return None

#Given a list, it finds the closest anime series it can.
def getClosestAnime(searchText, animeList):
    try:
        nameList = []
        
        for anime in animeList:
            nameList.append(anime['title'].lower())

            if not (anime['english'] is None):
                nameList.append(anime['english'].lower())

            if anime['synonyms']:
                for synonym in anime['synonyms']:
                    nameList.append(synonym.lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), nameList, 1, 0.90)[0]

        for anime in animeList:
            if (anime['title'].lower() == closestNameFromList.lower()) or (anime['english'].lower() == closestNameFromList.lower()):
                return anime
            else:
                for synonym in anime['synonyms']:
                    if synonym.lower() == closestNameFromList.lower():
                        return anime

        return None
    except Exception as e:
        #traceback.print_exc()
        return None

#MAL's XML is a piece of crap. There has to be a better way to do this.
def convertShittyXML(text):
    text = text.replace('&Eacute;', 'É').replace('&times;', 'x').replace('&rsquo;', "'").replace('&lsquo;', "'").replace('&hellip', '...').replace('&le', '<').replace('<;', '; ').replace('&hearts;', '♥').replace('&mdash;', '-')
    text = text.replace('&eacute;', 'é').replace('&ndash;', '-').replace('&Aacute;', 'Á').replace('&acute;', 'à').replace('&ldquo;', '"').replace('&rdquo;', '"').replace('&Oslash;', 'Ø').replace('&frac12;', '½').replace('&infin;', '∞')
    text = text.replace('&agrave;', 'à').replace('&egrave;', 'è').replace('&dagger;', '†').replace('&sup2;', '²')
    
    return text

#Used to check if two descriptions are relatively close. This is used in place of author searching because MAL don't give authors at any point.
def getClosestFromDescription(mangaList, descriptionToCheck):
    try:
        descList = []
        for manga in mangaList:
            descList.append(manga['synopsis'].lower())

        closestNameFromList = difflib.get_close_matches(descriptionToCheck.lower(), descList, 1, 0.1)[0]

        for manga in mangaList:
            if (closestNameFromList == manga['synopsis'].lower()):
                return manga
        
    except:
        return None

#Since MAL doesn't give me an author, I make a search using similar descriptions instead. Super janky.
def getMangaCloseToDescription(searchText, descriptionToCheck):
    try:
        try:
            request = mal.get('http://myanimelist.net/api/manga/search.xml?q=' + searchText.rstrip())
        except:
            setup()
            request = mal.get('http://myanimelist.net/api/manga/search.xml?q=' + searchText.rstrip())

        convertedRequest = convertShittyXML(request.text)
        rawList = ET.fromstring(convertedRequest)

        mangaList = []
        
        for manga in rawList.findall('./entry'):
            mangaID = manga.find('id').text
            title = manga.find('title').text
            title_english = manga.find('english').text

            synonyms = None
            if not (manga.find('synonyms').text is None):
                synonyms = (manga.find('synonyms').text).split(";")

            chapters = manga.find('chapters').text
            volumes = manga.find('volumes').text
            mangaType = manga.find('type').text
            status = manga.find('status').text
            start_date = manga.find('start_date').text
            end_date = manga.find('end_date').text
            synopsis = manga.find('synopsis').text
            image = manga.find('image').text

            data = {'id': mangaID,
                     'title': title,
                     'english': title_english,
                     'synonyms': synonyms,
                     'chapters': chapters,
                     'volumes': volumes,
                     'type': mangaType,
                     'status': status,
                     'start_date': start_date,
                     'end_date': end_date,
                     'synopsis': synopsis,
                     'image': image }

            mangaList.append(data)

        closeManga = getListOfCloseManga(searchText, mangaList)

        return getClosestFromDescription(closeManga, descriptionToCheck)

        return None
    except:
        traceback.print_exc()
        return None
    

#Returns the closest manga series given a specific search term. Again, MAL returns XML, so we conver it ourselves
def getMangaDetails(searchText):
    try:
        try:
            request = mal.get('http://myanimelist.net/api/manga/search.xml?q=' + searchText.rstrip())
        except:
            setup()
            request = mal.get('http://myanimelist.net/api/manga/search.xml?q=' + searchText.rstrip())

        convertedRequest = convertShittyXML(request.text)    
        rawList = ET.fromstring(convertedRequest)

        mangaList = []
        
        for manga in rawList.findall('./entry'):
            mangaID = manga.find('id').text
            title = manga.find('title').text
            title_english = manga.find('english').text

            synonyms = None
            if not (manga.find('synonyms').text is None):
                synonyms = (manga.find('synonyms').text).split(";")

            chapters = manga.find('chapters').text
            volumes = manga.find('volumes').text
            mangaType = manga.find('type').text
            status = manga.find('status').text
            start_date = manga.find('start_date').text
            end_date = manga.find('end_date').text
            synopsis = manga.find('synopsis').text
            image = manga.find('image').text

            data = {'id': mangaID,
                     'title': title,
                     'english': title_english,
                     'synonyms': synonyms,
                     'chapters': chapters,
                     'volumes': volumes,
                     'type': mangaType,
                     'status': status,
                     'start_date': start_date,
                     'end_date': end_date,
                     'synopsis': synopsis,
                     'image': image }

            mangaList.append(data)

        closestManga = getClosestManga(searchText, mangaList)

        if not (closestManga is None):
            return closestManga
        else:
            return None

    except:
        #traceback.print_exc()
        return None

#Returns a list of manga with titles very close to the search text. Current unused because MAL's API is shit and doesn't return author names.
def getListOfCloseManga(searchText, mangaList):
    try:
        ratio = 0.90
        returnList = []
        
        for manga in mangaList:          
            if round(difflib.SequenceMatcher(lambda x: x == "", manga['title'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                returnList.append(manga)
            elif not (manga['english'] is None):
                if round(difflib.SequenceMatcher(lambda x: x == "", manga['english'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                    returnList.append(manga)
            elif not (manga['synonyms'] is None):
                for synonym in manga['synonyms']:
                    if round(difflib.SequenceMatcher(lambda x: x == "", synonym, searchText.lower()).ratio(), 3) >= ratio:
                        returnList.append(manga)
                        break

        return returnList
        
    except Exception as e:
        #traceback.print_exc()
        return None

#Used to determine the closest manga to a given search term in a list
def getClosestManga(searchText, mangaList):
    try:
        nameList = []
        
        for manga in mangaList:
            nameList.append(manga['title'].lower())
            
            if not (manga['english'] is None):
                nameList.append(manga['english'].lower())
                
            if not (manga['synonyms'] is None):
                for synonym in manga['synonyms']:
                    nameList.append(synonym.lower().strip())
        
        closestNameFromList = difflib.get_close_matches(searchText.lower(), nameList, 1, 0.90)[0]

        for manga in mangaList:
            if (manga['title'].lower() == closestNameFromList.lower()):
                return manga
            elif not (manga['english'] is None):
                if (manga['english'].lower() == closestNameFromList.lower()):
                    return manga

        for manga in mangaList:
            if not (manga['synonyms'] is None):
                for synonym in manga['synonyms']:
                    if synonym.lower().strip() == closestNameFromList.lower():
                        return manga

        return None
    except Exception as e:
        #traceback.print_exc()
        return None

setup()
