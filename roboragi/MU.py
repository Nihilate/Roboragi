'''
MU.py
Handles all MangaUpdates information
'''

from pyquery import PyQuery as pq
import requests
import difflib
import traceback
import pprint
import collections

req = requests.Session()

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

def findAuthorURL(authorName):
    try:
        payload = {'search': authorName}
        html = req.get('https://mangaupdates.com/authors.html', params=payload, timeout=10)
        req.close()
        mu = pq(html.text)
        authorURL = None

        for thing in pq(mu).find('table tr td .text .pad'):
            try:
                url = pq(thing).find('a').attr('href')
                if 'http://www.mangaupdates.com/authors.html?id=' in url:
                    authorURL = url
            except:
                pass

        return authorURL
    except:
        req.close()
        traceback.print_exc()
        return None

def findSeriesURLViaAuthor(seriesName, authorName, authorURL):
    try:
        html = req.get(authorURL, timeout=10)
        req.close()
        mu = pq(html.text)
        authorURL = None

        authorName = authorName.lower()
        authorName = authorName.split(' ')
        
        for thing in mu.find('table tr .text'):
            try:
                title = pq(thing).find('a')[1].text
                url = pq(thing).find('a').attr('href')

                if url:
                    if 'http://www.mangaupdates.com/series.html?id=' in url:
                        title = title.lower()

                        for name in authorName:
                            title = title.replace(name, '')

                        s = difflib.SequenceMatcher(lambda x: x == "", seriesName, title)
                        if s.ratio() > 0.5:
                            return url
                            
            except:
                pass

        return authorURL
    except:
        req.close()
        traceback.print_exc()
        return None

def getMangaWithAuthor(searchText, authorName):
    try:
        url = findAuthorURL(authorName)
        
        if not url:
            rearrangedAuthorNames = collections.deque(authorName.split(' '))
            rearrangedAuthorNames.rotate(-1)
            rearrangedName = ' '.join(rearrangedAuthorNames)
            url = findAuthorURL(rearrangedName)

        if url:
            return findSeriesURLViaAuthor(searchText, authorName, url)
        else:
            return None
        
    except:
        traceback.print_exc()
        return None

def getMangaURL(searchText):
    try:
        payload = {'search': searchText}
        html = req.get('https://mangaupdates.com/series.html', params=payload, timeout=10)
        req.close()

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
        req.close()
        return None

def getMangaURLById(mangaId):
    return 'https://www.mangaupdates.com/series.html?id=' + str(mangaId)
