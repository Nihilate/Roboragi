'''
LNDB.py
Handles all LNDB information
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


def getLightNovelURL(searchText):
    try:
        searchText = searchText.replace(' ', '+')
        html = req.get(
            url=f"http://lndb.info/search?text={searchText}",
            timeout=10
        )
        req.close()

        lndb = pq(html.text)

        if 'light_novel' in html.url:
            # we've immediately hit a result
            return html.url
        else:
            # scan the search page for stuff

            lnList = []

            for thing in lndb.find('#bodylightnovelscontentid table tr'):
                title = pq(thing).find('a').text()
                url = pq(thing).find('a').attr('href')

                if title:
                    data = {'title': title,
                            'url': url}
                    lnList.append(data)

            closest = findClosestLightNovel(searchText, lnList)
            return closest['url']

    except Exception:
        req.close()
        return None


def findClosestLightNovel(searchText, lnList):
    try:
        nameList = []

        for ln in lnList:
            nameList.append(ln['title'].lower())

        closestNameFromList = difflib.get_close_matches(
            word=searchText.lower(),
            possibilities=nameList,
            n=1,
            cutoff=0.80
        )

        for ln in lnList:
            if ln['title'].lower() == closestNameFromList[0].lower():
                return ln

        return None
    except Exception:
        return None


def getLightNovelById(lnId):
    return 'http://lndb.info/light_novel/' + str(lnId)
