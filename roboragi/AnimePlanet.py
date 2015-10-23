from pyquery import PyQuery as pq
import requests
import difflib
import traceback
import pprint

BASE_URL = "http://www.anime-planet.com"

def getAnimeURL(searchText):
    try:
        html = requests.get(BASE_URL + "/anime/all?name=" + searchText.replace(" ", "%20"))
        ap = pq(html.text)

        animeList = []

        #If it's taken us to the search page
        if ap.find('.pillFilters.pure-g'):
            for entry in ap.find('.card.entry.pure-u-1-6'):
                entryTitle = pq(entry).find('a').text()
                entryURL = pq(entry).find('a').attr('href')
                
                anime = {}
                anime['title'] = entryTitle
                anime['url'] = BASE_URL + entryURL
                animeList.append(anime)

            closestName = difflib.get_close_matches(searchText.lower(), [x['title'].lower() for x in animeList], 1, 0.90)[0]
            closestURL = ''
            
            for anime in animeList:
                if anime['title'].lower() == closestName:
                    return anime['url']
            
        #Else if it's taken us right to the series page, get the url from the meta tag
        else:
            return ap.find("meta[property='og:url']").attr('content')
        return None
            
    except:
        traceback.print_exc()
        return None
