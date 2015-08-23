'''
MU.py
Handles all MangaUpdates information
'''

from pyquery import PyQuery as pq
import requests
import difflib

def findClosestManga(searchText, mangaList):
    try:
        nameList = []

        for manga in mangaList:
            nameList.append(manga['title'].lower())

        closestNameFromList = difflib.get_close_matches(searchText.lower(), nameList, 1, 0.85)

        for manga in mangaList:
            if manga['title'].lower() == closestNameFromList[0].lower():
                return manga

        return None
    except:
        return None

def getMangaURL(searchText):
    try:
        payload = {'search': searchText}
        html = requests.get('https://mangaupdates.com/series.html', params=payload)

        mu = pq(html.text)

        mangaList = []

        for thing in mu.find('.series_rows_table tr'):
            title = pq(thing).find('.col1').text()
            url = pq(thing).find('.col1 a').attr('href')
            genres = pq(thing).find('.col2').text()
            year = pq(thing).find('.col3').text()
            rating = pq(thing).find('.col4').text()
            
            if title:
                data = { 'title': title,
                        'url': url,
                        'genres': genres,
                        'year': year,
                        'rating': rating }

                mangaList.append(data)

        closest = findClosestManga(searchText, mangaList)
        return closest['url']
    
    except:
        return None
