'''
MU.py
Handles all MangaUpdates information
'''

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

import requests
from pyquery import PyQuery as pq

req = requests.Session()


def findClosestManga(searchText, mangaList):
    try:
        nameList = []

        for manga in mangaList:
            nameList.append(manga['title'].lower())

        closestNameFromList = difflib.get_close_matches(
            word=searchText.lower(),
            possibilities=nameList,
            n=1,
            cutoff=0.85
        )

        for manga in mangaList:
            if manga['title'].lower() == closestNameFromList[0].lower():
                return manga

        return None
    except Exception:
        return None


def getMangaURL(searchText):
    try:
        payload = {'search': searchText}
        html = req.get(
            url='https://mangaupdates.com/series.html',
            params=payload,
            timeout=10
        )
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
                data = {'title': title,
                        'url': url,
                        'genres': genres,
                        'year': year,
                        'rating': rating}

                mangaList.append(data)

        closest = findClosestManga(searchText, mangaList)
        return closest['url']

    except Exception:
        req.close()
        return None


def getMangaURLById(mangaId):
    return 'https://www.mangaupdates.com/series.html?id=' + str(mangaId)
