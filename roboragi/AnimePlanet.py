from pyquery import PyQuery as pq
import requests
import difflib
import traceback
import pprint
import collections

BASE_URL = "http://www.anime-planet.com"

req = requests.Session()

def sanitiseSearchText(searchText):
    return searchText.replace('(TV)', 'TV')

def getAnimeURL(searchText):
    try:
        searchText = sanitiseSearchText(searchText)
        
        html = req.get(BASE_URL + "/anime/all?name=" + searchText.replace(" ", "%20"), timeout=10)
        req.close()
        ap = pq(html.text)

        animeList = []

        #If it's taken us to the search page
        if ap.find('.cardDeck.pure-g.cd-narrow[data-type="anime"]'):
            for entry in ap.find('.card.pure-1-6'):
                entryTitle = pq(entry).find('a').text()
                entryURL = pq(entry).find('a').attr('href')
                
                anime = {}
                anime['title'] = entryTitle
                anime['url'] = BASE_URL + entryURL
                animeList.append(anime)

            closestName = difflib.get_close_matches(searchText.lower(), [x['title'].lower() for x in animeList], 1, 0.85)[0]
            closestURL = ''
            
            for anime in animeList:
                if anime['title'].lower() == closestName:
                    return anime['url']
            
        #Else if it's taken us right to the series page, get the url from the meta tag
        else:
            return ap.find("meta[property='og:url']").attr('content')
        return None
            
    except:
        req.close()
        return None

#Probably doesn't need to be split into two functions given how similar they are, but it might be worth keeping separate for the sake of issues between anime/manga down the line
def getMangaURL(searchText, authorName=None):
    try:
        if authorName:
            html = req.get(BASE_URL + "/manga/all?name=" + searchText.replace(" ", "%20") + '&author=' + authorName.replace(" ", "%20"), timeout=10)
            req.close()

            if "No results found" in html.text:
                rearrangedAuthorNames = collections.deque(authorName.split(' '))
                rearrangedAuthorNames.rotate(-1)
                rearrangedName = ' '.join(rearrangedAuthorNames)
                html = req.get(BASE_URL + "/manga/all?name=" + searchText.replace(" ", "%20") + '&author=' + rearrangedName.replace(" ", "%20"), timeout=10)
                req.close()
            
        else:
            html = req.get(BASE_URL + "/manga/all?name=" + searchText.replace(" ", "%20"), timeout=10)
            req.close()
            
        ap = pq(html.text)

        mangaList = []

        #If it's taken us to the search page
        if ap.find('.cardDeck.pure-g.cd-narrow[data-type="manga"]'):
            for entry in ap.find('.card.pure-1-6'):
                entryTitle = pq(entry).find('a').text()
                entryURL = pq(entry).find('a').attr('href')
                
                manga = {}
                manga['title'] = entryTitle
                manga['url'] = BASE_URL + entryURL
                mangaList.append(manga)

            if authorName:
                authorName = authorName.lower()
                authorName = authorName.split(' ')

                for manga in mangaList:
                    manga['title'] = manga['title'].lower()
                    
                    for name in authorName:
                        manga['title'] = manga['title'].replace(name, '')
                    manga['title'] = manga['title'].replace('(', '').replace(')', '').strip()
                
            closestName = difflib.get_close_matches(searchText.lower(), [x['title'].lower() for x in mangaList], 1, 0.85)[0]
            closestURL = ''
            
            for manga in mangaList:
                if manga['title'].lower() == closestName:
                    return manga['url']
            
        #Else if it's taken us right to the series page, get the url from the meta tag
        else:
            return ap.find("meta[property='og:url']").attr('content')
        return None
            
    except:
        req.close()
        return None

def getAnimeURLById(animeId):
    return 'http://www.anime-planet.com/anime/' + str(animeId)

def getMangaURLById(mangaId):
    return 'http://www.anime-planet.com/manga/' + str(mangaId)
