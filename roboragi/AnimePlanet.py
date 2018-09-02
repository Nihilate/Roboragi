# Copyright (C) 2018  Nihilate
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import difflib
from sys import version_info

import requests
from pyquery import PyQuery as pq

PY2 = version_info == 2

if PY2:
    from urllib import quote
    from urlparse import urljoin
else:
    from urllib.parse import quote, urljoin


BASE_URL = "https://www.anime-planet.com"

req = requests.Session()


def sanitiseSearchText(searchText):
    return searchText.replace('(TV)', 'TV')


def getAnimeURL(searchText):
    try:
        searchText = sanitiseSearchText(searchText)

        url = urljoin(BASE_URL, '/anime/all?name=' + quote(searchText))
        html = req.get(url, timeout=10)
        req.close()
        ap = pq(html.text)

        animeList = []

        # If it's taken us to the search page
        if 'https://www.anime-planet.com/anime/all?' in html.url.lower():
            for entry in ap.find('.cardDeck li'):
                entryDetails = pq(pq(entry).find('a').attr('title'))

                entryTitle = pq(entryDetails).find('h5').text()
                altTitle = pq(entryDetails) \
                    .find('.aka') \
                    .text() \
                    .replace('Alt title: ', '')
                entryURL = pq(entry).find('a').attr('href')

                anime = {}
                anime['title'] = entryTitle
                anime['alt_title'] = altTitle
                anime['url'] = BASE_URL + entryURL
                animeList.append(anime)

            searchText = searchText.lower()

            try:
                matches = difflib.get_close_matches(
                    word=searchText,
                    possibilities=[a['title'].lower() for a in animeList],
                    n=1,
                    cutoff=0.85
                )
            except Exception:
                matches = difflib.get_close_matches(
                    word=searchText,
                    possibilities=[a['alt_title'].lower() for a in animeList],
                    n=1,
                    cutoff=0.85
                )

            closestName = matches[0]

            for anime in animeList:
                if anime['title'].lower() == closestName:
                    return anime['url']
                elif anime['alt_title'].lower() == closestName:
                    return anime['url']

        # Else if it's taken us right to the series page, get the url from the
        # meta tag
        else:
            return ap.find("meta[property='og:url']").attr('content')
        return None

    except Exception:
        req.close()
        return None


def getMangaURL(searchText, authorName=None):
    """
    Probably doesn't need to be split into two functions given how similar they
    are, but it might be worth keeping separate for the sake of issues between
    anime/manga down the line
    """
    try:
        url = urljoin(BASE_URL, '/manga/all?name=' + quote(searchText))
        html = req.get(url, timeout=10)
        req.close()

        ap = pq(html.text)

        mangaList = []

        # If it's taken us to the search page
        if 'https://www.anime-planet.com/manga/all?' in html.url.lower():
            for entry in ap.find('.card'):
                entryDetails = pq(pq(entry).find('a').attr('title'))

                entryTitle = pq(entryDetails).find('h5').text()
                altTitle = pq(entryDetails) \
                    .find('.aka') \
                    .text() \
                    .replace('Alt title: ', '')
                entryURL = pq(entry).find('a').attr('href')

                manga = {}
                manga['title'] = entryTitle
                manga['alt_title'] = altTitle
                manga['url'] = BASE_URL + entryURL
                mangaList.append(manga)

            searchText = searchText.lower()

            try:
                matches = difflib.get_close_matches(
                    word=searchText,
                    possibilities=[x['title'].lower() for x in mangaList],
                    n=1,
                    cutoff=0.85
                )
            except Exception:
                matches = difflib.get_close_matches(
                    word=searchText,
                    possibilities=[x['alt_title'].lower() for x in mangaList],
                    n=1,
                    cutoff=0.85
                )

            closestName = matches[0]

            for manga in mangaList:
                if manga['title'].lower() == closestName:
                    return manga['url']
                elif manga['alt_title'].lower() == closestName:
                    return manga['url']

        # Else if it's taken us right to the series page, get the url from the
        # meta tag
        else:
            return ap.find("meta[property='og:url']").attr('content')
        return None

    except Exception:
        req.close()
        return None


def getAnimeURLById(animeId):
    return 'https://www.anime-planet.com/anime/' + str(animeId)


def getMangaURLById(mangaId):
    return 'https://www.anime-planet.com/manga/' + str(mangaId)
